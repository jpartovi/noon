//
//  SpeechRecognitionService.swift
//  Noon
//
//  Created for on-device speech recognition optimization.
//

import AVFoundation
import Combine
import Speech

/// Protocol for speech recognition service
protocol SpeechRecognitionServicing {
    func startRecording() async throws
    func stopRecording() async throws -> String?
    var isRecording: Bool { get }
    func prewarm()
    func cleanup()
}

/// Service that uses Apple's SFSpeechRecognizer for on-device speech recognition.
/// This eliminates the need for backend transcription calls, saving ~1-3 seconds per request.
@MainActor
final class SpeechRecognitionService: NSObject, ObservableObject, SpeechRecognitionServicing {

    enum RecordingError: Error {
        case permissionDenied
        case speechRecognitionUnavailable
        case noAudioCaptured
        case recognitionFailed(String)
    }

    @Published private(set) var isRecording: Bool = false
    @Published private(set) var partialTranscript: String = ""

    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var audioEngine: AVAudioEngine?
    private var finalTranscript: String = ""
    private var hasPrewarmed = false
    private var isSessionActive = false
    private var isSpeechPermissionGranted: Bool?
    private var isMicPermissionGranted: Bool?

    override init() {
        super.init()
        // Initialize with user's preferred locale, fallback to en-US
        speechRecognizer = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        speechRecognizer?.delegate = self
    }

    /// Pre-warm the audio session and check permissions to eliminate startup delay.
    func prewarm() {
        guard !hasPrewarmed else { return }

        // Check speech recognition permission status (non-blocking)
        let speechStatus = SFSpeechRecognizer.authorizationStatus()
        isSpeechPermissionGranted = (speechStatus == .authorized)

        // Check microphone permission status (non-blocking)
        let session = AVAudioSession.sharedInstance()
        if #available(iOS 17.0, *) {
            let audioApp = AVAudioApplication.shared
            isMicPermissionGranted = (audioApp.recordPermission == .granted)
        } else {
            isMicPermissionGranted = (session.recordPermission == .granted)
        }

        // Pre-configure audio session
        do {
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .duckOthers])

            if #available(iOS 13.0, *) {
                try session.setAllowHapticsAndSystemSoundsDuringRecording(true)
            }

            hasPrewarmed = true

            // Activate session in background if permissions are granted
            Task { @MainActor in
                if !isSessionActive, isMicPermissionGranted == true, isSpeechPermissionGranted == true {
                    do {
                        #if targetEnvironment(simulator)
                        try? session.setActive(true, options: .notifyOthersOnDeactivation)
                        #else
                        try session.setActive(true, options: .notifyOthersOnDeactivation)
                        #endif
                        isSessionActive = true

                        // Pre-initialize audio engine to reduce first-use latency
                        audioEngine = AVAudioEngine()
                    } catch {
                        // Silently fail - will retry during recording start
                    }
                }
            }
        } catch {
            // Silently fail - will retry during recording start
        }
    }

    /// Start recording and transcribing speech in real-time.
    func startRecording() async throws {
        guard !isRecording else { return }

        // Request permissions if needed
        try await requestPermissionsIfNeeded()

        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            throw RecordingError.speechRecognitionUnavailable
        }

        // Configure audio session
        let session = AVAudioSession.sharedInstance()
        if !hasPrewarmed {
            try session.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .duckOthers])

            if #available(iOS 13.0, *) {
                try session.setAllowHapticsAndSystemSoundsDuringRecording(true)
            }
        }

        if !isSessionActive {
            #if targetEnvironment(simulator)
            try? session.setActive(true, options: .notifyOthersOnDeactivation)
            #else
            try session.setActive(true, options: .notifyOthersOnDeactivation)
            #endif
            isSessionActive = true
        }

        // Create audio engine if needed
        if audioEngine == nil {
            audioEngine = AVAudioEngine()
        }

        guard let audioEngine = audioEngine else {
            throw RecordingError.noAudioCaptured
        }

        // Reset state
        finalTranscript = ""
        partialTranscript = ""

        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw RecordingError.recognitionFailed("Failed to create recognition request")
        }

        // Configure for real-time results
        recognitionRequest.shouldReportPartialResults = true

        // Use on-device recognition if available (iOS 13+)
        if #available(iOS 13, *) {
            recognitionRequest.requiresOnDeviceRecognition = recognizer.supportsOnDeviceRecognition
        }

        // Get the audio input node
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        // Install tap on input node to capture audio
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)
        }

        // Start audio engine
        audioEngine.prepare()
        try audioEngine.start()

        // Start recognition task
        recognitionTask = recognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            Task { @MainActor in
                guard let self = self else { return }

                if let result = result {
                    // Update transcript with best transcription
                    let transcript = result.bestTranscription.formattedString
                    self.partialTranscript = transcript

                    if result.isFinal {
                        self.finalTranscript = transcript
                    }
                }

                if error != nil {
                    // Recognition ended - could be normal end or error
                    // Don't treat all errors as failures since the task may have been cancelled
                }
            }
        }

        isRecording = true
    }

    /// Stop recording and return the transcribed text.
    func stopRecording() async throws -> String? {
        guard isRecording else { return nil }

        // Stop audio engine
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)

        // End recognition request
        recognitionRequest?.endAudio()

        // Cancel the recognition task
        recognitionTask?.cancel()

        // Wait a brief moment for any final results
        try? await Task.sleep(nanoseconds: 100_000_000) // 100ms

        // Get the transcript
        let transcript = !finalTranscript.isEmpty ? finalTranscript : partialTranscript

        // Cleanup
        recognitionRequest = nil
        recognitionTask = nil
        isRecording = false
        partialTranscript = ""
        finalTranscript = ""

        guard !transcript.isEmpty else {
            throw RecordingError.noAudioCaptured
        }

        return transcript
    }

    /// Clean up audio session resources.
    func cleanup() {
        guard isSessionActive else { return }

        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()

        let session = AVAudioSession.sharedInstance()
        #if targetEnvironment(simulator)
        try? session.setActive(false, options: .notifyOthersOnDeactivation)
        #else
        do {
            try session.setActive(false, options: .notifyOthersOnDeactivation)
        } catch {
            // Silently ignore cleanup errors
        }
        #endif
        isSessionActive = false
    }

    // MARK: - Private Methods

    private func requestPermissionsIfNeeded() async throws {
        // Check and request speech recognition permission
        if isSpeechPermissionGranted != true {
            let speechStatus = SFSpeechRecognizer.authorizationStatus()

            switch speechStatus {
            case .authorized:
                isSpeechPermissionGranted = true
            case .denied, .restricted:
                isSpeechPermissionGranted = false
                throw RecordingError.permissionDenied
            case .notDetermined:
                let granted = await withCheckedContinuation { continuation in
                    SFSpeechRecognizer.requestAuthorization { status in
                        continuation.resume(returning: status == .authorized)
                    }
                }
                isSpeechPermissionGranted = granted
                if !granted {
                    throw RecordingError.permissionDenied
                }
            @unknown default:
                throw RecordingError.permissionDenied
            }
        }

        // Check and request microphone permission
        if isMicPermissionGranted != true {
            let session = AVAudioSession.sharedInstance()
            let micGranted: Bool

            if #available(iOS 17.0, *) {
                let audioApp = AVAudioApplication.shared
                switch audioApp.recordPermission {
                case .granted:
                    micGranted = true
                case .undetermined:
                    micGranted = await AVAudioApplication.requestRecordPermission()
                default:
                    micGranted = false
                }
            } else {
                switch session.recordPermission {
                case .granted:
                    micGranted = true
                case .undetermined:
                    micGranted = await withCheckedContinuation { continuation in
                        session.requestRecordPermission { granted in
                            continuation.resume(returning: granted)
                        }
                    }
                default:
                    micGranted = false
                }
            }

            isMicPermissionGranted = micGranted
            if !micGranted {
                throw RecordingError.permissionDenied
            }
        }
    }
}

// MARK: - SFSpeechRecognizerDelegate

extension SpeechRecognitionService: SFSpeechRecognizerDelegate {
    nonisolated func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        // Handle availability changes if needed
    }
}
