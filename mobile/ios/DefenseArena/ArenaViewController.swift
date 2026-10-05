import UIKit
import WebKit
import AuthenticationServices
import CryptoKit
import Security

// WKUserContentController retains handlers; this proxy prevents a controller cycle.
private final class ExportHandler: NSObject, WKScriptMessageHandler {
    weak var owner: ArenaViewController?
    init(_ owner: ArenaViewController) { self.owner = owner }
    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        owner?.userContentController(controller, didReceive: message)
    }
}

/// Thin URL-loading shell. No native account, payment or defense policy.
final class ArenaViewController: UIViewController, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, ASWebAuthenticationPresentationContextProviding {
    private var web: WKWebView!
    private var origin: URL!
    private let banner = UIStackView()
    private let message = UILabel()
    private let retry = UIButton(type: .system)
    private let progress = UIProgressView(progressViewStyle: .default)
    private var observation: NSKeyValueObservation?
    private var auth: ASWebAuthenticationSession?
    private var flow: String?
    private var verifier: String?
    private var failed = false
    private var exporting = false
    private let http = URLSession(configuration: .ephemeral)

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.91, green: 0.90, blue: 0.89, alpha: 1)
        let value = Bundle.main.object(forInfoDictionaryKey: "ArenaURL") as? String ?? ""
        guard let url = URL(string: value), url.scheme == "https", url.host != nil,
              url.user == nil, url.password == nil, url.query == nil, url.fragment == nil,
              url.path.isEmpty || url.path == "/" else {
            message.text = "Configure a valid HTTPS ArenaURL before building the app."
            message.frame = view.bounds.insetBy(dx: 24, dy: 60)
            message.numberOfLines = 0; view.addSubview(message); return
        }
        origin = url
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.userContentController.add(ExportHandler(self), name: "defenseExport")
        web = WKWebView(frame: .zero, configuration: configuration)
        web.navigationDelegate = self; web.uiDelegate = self
        web.translatesAutoresizingMaskIntoConstraints = false
        web.scrollView.contentInsetAdjustmentBehavior = .never
        view.addSubview(web)
        NSLayoutConstraint.activate([
            web.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
            web.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor),
            web.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            web.bottomAnchor.constraint(equalTo: view.keyboardLayoutGuide.topAnchor)
        ])
        banner.axis = .vertical; banner.spacing = 8; banner.translatesAutoresizingMaskIntoConstraints = false
        banner.backgroundColor = view.backgroundColor
        message.numberOfLines = 0
        retry.setTitle("Retry website", for: .normal)
        retry.addTarget(self, action: #selector(reloadWebsite), for: .touchUpInside)
        banner.addArrangedSubview(message); banner.addArrangedSubview(progress); banner.addArrangedSubview(retry)
        view.addSubview(banner)
        NSLayoutConstraint.activate([
            banner.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 8),
            banner.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 16),
            banner.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -16)
        ])
        observation = web.observe(\.estimatedProgress, options: [.new]) { [weak self] web, _ in
            self?.progress.progress = Float(web.estimatedProgress)
        }
        NotificationCenter.default.addObserver(self, selector: #selector(resume), name: UIApplication.didBecomeActiveNotification, object: nil)
        reloadWebsite()
    }
    private func trusted(_ url: URL) -> Bool {
        url.scheme == "https" && url.host == origin.host && (url.port ?? 443) == (origin.port ?? 443) && url.user == nil && url.password == nil
    }
    private func show(_ text: String, retryable: Bool) {
        message.text = text; retry.isHidden = !retryable; progress.isHidden = retryable; banner.isHidden = false
    }
    @objc private func reloadWebsite() { web.load(URLRequest(url: origin)) }
    @objc private func resume() {
        web?.evaluateJavaScript("window.dispatchEvent(new Event('defense-native-resume'))", completionHandler: nil)
    }
    private func external(_ url: URL) {
        guard url.scheme == "https", url.user == nil, url.password == nil else { return }
        UIApplication.shared.open(url)
    }
    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if action.targetFrame?.isMainFrame == false {
            decisionHandler(trusted(url) ? .allow : .cancel); return
        }
        if trusted(url), url.path == "/api/auth/google/login" {
            decisionHandler(.cancel)
            let target = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.first(where: { $0.name == "return_to" })?.value ?? "/?account=1"
            beginLogin(target: target); return
        }
        if trusted(url), action.targetFrame != nil { decisionHandler(.allow) }
        else { external(url); decisionHandler(.cancel) }
    }
    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        if response.isForMainFrame, let url = response.response.url, !trusted(url) {
            external(url); decisionHandler(.cancel); return
        }
        if response.isForMainFrame, let response = response.response as? HTTPURLResponse, response.statusCode >= 400 {
            failed = true; show("The website could not load. Check your connection and retry.", retryable: true)
            decisionHandler(.cancel); return
        }
        decisionHandler(.allow)
    }
    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        failed = false; show("Loading website…", retryable: false)
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) { if !failed { banner.isHidden = true } }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { loadFailed(error) }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { loadFailed(error) }
    private func loadFailed(_ error: Error) {
        if (error as NSError).code == NSURLErrorCancelled { return }
        failed = true; show("The website could not load securely. Check your connection and retry.", retryable: true)
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        show("The page was closed by iOS. Retry to reconnect to your room.", retryable: true)
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url { external(url) }
        return nil
    }
    private func post(_ path: String, body: [String: String], completion: @escaping (Result<([String: Any], HTTPURLResponse), Error>) -> Void) {
        var request = URLRequest(url: URL(string: path, relativeTo: origin)!.absoluteURL)
        request.httpMethod = "POST"; request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        http.dataTask(with: request) { data, response, error in
            let result: Result<([String: Any], HTTPURLResponse), Error>
            if let response = response as? HTTPURLResponse, response.statusCode == 200,
               let data = data, data.count <= 65536, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                result = .success((json, response))
            } else { result = .failure(error ?? NSError(domain: "ArenaSignIn", code: 1)) }
            DispatchQueue.main.async { completion(result) }
        }.resume()
    }
    private func beginLogin(target: String) {
        guard auth == nil, verifier == nil else { return }
        var bytes = [UInt8](repeating: 0, count: 48)
        guard SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes) == errSecSuccess else { return }
        let proof = Data(bytes).base64EncodedString().replacingOccurrences(of: "+", with: "-").replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
        let challenge = Data(SHA256.hash(data: Data(proof.utf8))).base64EncodedString().replacingOccurrences(of: "+", with: "-").replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
        verifier = proof; show("Opening secure browser sign-in…", retryable: false)
        post("/api/auth/mobile/start", body: ["challenge": challenge, "return_to": target]) { [weak self] result in
            guard let self = self else { return }
            guard case let .success((json, _)) = result, let flow = json["flow"] as? String,
                  let value = json["login_url"] as? String, let url = URL(string: value), self.trusted(url), url.path == "/api/auth/google/login" else { self.signInFailed(); return }
            self.flow = flow
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: "defensearena") { [weak self] returned, error in
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    self.auth = nil
                    guard error == nil, let returned = returned else { self.signInFailed(); return }
                    self.completeLogin(returned)
                }
            }
            self.auth = session; session.presentationContextProvider = self
            if !session.start() { self.auth = nil; self.signInFailed() }
        }
    }
    private func signInFailed() {
        verifier = nil; flow = nil; show("Sign-in did not complete. Start again from Account.", retryable: true)
    }
    private func completeLogin(_ returned: URL) {
        let parts = URLComponents(url: returned, resolvingAgainstBaseURL: false)
        let items = parts?.queryItems ?? []
        guard returned.scheme == "defensearena", returned.host == "auth", returned.user == nil, returned.port == nil, returned.path.isEmpty,
              let flow = flow, items.first(where: { $0.name == "flow" })?.value == flow,
              let code = items.first(where: { $0.name == "code" })?.value, let verifier = verifier else { signInFailed(); return }
        show("Completing sign-in…", retryable: false)
        post("/api/auth/mobile/complete", body: ["flow": flow, "code": code, "verifier": verifier]) { [weak self] result in
            guard let self = self else { return }
            guard case let .success((json, response)) = result, let target = json["return_to"] as? String,
                  ["/", "/?account=1", "/?payments=test"].contains(target),
                  let headers = response.allHeaderFields as? [String: String] else { self.signInFailed(); return }
            let cookies = HTTPCookie.cookies(withResponseHeaderFields: headers, for: self.origin)
            guard cookies.contains(where: { $0.name == "arena_account" && $0.isHTTPOnly && $0.isSecure }) else { self.signInFailed(); return }
            let group = DispatchGroup()
            for cookie in cookies { group.enter(); self.web.configuration.websiteDataStore.httpCookieStore.setCookie(cookie) { group.leave() } }
            group.notify(queue: .main) {
                self.flow = nil; self.verifier = nil
                self.web.load(URLRequest(url: URL(string: target, relativeTo: self.origin)!.absoluteURL))
            }
        }
    }
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor { view.window! }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        let source = message.frameInfo.securityOrigin
        guard message.name == "defenseExport", message.frameInfo.isMainFrame,
              source.protocol == "https", source.host == origin.host, (source.port == 0 ? 443 : source.port) == (origin.port ?? 443),
              let current = web.url, trusted(current), !exporting,
              let body = message.body as? [String: String], let filename = body["filename"], let text = body["text"],
              filename.range(of: "^defense-[a-z0-9-]+\\.txt$", options: .regularExpression) != nil, text.utf8.count <= 2_000_000 else { return }
        let path = FileManager.default.temporaryDirectory.appendingPathComponent(filename)
        do { try text.write(to: path, atomically: true, encoding: .utf8) }
        catch { show("Could not save the summary. Try again.", retryable: true); return }
        exporting = true
        let share = UIActivityViewController(activityItems: [path], applicationActivities: nil)
        share.popoverPresentationController?.sourceView = web
        share.completionWithItemsHandler = { [weak self] _, _, _, _ in try? FileManager.default.removeItem(at: path); self?.exporting = false }
        present(share, animated: true)
    }
    deinit { NotificationCenter.default.removeObserver(self); http.invalidateAndCancel() }
}
