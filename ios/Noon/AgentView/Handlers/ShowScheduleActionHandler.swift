//
//  ShowScheduleActionHandler.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/9/25.
//

import Foundation

struct ShowScheduleActionResult {
    let startDate: Date
    let displayEvents: [DisplayEvent]
}

protocol ShowScheduleActionHandling {
    func handle(
        response: ShowScheduleResponse,
        accessToken: String
    ) async throws -> ShowScheduleActionResult
}

struct ShowScheduleActionHandler: ShowScheduleActionHandling {
    private let scheduleService: GoogleCalendarScheduleServicing

    init(scheduleService: GoogleCalendarScheduleServicing = GoogleCalendarScheduleService()) {
        self.scheduleService = scheduleService
    }

    func handle(
        response: ShowScheduleResponse,
        accessToken: String
    ) async throws -> ShowScheduleActionResult {
        let metadata = response.metadata
        let timezone = TimeZone.autoupdatingCurrent.identifier

        let startDate = try parseDate(from: metadata.startDateISO)
        let endDate = try parseDate(from: metadata.endDateISO)

        let schedule = try await scheduleService.fetchSchedule(
            startDate: startDate,
            endDate: endDate,
            timezone: timezone,
            accessToken: accessToken
        )

        let events = schedule.events.map { DisplayEvent(event: $0) }

        // ScheduleView expects a specific day; use the start date from the agent response.
        let calendar = Calendar.autoupdatingCurrent
        let normalizedStartDate = calendar.startOfDay(for: startDate)

        return ShowScheduleActionResult(
            startDate: normalizedStartDate,
            displayEvents: events
        )
    }
}

private extension ShowScheduleActionHandler {
    func parseDate(from isoString: String) throws -> Date {
        if let date = Self.dateTimeFormatter.date(from: isoString) {
            return date
        }
        if let date = Self.dateFormatter.date(from: isoString) {
            return date
        }
        throw DateParseError.invalidFormat(isoString)
    }

    enum DateParseError: Error {
        case invalidFormat(String)
    }

    static let dateTimeFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [
            .withInternetDateTime,
            .withFractionalSeconds
        ]
        return formatter
    }()

    static let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}

