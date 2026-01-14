//
//  AgentView.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/8/25.
//

import SwiftUI

struct AgentView: View {
    @StateObject private var viewModel = AgentViewModel()
    @State private var isPressingMic = false

    @EnvironmentObject private var authViewModel: AuthViewModel
    @State private var isLoading = false
    @State private var isCreatingEvent = false
    @State private var didConfigureViewModel = false

    var body: some View {
        ZStack(alignment: .top) {
            ColorPalette.Gradients.backgroundBase
                .ignoresSafeArea()

            if viewModel.hasLoadedSchedule {
                NDayScheduleView(
                    startDate: viewModel.scheduleDate,
                    numberOfDays: viewModel.numberOfDays,
                    events: viewModel.displayEvents,
                    focusEvent: viewModel.focusEvent
                )
                .padding(.horizontal, 24)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
                .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            VStack(spacing: 0) {
                Color.clear
                    .frame(height: 24)

                ZStack(alignment: .center) {
                    microphoneButton
                    
                    if viewModel.pendingCreateEvent != nil {
                        confirmationButton
                            .offset(x: 150) // Position to the right: mic center (0) + half mic width (98) + spacing (24) + half checkmark (28) = 150
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.horizontal, 24)
            }
        }
        .onReceive(viewModel.$displayState) { state in
            handleDisplayStateChange(state)
        }
        .task {
            if didConfigureViewModel == false {
                viewModel.configure(authProvider: authViewModel)
                didConfigureViewModel = true
                viewModel.loadCurrentDaySchedule()
            }
        }
    }

    private var microphoneButton: some View {
        Button {
            // Intentionally empty; gesture handles interaction
        } label: {
            Capsule()
                .fill(ColorPalette.Gradients.primary)
                .frame(width: 196, height: 72)
                .shadow(
                    color: ColorPalette.Semantic.primary.opacity(0.35),
                    radius: 24,
                    x: 0,
                    y: 12
                )
                .overlay {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .tint(ColorPalette.Text.inverted)
                    } else {
                        Image(systemName: "mic.fill")
                            .font(.system(size: 32, weight: .semibold))
                            .foregroundStyle(ColorPalette.Text.inverted)
                    }
                }
                .frame(maxWidth: .infinity)
        }
        .scaleEffect(viewModel.isRecording ? 1.05 : 1.0)
        .opacity(viewModel.isRecording ? 0.85 : 1.0)
        .buttonStyle(.plain)
        .onLongPressGesture(
            minimumDuration: 0,
            maximumDistance: 80,
            pressing: { pressing in
                if pressing && isPressingMic == false {
                    isPressingMic = true
                    viewModel.startRecording()
                } else if pressing == false && isPressingMic {
                    isPressingMic = false
                    viewModel.stopAndSendRecording(accessToken: authViewModel.session?.accessToken)
                }
            },
            perform: {}
        )
        .padding(.bottom, 20)
    }

    private var confirmationButton: some View {
        Button {
            isCreatingEvent = true
            Task {
                await viewModel.confirmCreateEvent(accessToken: authViewModel.session?.accessToken)
                isCreatingEvent = false
            }
        } label: {
            // Gradient stroke using two-circle technique
            ZStack {
                // Outer circle with gradient (creates the stroke effect)
                Circle()
                    .fill(ColorPalette.Gradients.primary)
                    .frame(width: 56, height: 56)
                
                // Inner circle with background to create transparent-looking interior
                Circle()
                    .fill(ColorPalette.Gradients.backgroundBase)
                    .frame(width: 52, height: 52)
            }
            .shadow(
                color: ColorPalette.Semantic.primary.opacity(0.35),
                radius: 18,
                x: 0,
                y: 10
            )
            .overlay {
                if isCreatingEvent {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .tint(ColorPalette.Semantic.primary)
                } else {
                    Image(systemName: "checkmark")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundStyle(ColorPalette.Gradients.primary)
                }
            }
        }
        .buttonStyle(.plain)
        .padding(.bottom, 20)
        .disabled(isCreatingEvent)
    }

    private func handleDisplayStateChange(_ state: AgentViewModel.DisplayState) {
        switch state {
        case .recording:
            isLoading = false
        case .uploading:
            isLoading = true
        case .completed:
            isLoading = false
        case .failed(_):
            isLoading = false
        case .idle:
            isLoading = false
        }
    }
}

#Preview {
    AgentView()
        .environmentObject(AuthViewModel())
}
