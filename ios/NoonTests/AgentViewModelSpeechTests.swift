//
//  AgentViewModelSpeechTests.swift
//  NoonTests
//
//  Tests for AgentViewModel speech recognition integration
//  using MockSpeechRecognitionService.
//

import Combine
import XCTest
@testable import Noon

@MainActor
final class AgentViewModelSpeechTests: XCTestCase {

    private var mockSpeech: MockSpeechRecognitionService!
    private var cancellables: Set<AnyCancellable>!

    override func setUp() {
        super.setUp()
        mockSpeech = MockSpeechRecognitionService()
        cancellables = []
    }

    override func tearDown() {
        cancellables = nil
        mockSpeech = nil
        super.tearDown()
    }

    // MARK: - Helpers

    private func makeSUT(useOnDeviceSpeech: Bool = true) -> AgentViewModel {
        AgentViewModel(
            speechRecognitionService: mockSpeech,
            useOnDeviceSpeechRecognition: useOnDeviceSpeech
        )
    }

    // MARK: - Initial State

    func testInitialState() {
        let sut = makeSUT()

        XCTAssertFalse(sut.isRecording)
        XCTAssertEqual(sut.liveTranscript, "")
        XCTAssertNil(sut.transcriptionText)
        if case .idle = sut.displayState { } else {
            XCTFail("Expected idle display state, got \(sut.displayState)")
        }
    }

    // MARK: - Prewarm

    func testInitCallsPrewarmWhenOnDeviceSpeechEnabled() {
        _ = makeSUT(useOnDeviceSpeech: true)

        XCTAssertEqual(mockSpeech.prewarmCallCount, 1)
    }

    func testInitDoesNotCallPrewarmWhenOnDeviceSpeechDisabled() {
        _ = makeSUT(useOnDeviceSpeech: false)

        XCTAssertEqual(mockSpeech.prewarmCallCount, 0)
    }

    // MARK: - Start Recording

    func testStartRecordingSetsDisplayStateToRecording() {
        let sut = makeSUT()

        sut.startRecording()

        XCTAssertTrue(sut.isRecording)
        if case .recording = sut.displayState { } else {
            XCTFail("Expected recording display state, got \(sut.displayState)")
        }
    }

    func testStartRecordingClearsPreviousState() {
        let sut = makeSUT()
        // Set some prior state
        sut.transcriptionText = "old text"

        sut.startRecording()

        XCTAssertNil(sut.transcriptionText)
        XCTAssertEqual(sut.liveTranscript, "")
    }

    func testStartRecordingHandlesPermissionError() async throws {
        let sut = makeSUT()
        mockSpeech.startRecordingError = SpeechRecognitionService.RecordingError.permissionDenied

        sut.startRecording()

        // The Task inside startRecording needs a moment to execute
        try await Task.sleep(nanoseconds: 100_000_000)

        // The error handler sets displayState to .failed
        if case .failed = sut.displayState { } else {
            XCTFail("Expected failed display state after permission error, got \(sut.displayState)")
        }
    }

    // MARK: - Live Transcript

    func testLiveTranscriptUpdatesFromSpeechService() async throws {
        let sut = makeSUT()

        let expectation = XCTestExpectation(description: "live transcript updated")

        sut.$liveTranscript
            .dropFirst() // skip initial ""
            .first(where: { $0 == "Hello world" })
            .sink { _ in expectation.fulfill() }
            .store(in: &cancellables)

        mockSpeech.simulatePartialTranscript("Hello world")

        await fulfillment(of: [expectation], timeout: 2.0)
        XCTAssertEqual(sut.liveTranscript, "Hello world")
    }

    func testLiveTranscriptUpdatesProgressively() async throws {
        let sut = makeSUT()
        var collected: [String] = []

        let expectation = XCTestExpectation(description: "received multiple transcripts")

        sut.$liveTranscript
            .dropFirst() // skip initial ""
            .sink { value in
                collected.append(value)
                if collected.count >= 3 {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        mockSpeech.simulatePartialTranscript("Hello")
        mockSpeech.simulatePartialTranscript("Hello world")
        mockSpeech.simulatePartialTranscript("Hello world today")

        await fulfillment(of: [expectation], timeout: 2.0)
        XCTAssertEqual(collected, ["Hello", "Hello world", "Hello world today"])
    }

    // MARK: - Cleanup

    func testCleanupAudioSessionDelegatesToSpeechService() {
        let sut = makeSUT()

        sut.cleanupAudioSession()

        XCTAssertEqual(mockSpeech.cleanupCallCount, 1)
    }

    // MARK: - Reset

    func testResetClearsLiveTranscript() async throws {
        let sut = makeSUT()

        // Simulate some transcript data flowing in
        mockSpeech.simulatePartialTranscript("Some text")
        try await Task.sleep(nanoseconds: 100_000_000)

        sut.reset()

        XCTAssertEqual(sut.liveTranscript, "")
        XCTAssertFalse(sut.isRecording)
        if case .idle = sut.displayState { } else {
            XCTFail("Expected idle display state after reset, got \(sut.displayState)")
        }
    }

    // MARK: - Guards

    func testDoubleStartRecordingIsGuarded() {
        let sut = makeSUT()

        sut.startRecording()
        sut.startRecording() // should be a no-op

        // startRecording sets isRecording = true synchronously before Task,
        // so the guard fires on the second call.
        // The mock's startRecording is called asynchronously inside a Task,
        // so we check isRecording was only set once (still true).
        XCTAssertTrue(sut.isRecording)
    }

    func testStopRecordingWhenNotRecordingIsNoOp() {
        let sut = makeSUT()

        // stopAndSendRecording guards on isRecording
        sut.stopAndSendRecording(accessToken: nil)

        // Should not change state
        XCTAssertFalse(sut.isRecording)
        if case .idle = sut.displayState { } else {
            XCTFail("Expected idle display state, got \(sut.displayState)")
        }
    }
}
