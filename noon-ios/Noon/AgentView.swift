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

            VStack(spacing: 24) {
                Spacer()

                VStack(spacing: 12) {
                    Text("Agent")
                        .font(.system(size: 44, weight: .bold, design: .rounded))
                        .foregroundStyle(ColorPalette.Text.primary)

                    Text("Ask Noon to manage your schedule, join meetings, and follow up for you.")
                        .font(.title3.weight(.medium))
                        .multilineTextAlignment(.center)
                        .foregroundStyle(ColorPalette.Text.secondary)
                        .padding(.horizontal, 32)
                }

                Spacer(minLength: 160)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .safeAreaInset(edge: .bottom) {
            microphoneButton
        }
    }

    private var microphoneButton: some View {
        Button {
            // TODO: Trigger voice capture
        } label: {
            ZStack {
                Circle()
                    .fill(ColorPalette.Gradients.primary)
                    .frame(width: 96, height: 96)
                    .shadow(
                        color: ColorPalette.Semantic.primary.opacity(0.35),
                        radius: 24,
                        x: 0,
                        y: 12
                    )

                Image(systemName: "mic.fill")
                    .font(.system(size: 36, weight: .semibold))
                    .foregroundStyle(ColorPalette.Text.inverted)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
        .padding(.bottom, 24)
    }
}

#Preview {
    AgentView()
}

