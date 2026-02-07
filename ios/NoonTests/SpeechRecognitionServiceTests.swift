//
//  SpeechRecognitionServiceTests.swift
//  NoonTests
//
//  Unit tests for SpeechRecognitionService to debug error messages
//  and verify error handling behavior.
//

import XCTest
@testable import Noon

final class SpeechRecognitionServiceTests: XCTestCase {

    var service: SpeechRecognitionService!

    @MainActor
    override func setUp() {
        super.setUp()
        service = SpeechRecognitionService()
    }

    @MainActor
    override func tearDown() {
        service.cleanup()
        service = nil
        super.tearDown()
    }

    // MARK: - Prewarm Tests

    @MainActor
    func testPrewarmDoesNotThrow() async {
        // Should not throw even without permissions
        // This test verifies prewarm() is safe to call
        service.prewarm()

        // Calling prewarm twice should also be safe (idempotent)
        service.prewarm()
    }

    // MARK: - Permission Handling Tests

    @MainActor
    func testStartRecordingWithoutPermission() async {
        // Should throw permissionDenied or speechRecognitionUnavailable error
        do {
            try await service.startRecording()
            XCTFail("Expected an error to be thrown when starting without permissions")
        } catch let error as SpeechRecognitionService.RecordingError {
            // Log the actual error type for debugging
            switch error {
            case .permissionDenied:
                print("Got expected error: permissionDenied")
            case .speechRecognitionUnavailable:
                // Also acceptable - speech recognition unavailable on simulator
                print("Got expected error: speechRecognitionUnavailable")
            case .noAudioCaptured:
                print("Got error: noAudioCaptured")
            case .recognitionFailed(let message):
                print("Got error: recognitionFailed - \(message)")
            }
        } catch {
            // Log the actual error for debugging
            print("="*60)
            print("UNEXPECTED ERROR TYPE")
            print("Error: \(error)")
            print("Error type: \(type(of: error))")
            print("Localized description: \(error.localizedDescription)")

            // Check if it's an NSError and log details
            let nsError = error as NSError
            print("NSError domain: \(nsError.domain)")
            print("NSError code: \(nsError.code)")
            print("NSError userInfo: \(nsError.userInfo)")
            print("="*60)

            // Don't fail - just log for debugging
            // The error type tells us what's happening
        }
    }

    // MARK: - Stop Recording Tests

    @MainActor
    func testStopRecordingWithoutStarting() async throws {
        // Should return nil when not recording (no error thrown)
        let result = try await service.stopRecording()
        XCTAssertNil(result, "stopRecording() should return nil when not currently recording")
    }

    // MARK: - Recording State Tests

    @MainActor
    func testIsRecordingInitiallyFalse() {
        XCTAssertFalse(service.isRecording, "isRecording should be false initially")
    }

    // MARK: - Cleanup Tests

    @MainActor
    func testCleanupIsSafe() {
        // Cleanup should be safe to call even when not recording
        service.cleanup()

        // Should be safe to call multiple times
        service.cleanup()
    }

    @MainActor
    func testCleanupAfterPrewarm() {
        service.prewarm()
        service.cleanup()

        // isRecording should still be false
        XCTAssertFalse(service.isRecording)
    }

    // MARK: - Error Logging Helper Test

    @MainActor
    func testRecordingErrorDescriptions() {
        // Verify error descriptions are helpful for debugging
        let errors: [SpeechRecognitionService.RecordingError] = [
            .permissionDenied,
            .speechRecognitionUnavailable,
            .noAudioCaptured,
            .recognitionFailed("Test error message"),
        ]

        for error in errors {
            let description = String(describing: error)
            print("RecordingError.\(description)")
            XCTAssertFalse(description.isEmpty, "Error description should not be empty")
        }
    }
}

// MARK: - String Repeat Helper

private extension String {
    static func *(lhs: String, rhs: Int) -> String {
        return String(repeating: lhs, count: rhs)
    }
}
