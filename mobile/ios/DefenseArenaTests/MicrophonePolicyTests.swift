import XCTest

/// Policy-level checks for the iOS microphone lifecycle. These run without a
/// simulator, WebKit or a real system prompt: the pure policy structs are the
/// same ones the controller uses.
final class MicrophonePolicyTests: XCTestCase {
    func testTheArmIsSingleUseAndExpiresAtTenSeconds() {
        var arm = MicrophoneArmPolicy()
        XCTAssertFalse(arm.isArmed(now: 0))
        arm.arm(id: "mic-1", now: 1000)
        XCTAssertTrue(arm.isArmed(now: 10999))
        XCTAssertEqual(arm.consume(now: 10999), "mic-1")
        XCTAssertNil(arm.consume(now: 1000))
        XCTAssertFalse(arm.isArmed(now: 1000))
        arm.arm(id: "mic-2", now: 1000)
        XCTAssertFalse(arm.isArmed(now: 11000))
        XCTAssertNil(arm.consume(now: 11000))
        XCTAssertNil(arm.intent)
    }

    func testCancelOnlyClearsTheMatchingIntent() {
        var arm = MicrophoneArmPolicy()
        arm.arm(id: "mic-1", now: 1000)
        arm.cancel(id: "mic-2")
        XCTAssertEqual(arm.consume(now: 1001), "mic-1")
        arm.arm(id: "mic-1", now: 1000)
        arm.cancel(id: "mic-1")
        XCTAssertNil(arm.consume(now: 1001))
        XCTAssertNil(arm.intent)
    }

    func testPromptSettlementIsExactlyOnceAndNeverClearsANewerRequest() {
        var prompt = MicrophonePromptPolicy()
        XCTAssertTrue(prompt.begin(id: "mic-1"))
        XCTAssertFalse(prompt.begin(id: "mic-2"))
        prompt.cancel(id: "mic-2")
        XCTAssertEqual(prompt.pending, "mic-1")
        prompt.clearPending()
        XCTAssertFalse(prompt.begin(id: "mic-3"))
        XCTAssertEqual(prompt.settle(id: "mic-1", allowed: true), .denied("mic-1"))
        XCTAssertTrue(prompt.begin(id: "mic-3"))
        XCTAssertEqual(prompt.settle(id: "mic-3", allowed: false), .denied("mic-3"))

        XCTAssertTrue(prompt.begin(id: "mic-4"))
        XCTAssertEqual(prompt.settle(id: "mic-4", allowed: true), .prepared("mic-4"))
        XCTAssertNil(prompt.pending)
        XCTAssertFalse(prompt.outstanding)
        XCTAssertEqual(prompt.settle(id: "mic-4", allowed: true), .denied("mic-4"))
    }
}
