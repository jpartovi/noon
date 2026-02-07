//
//  MockSpeechRecognitionService.swift
//  NoonTests
//
//  Mock for testing AgentViewModel speech recognition flows.
//

import Combine
import Foundation
@testable import Noon

@MainActor
final class MockSpeechRecognitionService: SpeechRecognitionServicing {

    // MARK: - Call Tracking

    private(set) var startRecordingCallCount = 0
    private(set) var stopRecordingCallCount = 0
    private(set) var prewarmCallCount = 0
    private(set) var cleanupCallCount = 0

    // MARK: - Configurable Behavior

    var startRecordingError: Error?
    var stopRecordingResult: String? = "mock transcript"

    // MARK: - State

    private(set) var isRecording: Bool = false

    // MARK: - Publisher

    private let partialTranscriptSubject = CurrentValueSubject<String, Never>("")

    var partialTranscriptPublisher: AnyPublisher<String, Never> {
        partialTranscriptSubject.eraseToAnyPublisher()
    }

    // MARK: - Protocol Methods

    func startRecording() async throws {
        startRecordingCallCount += 1
        if let error = startRecordingError {
            throw error
        }
        isRecording = true
    }

    func stopRecording() async throws -> String? {
        stopRecordingCallCount += 1
        isRecording = false
        return stopRecordingResult
    }

    func prewarm() {
        prewarmCallCount += 1
    }

    func cleanup() {
        cleanupCallCount += 1
    }

    // MARK: - Test Helpers

    func simulatePartialTranscript(_ text: String) {
        partialTranscriptSubject.send(text)
    }
}
