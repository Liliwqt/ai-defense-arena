package com.defensearena.mobile;

import java.net.URI;

/** Audio-only, single-use intent bound to the current trusted document/lifecycle. */
public final class MicrophonePolicy {
    private static final String AUDIO = "android.webkit.resource.AUDIO_CAPTURE";
    private final URI origin;
    private boolean foreground;
    private boolean trustedDocument;
    private boolean capturePrepared;
    private long armedUntil;

    public MicrophonePolicy(String site) { origin = URI.create(site); }

    private boolean trusted(String value, boolean originOnly) {
        try {
            URI uri = URI.create(value);
            return "https".equals(uri.getScheme()) && uri.getRawUserInfo() == null
                && origin.getHost() != null && origin.getHost().equalsIgnoreCase(uri.getHost())
                && (uri.getPort() == -1 ? 443 : uri.getPort()) == (origin.getPort() == -1 ? 443 : origin.getPort())
                && (!originOnly || (uri.getRawQuery() == null && uri.getRawFragment() == null
                    && (uri.getRawPath().isEmpty() || "/".equals(uri.getRawPath()))));
        } catch (Exception invalid) { return false; }
    }
    public void enterDocument(String url) {
        trustedDocument = trusted(url, false); armedUntil = 0;
    }
    public void resume() { foreground = true; }
    public void suspend() { foreground = false; armedUntil = 0; }
    public void cancelIntent() { armedUntil = 0; }
    public boolean arm(long now) {
        if (!foreground || !trustedDocument) return false;
        armedUntil = now + 10000; capturePrepared = true; return true;
    }
    public boolean request(String requestOrigin, String[] resources, long now, boolean osPermission) {
        boolean allowed = foreground && trustedDocument && osPermission && armedUntil > now
            && trusted(requestOrigin, true) && resources != null && resources.length == 1 && AUDIO.equals(resources[0]);
        armedUntil = 0;
        return allowed;
    }
    /** Android WebView has no native stop-all-media API: unload this document on suspension. */
    public boolean mustUnloadCapture() { return capturePrepared; }
}
