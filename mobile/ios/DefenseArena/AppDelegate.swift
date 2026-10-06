import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = ArenaViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
    func application(_ application: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
        guard url.scheme == "defensearena", url.host == "payment-return", url.user == nil,
              url.password == nil, url.port == nil, url.path.isEmpty, url.query == nil,
              url.fragment == nil, let room = window?.rootViewController as? ArenaViewController else { return false }
        room.returnFromCheckout()
        return true
    }
}
