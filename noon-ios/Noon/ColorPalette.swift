//
//  ColorPalette.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/8/25.
//

import SwiftUI

enum ColorPalette {
    enum Semantic {
        /// Primary brand color for emphasis against dark backgrounds.
        static let primary = Color(
            .displayP3,
            red: 1.0,
            green: 0.56,
            blue: 0.24,
            opacity: 1.0
        )

        /// Secondary accents for less prominent interactive elements.
        static let secondary = Color(
            .displayP3,
            red: 0.64,
            green: 0.54,
            blue: 0.99,
            opacity: 1.0
        )

        /// Destructive actions and critical warnings.
        static let destructive = Color(
            .displayP3,
            red: 1.0,
            green: 0.32,
            blue: 0.33,
            opacity: 1.0
        )

        /// Positive status and confirmation states.
        static let success = Color(
            .displayP3,
            red: 0.31,
            green: 0.83,
            blue: 0.57,
            opacity: 1.0
        )

        /// Attention-grabbing warning tone without destructive intent.
        static let warning = Color(
            .displayP3,
            red: 1.0,
            green: 0.72,
            blue: 0.23,
            opacity: 1.0
        )
    }

    enum Text {
        static let primary = Color(
            .displayP3,
            red: 0.95,
            green: 0.95,
            blue: 0.98,
            opacity: 1.0
        )

        static let secondary = Color(
            .displayP3,
            red: 0.77,
            green: 0.79,
            blue: 0.86,
            opacity: 1.0
        )

        static let inverted = Color(
            .displayP3,
            red: 0.06,
            green: 0.07,
            blue: 0.12,
            opacity: 1.0
        )
    }

    enum Surface {
        static let background = Color(
            .displayP3,
            red: 0.05,
            green: 0.06,
            blue: 0.14,
            opacity: 1.0
        )

        static let elevated = Color(
            .displayP3,
            red: 0.08,
            green: 0.09,
            blue: 0.18,
            opacity: 1.0
        )

        static let overlay = Color(
            .displayP3,
            red: 0.12,
            green: 0.13,
            blue: 0.21,
            opacity: 0.65
        )
    }

    enum Gradients {
        /// Brand-forward orangey gradient for key calls to action.
        static let primary = LinearGradient(
            gradient: Gradient(
                colors: [
                    Color(
                        .displayP3,
                        red: 1.0,
                        green: 0.48,
                        blue: 0.29,
                        opacity: 1.0
                    ),
                    Color(
                        .displayP3,
                        red: 1.0,
                        green: 0.68,
                        blue: 0.24,
                        opacity: 1.0
                    )
                ]
            ),
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        static let backgroundBase = LinearGradient(
            gradient: Gradient(
                colors: [
                    Color(
                        .displayP3,
                        red: 0.08,
                        green: 0.09,
                        blue: 0.21,
                        opacity: 1.0
                    ),
                    Color(
                        .displayP3,
                        red: 0.01,
                        green: 0.05,
                        blue: 0.12,
                        opacity: 1.0
                    )
                ]
            ),
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        static let backgroundAccentWarm = RadialGradient(
            gradient: Gradient(
                colors: [
                    Color(
                        .displayP3,
                        red: 0.96,
                        green: 0.63,
                        blue: 0.35,
                        opacity: 0.55
                    ),
                    Color(
                        .displayP3,
                        red: 0.31,
                        green: 0.19,
                        blue: 0.05,
                        opacity: 0.0
                    )
                ]
            ),
            center: .topLeading,
            startRadius: 20,
            endRadius: 260
        )

        static let backgroundAccentCool = RadialGradient(
            gradient: Gradient(
                colors: [
                    Color(
                        .displayP3,
                        red: 0.36,
                        green: 0.74,
                        blue: 0.94,
                        opacity: 0.55
                    ),
                    Color(
                        .displayP3,
                        red: 0.05,
                        green: 0.11,
                        blue: 0.28,
                        opacity: 0.0
                    )
                ]
            ),
            center: .bottomTrailing,
            startRadius: 10,
            endRadius: 300
        )
    }
}

