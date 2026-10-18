import Foundation

/// Single-use, monotonic ten-second microphone intent for the iOS shell.
/// Pure Foundation so the policy can be tested without WebKit or UIKit.
struct MicrophoneArmPolicy {
    static let window: TimeInterval = 10

    private(set) var intent: String?
    private(set) var armedUntil: TimeInterval = 0

    func isArmed(now: TimeInterval) -> Bool {
        intent != nil && armedUntil > now
    }

    mutating func reset() {
        intent = nil
        armedUntil = 0
    }

    mutating func arm(id: String, now: TimeInterval) {
        intent = id
        armedUntil = now + Self.window
    }

    mutating func cancel(id: String) {
        if intent == id { reset() }
    }

    /// Consumes the intent for one media grant; the arm is valid at most once.
    mutating func consume(now: TimeInterval) -> String? {
        guard let id = intent, armedUntil > now else { return nil }
        reset()
        return id
    }
}

/// The one outstanding system microphone prompt for an explicit Start-mic request.
/// Settling resolves the requesting id exactly once and never clears a newer request.
struct MicrophonePromptPolicy {
    private(set) var pending: String?
    private(set) var outstanding = false

    enum Settlement: Equatable {
        case prepared(String)
        case denied(String)
    }

    mutating func begin(id: String) -> Bool {
        guard !outstanding, pending == nil else { return false }
        pending = id
        outstanding = true
        return true
    }

    /// Navigation or teardown clears the pending document id; the system prompt
    /// itself cannot be cancelled and stays outstanding until it resolves.
    mutating func clearPending() {
        pending = nil
    }

    mutating func cancel(id: String) {
        if pending == id { pending = nil }
    }

    mutating func settle(id: String, allowed: Bool) -> Settlement {
        outstanding = false
        guard pending == id else { return .denied(id) }
        pending = nil
        return allowed ? .prepared(id) : .denied(id)
    }
}
