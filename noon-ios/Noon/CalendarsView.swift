//
//  CalendarsView.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/9/25.
//

import SwiftUI

struct CalendarsView: View {
    @StateObject private var viewModel: CalendarsViewModel
    @StateObject private var coordinator = CalendarLinkCoordinator()

    init(session: OTPSession, calendarService: CalendarServicing? = nil) {
        _viewModel = StateObject(
            wrappedValue: CalendarsViewModel(
                session: session,
                calendarService: calendarService
            )
        )
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                header
                connectButton
                content
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 32)
        }
        .background(ColorPalette.Surface.background.ignoresSafeArea())
        .navigationTitle("Calendars")
        .toolbarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadCalendars()
        }
    }
}

private extension CalendarsView {
    var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Connected Calendars")
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundStyle(ColorPalette.Text.primary)
            Text("Manage the calendars linked to your Noon account.")
                .font(.callout)
                .foregroundStyle(ColorPalette.Text.secondary)
        }
    }

    var connectButton: some View {
        Button {
            Task {
                await viewModel.linkCalendar(using: coordinator)
            }
        } label: {
            Group {
                if viewModel.isLinking {
                    HStack(spacing: 12) {
                        ProgressView()
                            .progressViewStyle(.circular)
                        Text("Opening Google Sign-In…")
                            .font(.headline)
                    }
                } else {
                    HStack(spacing: 12) {
                        Image(systemName: "plus.circle.fill")
                            .imageScale(.large)
                        Text("Connect Google Calendar")
                            .font(.headline)
                    }
                }
            }
            .foregroundStyle(ColorPalette.Text.inverted)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 18)
        }
        .buttonStyle(.plain)
        .background(ColorPalette.Gradients.primary)
        .clipShape(Capsule())
        .disabled(viewModel.isLinking)
        .shadow(
            color: ColorPalette.Semantic.primary.opacity(0.35),
            radius: 20,
            x: 0,
            y: 12
        )
        .accessibilityIdentifier("connect-google-calendar")
    }

    @ViewBuilder
    var content: some View {
        if viewModel.isLoading && viewModel.accounts.isEmpty {
            loadingState
        } else if let message = viewModel.errorMessage {
            errorState(message: message)
        } else if viewModel.accounts.isEmpty {
            emptyState
        } else {
            accountsList
        }

        if let message = viewModel.linkingMessage {
            successBanner(message)
        }

        if let error = viewModel.linkingError {
            errorBanner(error)
        }
    }

    var loadingState: some View {
        VStack(spacing: 16) {
            ProgressView()
                .progressViewStyle(.circular)
                .tint(ColorPalette.Semantic.secondary)
            Text("Loading your calendars…")
                .foregroundStyle(ColorPalette.Text.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(ColorPalette.Surface.elevated.opacity(0.6))
        )
    }

    func errorState(message: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Unable to load calendars", systemImage: "exclamationmark.triangle.fill")
                .foregroundStyle(ColorPalette.Semantic.warning)
                .font(.headline)
            Text(message)
                .foregroundStyle(ColorPalette.Text.secondary)
            Button("Retry") {
                Task {
                    await viewModel.loadCalendars(force: true)
                }
            }
            .foregroundStyle(ColorPalette.Text.primary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(ColorPalette.Surface.elevated.opacity(0.6))
        )
    }

    var emptyState: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("No calendars connected yet")
                .font(.headline)
                .foregroundStyle(ColorPalette.Text.primary)
            Text("Connect your Google Calendar to see your schedules here.")
                .foregroundStyle(ColorPalette.Text.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(ColorPalette.Surface.elevated.opacity(0.6))
        )
    }

    var accountsList: some View {
        VStack(spacing: 16) {
            ForEach(viewModel.accounts, id: \.self) { account in
                CalendarRow(account: account)
            }
        }
    }

    func successBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.seal.fill")
                .foregroundStyle(ColorPalette.Semantic.success)
            Text(message)
                .foregroundStyle(ColorPalette.Text.primary)
            Spacer()
            Button {
                viewModel.clearLinkingFeedback()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .imageScale(.medium)
                    .foregroundStyle(ColorPalette.Text.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(ColorPalette.Surface.elevated.opacity(0.7))
        )
    }

    func errorBanner(_ message: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.circle.fill")
                .foregroundStyle(ColorPalette.Semantic.warning)
            Text(message)
                .foregroundStyle(ColorPalette.Text.secondary)
            Spacer()
            Button {
                viewModel.clearLinkingFeedback()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .imageScale(.medium)
                    .foregroundStyle(ColorPalette.Text.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(ColorPalette.Surface.elevated.opacity(0.6))
        )
    }
}

private struct CalendarRow: View {
    let account: GoogleAccount

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(displayName)
                .font(.headline)
                .foregroundStyle(ColorPalette.Text.primary)
            Text(account.email)
                .font(.subheadline)
                .foregroundStyle(ColorPalette.Text.secondary)
            Text("Google ID: \(account.googleUserId)")
                .font(.caption)
                .foregroundStyle(ColorPalette.Text.secondary.opacity(0.8))
            Divider()
                .background(ColorPalette.Surface.overlay)
            HStack(spacing: 12) {
                Label(formatted(date: account.createdAt), systemImage: "calendar.badge.clock")
                Spacer()
                Label("Updated \(formatted(relative: account.updatedAt))", systemImage: "arrow.clockwise.circle")
            }
            .font(.caption)
            .foregroundStyle(ColorPalette.Text.secondary.opacity(0.9))
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(ColorPalette.Surface.elevated.opacity(0.85))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24)
                .stroke(ColorPalette.Surface.overlay.opacity(0.5), lineWidth: 1)
        )
    }

    private var displayName: String {
        if let name = account.displayName, name.isEmpty == false {
            return name
        }
        return account.email
    }

    private func formatted(date: Date) -> String {
        date.formatted(date: .abbreviated, time: .shortened)
    }

    private func formatted(relative date: Date) -> String {
        date.formatted(.relative(presentation: .named))
    }
}

#Preview {
    let session = OTPSession(accessToken: "token", refreshToken: nil, tokenType: "bearer", expiresIn: nil)
    return NavigationStack {
        CalendarsView(session: session, calendarService: MockCalendarService())
    }
    .preferredColorScheme(.dark)
}

private struct MockCalendarService: CalendarServicing {
    func fetchCalendars(accessToken: String) async throws -> [GoogleAccount] {
        [
            GoogleAccount(
                id: UUID().uuidString,
                userId: UUID().uuidString,
                googleUserId: "primary",
                email: "alex@example.com",
                displayName: "Alex Primary Calendar",
                avatarURL: nil,
                createdAt: Date().addingTimeInterval(-86_400 * 4),
                updatedAt: Date().addingTimeInterval(-3_600)
            ),
            GoogleAccount(
                id: UUID().uuidString,
                userId: UUID().uuidString,
                googleUserId: "work",
                email: "alex@work.com",
                displayName: "Work",
                avatarURL: nil,
                createdAt: Date().addingTimeInterval(-86_400 * 20),
                updatedAt: Date().addingTimeInterval(-9_000)
            ),
        ]
    }

    func beginGoogleOAuth(accessToken: String) async throws -> GoogleOAuthStart {
        GoogleOAuthStart(
            authorizationURL: URL(string: "https://accounts.google.com/o/oauth2/v2/auth?mock=true")!,
            state: "mock-state",
            stateExpiresAt: Date().addingTimeInterval(300)
        )
    }
}

