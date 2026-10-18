package com.defensearena.mobile;

import org.junit.Test;
import static org.junit.Assert.*;

/** Native permission boundary; no microphone, WebView or provider is invoked. */
public class MicrophonePolicyTest {
    private static final String SITE = "https://arena.example.test";
    private static final String AUDIO = "android.webkit.resource.AUDIO_CAPTURE";

    @Test public void onlyExplicitCurrentTopPageIntentPermitsRequestedAudio() {
        MicrophonePolicy policy = new MicrophonePolicy(SITE); policy.resume();
        policy.enterDocument(SITE + "/#/room");
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1000, true));
        assertTrue(policy.arm(1000));
        assertTrue(policy.mustUnloadCapture()); // Cached WebView grants may skip request().
        assertTrue(policy.request(SITE, new String[]{AUDIO}, 1001, true));
        assertTrue(policy.mustUnloadCapture());
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1002, true));
    }

    @Test public void externalPagesFramesCameraAndPermissionLossNeverGainCapture() {
        for (String origin : new String[]{"https://arena.example.test.evil", "https://evil.example.test", "http://arena.example.test", "https://arena.example.test:444", "https://user@arena.example.test", SITE + "/frame", SITE + "?x=1", SITE + "#frame"}) {
            MicrophonePolicy policy = new MicrophonePolicy(SITE); policy.resume();
            policy.enterDocument(SITE); policy.arm(1000);
            assertFalse(policy.request(origin, new String[]{AUDIO}, 1001, true));
        }
        MicrophonePolicy policy = new MicrophonePolicy(SITE); policy.resume();
        policy.enterDocument(SITE); policy.arm(1000);
        assertFalse(policy.request(SITE, new String[]{AUDIO,"android.webkit.resource.VIDEO_CAPTURE"}, 1001, true));
        policy.arm(1000);
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1001, false));
        policy.enterDocument("https://evil.example.test");
        assertFalse(policy.arm(1000));
    }

    @Test public void cancellingAnIntentNeverClearsTheNeedToUnloadAfterAnEarlierGrant() {
        MicrophonePolicy policy = new MicrophonePolicy(SITE); policy.resume(); policy.enterDocument(SITE);
        policy.arm(1000); assertTrue(policy.request(SITE, new String[]{AUDIO}, 1001, true));
        policy.cancelIntent(); policy.enterDocument(SITE + "/next");
        assertTrue(policy.mustUnloadCapture());
        policy.arm(2000); policy.cancelIntent();
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 2001, true));
        policy.arm(2000); assertFalse(policy.request(SITE, new String[]{}, 2001, true));
        policy.arm(2000); assertFalse(policy.request(SITE, new String[]{"android.webkit.resource.VIDEO_CAPTURE"}, 2001, true));
    }

    @Test public void backgroundNavigationAndExpiredIntentRequireFreshExplicitPreparation() {
        MicrophonePolicy policy = new MicrophonePolicy(SITE); policy.resume();
        policy.enterDocument(SITE); policy.arm(1000); policy.suspend();
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1001, true));
        policy.resume();
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1002, true));
        policy.arm(1000); policy.enterDocument(SITE + "/?account=1");
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 1002, true));
        policy.arm(1000);
        assertFalse(policy.request(SITE, new String[]{AUDIO}, 12000, true));
    }
}
