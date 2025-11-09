//
//  GoogleCalendarScheduleService.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/9/25.
//

import Foundation
import os

private let scheduleLogger = Logger(subsystem: "com.noon.app", category: "GoogleCalendarScheduleService")

struct GoogleCalendarSchedule: Decodable {
    struct Window: Decodable {
        let start: Date
        let end: Date
        let timezone: String
        let startDate: Date
        let endDate: Date

        private enum CodingKeys: String, CodingKey {
            case start
            case end
            case timezone
            case startDate = "start_date"
            case endDate = "end_date"
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)

            let startString = try container.decode(String.self, forKey: .start)
            let endString = try container.decode(String.self, forKey: .end)
            let startDateString = try container.decode(String.self, forKey: .startDate)
            let endDateString = try container.decode(String.self, forKey: .endDate)

            self.timezone = try container.decode(String.self, forKey: .timezone)

            guard let start = Self.parseDateTime(startString),
                  let end = Self.parseDateTime(endString) else {
                throw DecodingError.dataCorruptedError(
                    forKey: .start,
                    in: container,
                    debugDescription: "Unable to decode start/end into ISO 8601 dates."
                )
            }

            guard let startDate = Self.dateFormatter.date(from: startDateString),
                  let endDate = Self.dateFormatter.date(from: endDateString) else {
                throw DecodingError.dataCorruptedError(
                    forKey: .startDate,
                    in: container,
                    debugDescription: "Unable to decode start_date/end_date into yyyy-MM-dd dates."
                )
            }

            self.start = start
            self.end = end
            self.startDate = startDate
            self.endDate = endDate
        }

        private static let dateTimeFormatters: [ISO8601DateFormatter] = {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            let fallback = ISO8601DateFormatter()
            fallback.formatOptions = [.withInternetDateTime]
            return [formatter, fallback]
        }()

        private static let fallbackDateFormatters: [DateFormatter] = {
            let formats = [
                "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXXXX",
                "yyyy-MM-dd'T'HH:mm:ss.SSSXXX",
                "yyyy-MM-dd'T'HH:mm:ssXXXXX",
            ]
            return formats.map { pattern in
                let formatter = DateFormatter()
                formatter.calendar = Calendar(identifier: .gregorian)
                formatter.locale = Locale(identifier: "en_US_POSIX")
                formatter.timeZone = TimeZone(secondsFromGMT: 0)
                formatter.dateFormat = pattern
                return formatter
            }
        }()

        private static let dateFormatter: DateFormatter = {
            let formatter = DateFormatter()
            formatter.calendar = Calendar(identifier: .gregorian)
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = TimeZone(secondsFromGMT: 0)
            formatter.dateFormat = "yyyy-MM-dd"
            return formatter
        }()

        private static func parseDateTime(_ string: String) -> Date? {
            for formatter in dateTimeFormatters {
                if let date = formatter.date(from: string) {
                    return date
                }
            }
            for formatter in fallbackDateFormatters {
                if let date = formatter.date(from: string) {
                    return date
                }
            }
            return nil
        }
    }

    let window: Window
    let events: [CalendarEvent]
}

enum GoogleCalendarScheduleServiceError: Error {
    case invalidURL
    case unauthorized
    case http(Int)
    case decoding(Error)
    case network(Error)
    case unexpectedResponse
}

extension GoogleCalendarScheduleServiceError: LocalizedError {
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Unable to prepare the Google Calendar request."
        case .unauthorized:
            return "Your Google account authorization expired. Please re-link it to continue."
        case .http(let statusCode):
            return "Google Calendar returned an unexpected response (\(statusCode))."
        case .decoding:
            return "Received an unexpected schedule format from Google Calendar."
        case .network:
            return "A network error prevented loading your schedule."
        case .unexpectedResponse:
            return "Received an unexpected response from Google Calendar."
        }
    }

    var failureReason: String? {
        switch self {
        case .decoding(let error),
             .network(let error):
            return error.localizedDescription
        case .http(let statusCode):
            return "Status code \(statusCode)"
        default:
            return nil
        }
    }
}

protocol GoogleCalendarScheduleServicing {
    func fetchSchedule(
        startDate: Date,
        endDate: Date,
        timezone: String,
        accessToken: String
    ) async throws -> GoogleCalendarSchedule
}

struct GoogleCalendarScheduleService: GoogleCalendarScheduleServicing {
    private let baseURL: URL
    private let urlSession: URLSession

    init(
        baseURL: URL = GoogleCalendarScheduleService.defaultBaseURL(),
        urlSession: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.urlSession = urlSession
    }

    func fetchSchedule(
        startDate: Date,
        endDate: Date,
        timezone: String,
        accessToken: String
    ) async throws -> GoogleCalendarSchedule {
        let request = try makeRequest(
            path: "/google-calendar/schedule",
            accessToken: accessToken,
            startDate: startDate,
            endDate: endDate,
            timezone: timezone
        )

        do {
            let (data, response) = try await urlSession.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                scheduleLogger.error("❌ Non-HTTP response when fetching schedule")
                throw GoogleCalendarScheduleServiceError.unexpectedResponse
            }

            guard 200..<300 ~= httpResponse.statusCode else {
                if httpResponse.statusCode == 401 {
                    scheduleLogger.error("🚫 Unauthorized when fetching schedule")
                    throw GoogleCalendarScheduleServiceError.unauthorized
                }

                if let payload = String(data: data, encoding: .utf8) {
                    scheduleLogger.error("❌ HTTP \(httpResponse.statusCode, privacy: .public) when fetching schedule: \(payload, privacy: .private)")
                } else {
                    scheduleLogger.error("❌ HTTP \(httpResponse.statusCode, privacy: .public) when fetching schedule with empty body")
                }

                throw GoogleCalendarScheduleServiceError.http(httpResponse.statusCode)
            }

            do {
                let decoder = JSONDecoder()
                let schedule = try decoder.decode(GoogleCalendarSchedule.self, from: data)
                scheduleLogger.debug("✅ Loaded schedule with \(schedule.events.count, privacy: .public) events")
                return schedule
            } catch {
                scheduleLogger.error("❌ Decoding schedule failed: \(String(describing: error))")
                throw GoogleCalendarScheduleServiceError.decoding(error)
            }
        } catch {
            if let scheduleError = error as? GoogleCalendarScheduleServiceError {
                throw scheduleError
            }
            scheduleLogger.error("❌ Network error when fetching schedule: \(String(describing: error))")
            throw GoogleCalendarScheduleServiceError.network(error)
        }
    }
}

private extension GoogleCalendarScheduleService {
    static func defaultBaseURL() -> URL {
        if let override = ProcessInfo.processInfo.environment["NOON_BACKEND_URL"],
           let url = URL(string: override) {
            return url
        }
        return URL(string: "http://localhost:8000")!
    }

    func makeRequest(
        path: String,
        accessToken: String,
        startDate: Date,
        endDate: Date,
        timezone: String
    ) throws -> URLRequest {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            scheduleLogger.error("❌ Invalid URL for schedule endpoint: \(path, privacy: .public)")
            throw GoogleCalendarScheduleServiceError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let payload = SchedulePayload(
            startDate: SchedulePayload.dateFormatter.string(from: startDate),
            endDate: SchedulePayload.dateFormatter.string(from: endDate),
            timezone: timezone
        )

        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(payload)

        return request
    }

    struct SchedulePayload: Encodable {
        let startDate: String
        let endDate: String
        let timezone: String

        private enum CodingKeys: String, CodingKey {
            case startDate = "start_date"
            case endDate = "end_date"
            case timezone
        }

        static let dateFormatter: DateFormatter = {
            let formatter = DateFormatter()
            formatter.calendar = Calendar(identifier: .gregorian)
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = TimeZone(secondsFromGMT: 0)
            formatter.dateFormat = "yyyy-MM-dd"
            return formatter
        }()
    }
}

