//
//  AgentView.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/8/25.
//

import SwiftUI

struct AgentView: View {
    var body: some View {
        ZStack {
            ColorPalette.Gradients.backgroundBase
                .ignoresSafeArea()

            VStack(spacing: 0) {
                ScheduleView(date: Date())
                    .padding(.horizontal, 24)
                    .padding(.top, 0)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            VStack(spacing: 0) {
                Color.clear
                    .frame(height: 24)

                microphoneButton
            }
        }
    }

    private var microphoneButton: some View {
        Button {
            // TODO: Trigger voice capture
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
                    Image(systemName: "mic.fill")
                        .font(.system(size: 32, weight: .semibold))
                        .foregroundStyle(ColorPalette.Text.inverted)
                }
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
        .padding(.bottom, 20)
    }
}

#Preview {
    AgentView()
}

