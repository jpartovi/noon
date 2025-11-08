//
//  ContentView.swift
//  Noon
//
//  Created by Jude Partovi on 11/8/25.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        ZStack {
            backgroundGradient
                .ignoresSafeArea()

            VStack(spacing: 48) {
                Spacer()

                Text("Noon")
                    .font(.system(size: 76, weight: .bold, design: .rounded))
                    .foregroundStyle(ColorPalette.Text.primary)
                    .padding(.horizontal, 24)
                    .multilineTextAlignment(.center)

                Button(action: handleGetStarted) {
                    Text("Get Started")
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(ColorPalette.Text.inverted)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                }
                .buttonStyle(.plain)
                .background(ColorPalette.Gradients.primary)
                .clipShape(Capsule())
                .shadow(
                    color: ColorPalette.Semantic.primary.opacity(0.35),
                    radius: 24,
                    x: 0,
                    y: 14
                )
                .padding(.horizontal, 40)

                Spacer()
            }
            .frame(maxWidth: 420)
            .padding()
        }
    }

    private var backgroundGradient: some View {
        ZStack {
            ColorPalette.Gradients.backgroundBase

            ColorPalette.Gradients.backgroundAccentWarm
                .blendMode(.screen)
                .blur(radius: 20)
                .offset(x: -30, y: -50)

            ColorPalette.Gradients.backgroundAccentCool
                .blendMode(.screen)
                .blur(radius: 40)
                .offset(x: 60, y: 90)
        }
    }

    private func handleGetStarted() {
        // TODO: Wire up navigation or onboarding activation.
    }
}
