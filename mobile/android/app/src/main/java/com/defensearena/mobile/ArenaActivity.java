package com.defensearena.mobile;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.SystemClock;
import android.content.Intent;
import android.content.res.Configuration;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.util.Base64;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.*;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** URL-loading shell. Account/room policy stays entirely on the web server. */
public class ArenaActivity extends Activity {
    private static final int PICK_FILES = 10, SAVE_SUMMARY = 11, MICROPHONE = 12;
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private WebView web;
    private LinearLayout notice;
    private TextView status;
    private Button retry;
    private ValueCallback<Uri[]> fileCallback;
    private String summary;
    private WebMessagePort exportPort;
    private boolean pageFailed;
    private boolean authBusy;
    private final MicrophonePolicy microphone = new MicrophonePolicy(BuildConfig.ARENA_URL);
    private WebMessagePort audioPort;
    private String pendingAudioId, preparedAudioId, resumeAfterCapture;
    private boolean permissionPrompt, visible, destroyed, webPaused, activeAudioGrant, audioDocumentUnloaded;
    private final android.os.Handler permissionHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable permissionCheck = new Runnable() {
        @Override public void run() {
            if (destroyed || !visible || !activeAudioGrant) return;
            if (!hasMicrophonePermission()) {
                stopAudioDocument(); microphone.resume();
                restoreAudioDocument();
            } else permissionHandler.postDelayed(this, 500);
        }
    };


    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = new FrameLayout(this);
        web = new WebView(this);
        root.addView(web, new FrameLayout.LayoutParams(-1, -1));
        notice = new LinearLayout(this);
        notice.setOrientation(LinearLayout.VERTICAL);
        notice.setPadding(24, 24, 24, 24);
        notice.setBackgroundColor(0xffe9e7e2);
        status = new TextView(this);
        retry = new Button(this);
        retry.setText("Retry website");
        retry.setOnClickListener(v -> web.loadUrl(BuildConfig.ARENA_URL));
        notice.addView(status); notice.addView(retry);
        root.addView(notice, new FrameLayout.LayoutParams(-1, -2));
        setContentView(root);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
            root.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return insets;
        });
        WebSettings settings = web.getSettings();
        settings.setUserAgentString(settings.getUserAgentString() + " DefenseArenaAndroid/2");
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true); // Document picker content URIs only; never a navigable page.
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportMultipleWindows(true);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (!request.isForMainFrame()) return !trusted(request.getUrl());
                Uri url = request.getUrl();
                if (trusted(url) && "/api/auth/google/login".equals(url.getPath())) {
                    beginLogin(url.getQueryParameter("return_to")); return true;
                }
                if (trusted(url)) return false;
                external(url); return true;
            }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {
                closeExportPort(); closeAudioPort(); microphone.enterDocument(url);
                if (visible && !audioDocumentUnloaded && trusted(Uri.parse(url))) resumeAfterCapture = null;
                if (!"about:blank".equals(url)) { pageFailed = false; showNotice("Loading website…", false); }
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (!destroyed && visible && !pageFailed && !audioDocumentUnloaded && trusted(Uri.parse(url))) { notice.setVisibility(View.GONE); installExportPort(); installAudioPort(); }
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) failPage();
            }
            @Override public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
                if (request.isForMainFrame()) failPage();
            }
            @Override public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel(); failPage();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> {
                    if (!destroyed && visible && !pageFailed && trusted(Uri.parse(web.getUrl() == null ? "" : web.getUrl()))
                            && microphone.request(request.getOrigin().toString(), request.getResources(), SystemClock.elapsedRealtime(), hasMicrophonePermission())) {
                        request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
                        watchMicrophonePermission();
                    } else request.deny();
                });
            }
            @Override public void onPermissionRequestCanceled(PermissionRequest request) { microphone.cancelIntent(); }

            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (!trusted(Uri.parse(web.getUrl() == null ? "" : web.getUrl()))) return false;
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                pick.addCategory(Intent.CATEGORY_OPENABLE); pick.setType("*/*");
                pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try { startActivityForResult(pick, PICK_FILES); }
                catch (Exception error) { callback.onReceiveValue(null); fileCallback = null; }
                return true;
            }
            @Override public boolean onCreateWindow(WebView view, boolean dialog, boolean gesture, android.os.Message result) {
                if (!gesture) return false;
                WebView popup = new WebView(ArenaActivity.this);
                popup.setWebViewClient(new WebViewClient() {
                    @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { external(r.getUrl()); v.destroy(); return true; }
                });
                ((WebView.WebViewTransport) result.obj).setWebView(popup); result.sendToTarget(); return true;
            }
        });
        web.loadUrl(BuildConfig.ARENA_URL);
        handleReturn(getIntent());
    }

    private boolean trusted(Uri uri) {
        Uri base = Uri.parse(BuildConfig.ARENA_URL);
        return "https".equals(uri.getScheme()) && base.getHost().equals(uri.getHost()) && uri.getUserInfo() == null
            && (uri.getPort() == -1 ? 443 : uri.getPort()) == (base.getPort() == -1 ? 443 : base.getPort());
    }
    private void external(Uri uri) {
        if (!"https".equals(uri.getScheme()) || uri.getUserInfo() != null) return;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (Exception e) { showNotice("No browser is available to open this link.", true); }
    }
    private void showNotice(String message, boolean canRetry) {
        status.setText(message); retry.setVisibility(canRetry ? View.VISIBLE : View.GONE); notice.setVisibility(View.VISIBLE);
    }
    private void failPage() { stopAudioDocument(); pageFailed = true; showNotice("The website could not load securely. Check your connection and retry.", true); }
    private void closeExportPort() { if (exportPort != null) { exportPort.close(); exportPort = null; } }
    private void installExportPort() {
        closeExportPort();
        WebMessagePort[] ports = web.createWebMessageChannel();
        exportPort = ports[0];
        exportPort.setWebMessageCallback(new WebMessagePort.WebMessageCallback() {
            @Override public void onMessage(WebMessagePort port, WebMessage message) {
                if (port != exportPort || !trusted(Uri.parse(web.getUrl() == null ? "" : web.getUrl()))) return;
                try {
                    JSONObject body = new JSONObject(message.getData());
                    String name = body.getString("filename"), text = body.getString("text");
                    if (!name.matches("defense-[a-z0-9-]+\\.txt") || text.length() > 2_000_000 || summary != null) return;
                    summary = text;
                    Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("text/plain").addCategory(Intent.CATEGORY_OPENABLE);
                    save.putExtra(Intent.EXTRA_TITLE, name); startActivityForResult(save, SAVE_SUMMARY);
                } catch (Exception error) { summary = null; showNotice("Could not save the summary. Try again.", true); }
            }
        });
        web.postWebMessage(new WebMessage("defense-export-port", new WebMessagePort[]{ports[1]}), Uri.parse(BuildConfig.ARENA_URL));
    }
    private boolean hasMicrophonePermission() {
        return checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
    }
    private void audioReply(String id, boolean allowed) {
        if (audioPort == null || id == null) return;
        try { audioPort.postMessage(new WebMessage(new JSONObject().put("type", allowed ? "prepared" : "denied").put("id", id).toString())); }
        catch (Exception closed) { /* The document may have left during the system prompt. */ }
    }
    private void closeAudioPort() {
        microphone.cancelIntent(); pendingAudioId = null; preparedAudioId = null;
        if (audioPort != null) { audioPort.close(); audioPort = null; }
    }
    private void installAudioPort() {
        closeAudioPort();
        WebMessagePort[] ports = web.createWebMessageChannel(); audioPort = ports[0];
        audioPort.setWebMessageCallback(new WebMessagePort.WebMessageCallback() {
            @Override public void onMessage(WebMessagePort port, WebMessage message) {
                if (port != audioPort || destroyed || !visible || pageFailed || !trusted(Uri.parse(web.getUrl() == null ? "" : web.getUrl()))) return;
                try {
                    String raw = message.getData(); if (raw == null || raw.length() > 200) return;
                    JSONObject data = new JSONObject(raw); String id = data.getString("id");
                    if (!id.matches("[A-Za-z0-9-]{1,64}")) return;
                    if ("cancel".equals(data.optString("type"))) {
                        if (id.equals(pendingAudioId)) pendingAudioId = null;
                        if (id.equals(preparedAudioId)) { preparedAudioId = null; microphone.cancelIntent(); activeAudioGrant = false; permissionHandler.removeCallbacks(permissionCheck); }
                        return;
                    }
                    if (!"prepare".equals(data.optString("type"))) return;
                    if (permissionPrompt || pendingAudioId != null) { audioReply(id, false); return; }
                    if (hasMicrophonePermission()) {
                        boolean allowed = microphone.arm(SystemClock.elapsedRealtime());
                        if (allowed) { preparedAudioId = id; watchMicrophonePermission(); }
                        audioReply(id, allowed);
                    } else {
                        pendingAudioId = id; permissionPrompt = true;
                        requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, MICROPHONE);
                    }
                } catch (Exception invalid) { microphone.cancelIntent(); }
            }
        });
        web.postWebMessage(new WebMessage("defense-audio-port-v1", new WebMessagePort[]{ports[1]}), Uri.parse(BuildConfig.ARENA_URL));
    }
    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request, permissions, results);
        if (request != MICROPHONE) return;
        permissionPrompt = false;
        String id = pendingAudioId; pendingAudioId = null;
        if (id == null || destroyed || !visible || audioPort == null) return;
        boolean allowed = permissions.length == 1 && Manifest.permission.RECORD_AUDIO.equals(permissions[0])
            && results.length == 1 && results[0] == PackageManager.PERMISSION_GRANTED && hasMicrophonePermission();
        if (allowed && microphone.arm(SystemClock.elapsedRealtime())) { preparedAudioId = id; watchMicrophonePermission(); audioReply(id, true); }
        else audioReply(id, false);
    }
    private void watchMicrophonePermission() {
        // WebView may reuse an earlier origin grant without another permission callback.
        activeAudioGrant = true;
        permissionHandler.removeCallbacks(permissionCheck); permissionHandler.postDelayed(permissionCheck, 500);
    }
    private void restoreAudioDocument() {
        if (resumeAfterCapture == null) return;
        String url = resumeAfterCapture; resumeAfterCapture = null; audioDocumentUnloaded = false;
        web.loadUrl(url);
    }
    private void stopAudioDocument() {
        activeAudioGrant = false; permissionHandler.removeCallbacks(permissionCheck);
        microphone.suspend();
        if (pendingAudioId != null) audioReply(pendingAudioId, false);
        pendingAudioId = null; preparedAudioId = null;
        if (web == null || destroyed) return;
        web.evaluateJavascript("window.dispatchEvent(new Event('defense-native-background'))", null);
        // onPause alone does not guarantee that WebView media/JS stops. Unload any
        // document after this WebView has prepared capture, retaining a trusted URL
        // for normal room-token/tab-draft restoration. Never auto-restart the mic.
        if (microphone.mustUnloadCapture() && !audioDocumentUnloaded) {
            String current = web.getUrl();
            if (current != null && trusted(Uri.parse(current))) resumeAfterCapture = current;
            audioDocumentUnloaded = true; web.stopLoading(); web.loadUrl("about:blank");
        }
    }
    private void pauseWeb() { if (web != null && !webPaused) { web.onPause(); webPaused = true; } }

    private static String randomVerifier() {
        byte[] bytes = new byte[48]; new SecureRandom().nextBytes(bytes);
        return Base64.encodeToString(bytes, Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING);
    }
    private JSONObject post(String path, JSONObject body, java.util.List<String> cookies) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(BuildConfig.ARENA_URL + path).openConnection();
        try {
            connection.setInstanceFollowRedirects(false); connection.setConnectTimeout(20000); connection.setReadTimeout(20000);
            connection.setRequestMethod("POST"); connection.setDoOutput(true); connection.setRequestProperty("Content-Type", "application/json");
            try (OutputStream out = connection.getOutputStream()) { out.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
            if (connection.getResponseCode() != 200) throw new IOException("Sign-in failed");
            if (cookies != null) for (java.util.Map.Entry<String, java.util.List<String>> h : connection.getHeaderFields().entrySet())
                if (h.getKey() != null && h.getKey().equalsIgnoreCase("Set-Cookie")) cookies.addAll(h.getValue());
            try (InputStream in = connection.getInputStream()) { ByteArrayOutputStream bytes = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; int count; while ((count = in.read(buffer)) != -1) { bytes.write(buffer, 0, count); if (bytes.size() > 65536) throw new IOException(); } return new JSONObject(bytes.toString(StandardCharsets.UTF_8.name())); }
        } finally { connection.disconnect(); }
    }
    private void beginLogin(String destination) {
        if (authBusy) return;
        authBusy = true; showNotice("Opening secure browser sign-in…", false);
        network.execute(() -> {
            try {
                String verifier = randomVerifier();
                String challenge = Base64.encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.getBytes(StandardCharsets.US_ASCII)), Base64.URL_SAFE | Base64.NO_WRAP | Base64.NO_PADDING);
                JSONObject start = post("/api/auth/mobile/start", new JSONObject().put("challenge", challenge).put("return_to", destination == null ? "/?account=1" : destination), null);
                Uri login = Uri.parse(start.getString("login_url"));
                if (!trusted(login) || !"/api/auth/google/login".equals(login.getPath())) throw new IOException();
                getPreferences(MODE_PRIVATE).edit().putString("flow", start.getString("flow")).putString("verifier", verifier).apply();
                runOnUiThread(() -> { authBusy = false; notice.setVisibility(View.GONE); external(login); });
            } catch (Exception error) { runOnUiThread(() -> { authBusy = false; showNotice("Sign-in is unavailable. Retry from Account.", true); }); }
        });
    }
    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); setIntent(intent); handleReturn(intent); }
    private void handleReturn(Intent intent) {
        Uri uri = intent.getData();
        if (uri == null || !"defensearena".equals(uri.getScheme()) || uri.getUserInfo() != null || uri.getPort() != -1 || !"".equals(uri.getPath())) return;
        if ("payment-return".equals(uri.getHost()) && uri.getQuery() == null && uri.getFragment() == null) {
            // A navigation signal never confirms payment or replaces a live room.
            if (web.getUrl() == null) web.loadUrl(BuildConfig.ARENA_URL + "/?payments=test");
            else web.evaluateJavascript("window.dispatchEvent(new Event('defense-native-resume'))", null);
            return;
        }
        if (!"auth".equals(uri.getHost()) || authBusy) return;
        String flow = getPreferences(MODE_PRIVATE).getString("flow", "");
        String verifier = getPreferences(MODE_PRIVATE).getString("verifier", "");
        if (flow.isEmpty() || !flow.equals(uri.getQueryParameter("flow")) || uri.getQueryParameter("code") == null) {
            showNotice("Sign-in did not complete. Start again from Account.", true); return;
        }
        authBusy = true; showNotice("Completing sign-in…", false);
        network.execute(() -> {
            try {
                java.util.List<String> cookies = new java.util.ArrayList<>();
                JSONObject result = post("/api/auth/mobile/complete", new JSONObject().put("flow", flow).put("code", uri.getQueryParameter("code")).put("verifier", verifier), cookies);
                String target = result.getString("return_to");
                if (!java.util.Set.of("/", "/?account=1", "/?payments=test").contains(target) || cookies.isEmpty()) throw new IOException();
                runOnUiThread(() -> {
                    java.util.concurrent.atomic.AtomicInteger remaining = new java.util.concurrent.atomic.AtomicInteger(cookies.size());
                    java.util.concurrent.atomic.AtomicBoolean failed = new java.util.concurrent.atomic.AtomicBoolean(false);
                    for (String cookie : cookies) CookieManager.getInstance().setCookie(BuildConfig.ARENA_URL, cookie, accepted -> {
                        if (!accepted) failed.set(true);
                        if (remaining.decrementAndGet() == 0) {
                            authBusy = false;
                            if (failed.get()) { showNotice("Could not establish the account session. Start sign-in again.", true); return; }
                            CookieManager.getInstance().flush();
                            getPreferences(MODE_PRIVATE).edit().clear().apply();
                            web.loadUrl(BuildConfig.ARENA_URL + target);
                        }
                    });
                });
            } catch (Exception error) { runOnUiThread(() -> { authBusy = false; showNotice("Sign-in expired or failed. Start again from Account.", true); }); }
        });
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_FILES && fileCallback != null) {
            Uri[] files = null;
            if (result == RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    files = new Uri[data.getClipData().getItemCount()];
                    for (int i = 0; i < files.length; i++) files[i] = data.getClipData().getItemAt(i).getUri();
                } else if (data.getData() != null) files = new Uri[]{data.getData()};
            }
            fileCallback.onReceiveValue(files); fileCallback = null;
        }
        if (request == SAVE_SUMMARY) {
            String text = summary; summary = null;
            if (result == RESULT_OK && data != null && data.getData() != null && text != null) {
                Uri uri = data.getData();
                network.execute(() -> {
                    try (OutputStream out = getContentResolver().openOutputStream(uri)) { out.write(text.getBytes(StandardCharsets.UTF_8)); }
                    catch (Exception error) { runOnUiThread(() -> showNotice("Could not save the summary. Try again.", true)); }
                });
            }
        }
    }
    @Override public void onBackPressed() {
        web.evaluateJavascript("Boolean(document.querySelector('#drawer-close'))", result -> {
            if ("true".equals(result)) web.evaluateJavascript("document.querySelector('#drawer-close').click()", null);
            else if (web.canGoBack()) web.goBack(); else super.onBackPressed();
        });
    }
    @Override protected void onPause() {
        // The app's own runtime permission dialog is not a user background event.
        // A real background transition still reaches onStop and cancels the intent.
        if (!permissionPrompt) { visible = false; stopAudioDocument(); pauseWeb(); }
        super.onPause();
    }
    @Override protected void onStop() { visible = false; stopAudioDocument(); pauseWeb(); super.onStop(); }
    @Override protected void onResume() {
        super.onResume(); visible = true; microphone.resume();
        if (web != null) {
            if (webPaused) { web.onResume(); webPaused = false; }
            if (resumeAfterCapture != null) restoreAudioDocument();
            else web.evaluateJavascript("window.dispatchEvent(new Event('defense-native-resume'))", null);
        }
    }
    @Override public void onConfigurationChanged(Configuration config) { super.onConfigurationChanged(config); }
    @Override protected void onDestroy() { stopAudioDocument(); destroyed = true; visible = false; closeAudioPort(); closeExportPort(); if(fileCallback != null) fileCallback.onReceiveValue(null); web.destroy(); network.shutdownNow(); super.onDestroy(); }
}
