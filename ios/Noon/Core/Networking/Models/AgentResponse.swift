//
//  AgentResponse.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/9/25.
//

import Foundation

enum AgentResponseKind: String, Codable, Sendable {
    case showEvent = "show-event"
    case showSchedule = "show-schedule"
    case createEvent = "create-event"
    case updateEvent = "update-event"
    case deleteEvent = "delete-event"
    case noAction = "no-action"
}

@preconcurrency protocol AgentSuccessResponse: Sendable {
    associatedtype Metadata: Sendable
    var success: Bool { get }
    var type: AgentResponseKind { get }
    var metadata: Metadata { get }
}

struct AgentErrorResponse: Codable, Sendable, Error {
    let success: Bool
    let message: String

    init(message: String) {
        self.success = false
        self.message = message
    }
}

enum AgentResponse: Codable, Sendable {
    case showEvent(ShowEventResponse)
    case showSchedule(ShowScheduleResponse)
    case createEvent(CreateEventResponse)
    case updateEvent(UpdateEventResponse)
    case deleteEvent(DeleteEventResponse)
    case noAction(NoActionResponse)
    case error(AgentErrorResponse)

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let success = try container.decode(Bool.self, forKey: .success)

        if success {
            let kind = try container.decode(AgentResponseKind.self, forKey: .type)
            switch kind {
            case .showEvent:
                self = .showEvent(try ShowEventResponse(from: decoder))
            case .showSchedule:
                self = .showSchedule(try ShowScheduleResponse(from: decoder))
            case .createEvent:
                self = .createEvent(try CreateEventResponse(from: decoder))
            case .updateEvent:
                self = .updateEvent(try UpdateEventResponse(from: decoder))
            case .deleteEvent:
                self = .deleteEvent(try DeleteEventResponse(from: decoder))
            case .noAction:
                self = .noAction(try NoActionResponse(from: decoder))
            }
        } else {
            self = .error(try AgentErrorResponse(from: decoder))
        }
    }

    func encode(to encoder: Encoder) throws {
        switch self {
        case .showEvent(let response):
            try response.encode(to: encoder)
        case .showSchedule(let response):
            try response.encode(to: encoder)
        case .createEvent(let response):
            try response.encode(to: encoder)
        case .updateEvent(let response):
            try response.encode(to: encoder)
        case .deleteEvent(let response):
            try response.encode(to: encoder)
        case .noAction(let response):
            try response.encode(to: encoder)
        case .error(let error):
            try error.encode(to: encoder)
        }
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
    }
}

struct ShowEventResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: ShowEventMetadata

    typealias Metadata = ShowEventMetadata

    init(metadata: ShowEventMetadata) {
        self.success = true
        self.type = .showEvent
        self.metadata = metadata
    }

    init(success: Bool, metadata: ShowEventMetadata) {
        self.success = success
        self.type = .showEvent
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .showEvent else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'show-event'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(ShowEventMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

struct ShowScheduleResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: ShowScheduleMetadata

    typealias Metadata = ShowScheduleMetadata

    init(metadata: ShowScheduleMetadata) {
        self.success = true
        self.type = .showSchedule
        self.metadata = metadata
    }

    init(success: Bool, metadata: ShowScheduleMetadata) {
        self.success = success
        self.type = .showSchedule
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .showSchedule else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'show-schedule'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(ShowScheduleMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

struct CreateEventResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: CreateEventMetadata

    typealias Metadata = CreateEventMetadata

    init(metadata: CreateEventMetadata) {
        self.success = true
        self.type = .createEvent
        self.metadata = metadata
    }

    init(success: Bool, metadata: CreateEventMetadata) {
        self.success = success
        self.type = .createEvent
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .createEvent else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'create-event'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(CreateEventMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

struct UpdateEventResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: UpdateEventMetadata

    typealias Metadata = UpdateEventMetadata

    init(metadata: UpdateEventMetadata) {
        self.success = true
        self.type = .updateEvent
        self.metadata = metadata
    }

    init(success: Bool, metadata: UpdateEventMetadata) {
        self.success = success
        self.type = .updateEvent
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .updateEvent else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'update-event'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(UpdateEventMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

struct DeleteEventResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: DeleteEventMetadata

    typealias Metadata = DeleteEventMetadata

    init(metadata: DeleteEventMetadata) {
        self.success = true
        self.type = .deleteEvent
        self.metadata = metadata
    }

    init(success: Bool, metadata: DeleteEventMetadata) {
        self.success = success
        self.type = .deleteEvent
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .deleteEvent else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'delete-event'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(DeleteEventMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

struct NoActionResponse: AgentSuccessResponse, Codable {
    let success: Bool
    let type: AgentResponseKind
    let metadata: NoActionMetadata

    typealias Metadata = NoActionMetadata

    init(metadata: NoActionMetadata) {
        self.success = true
        self.type = .noAction
        self.metadata = metadata
    }

    init(success: Bool, metadata: NoActionMetadata) {
        self.success = success
        self.type = .noAction
        self.metadata = metadata
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let decodedType = try container.decode(AgentResponseKind.self, forKey: .type)
        guard decodedType == .noAction else {
            throw DecodingError.dataCorruptedError(forKey: .type, in: container, debugDescription: "Expected type 'no-action'.")
        }
        self.success = try container.decode(Bool.self, forKey: .success)
        self.type = decodedType
        self.metadata = try container.decode(NoActionMetadata.self, forKey: .metadata)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(success, forKey: .success)
        try container.encode(type, forKey: .type)
        try container.encode(metadata, forKey: .metadata)
    }

    private enum CodingKeys: String, CodingKey {
        case success
        case type
        case metadata
    }
}

// MARK: - Metadata

struct ShowEventMetadata: Codable, Sendable {
    let eventID: String
    let calendarID: String

    private enum CodingKeys: String, CodingKey {
        case eventID = "event-id"
        case calendarID = "calendar-id"
    }
}

struct ShowScheduleMetadata: Codable, Sendable {
    let startDateISO: String
    let endDateISO: String

    private enum CodingKeys: String, CodingKey {
        case startDateISO = "start-date"
        case endDateISO = "end-date"
    }
}

struct CreateEventMetadata: Codable, Sendable {
    let payload: [String: AgentJSONValue]

    init(payload: [String: AgentJSONValue]) {
        self.payload = payload
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        self.payload = try container.decode([String: AgentJSONValue].self)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(payload)
    }
}

struct UpdateEventMetadata: Codable, Sendable {
    let eventID: String
    let calendarID: String
    let changes: [String: AgentJSONValue]

    init(eventID: String, calendarID: String, changes: [String: AgentJSONValue]) {
        self.eventID = eventID
        self.calendarID = calendarID
        self.changes = changes
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: DynamicCodingKey.self)

        guard let eventKey = DynamicCodingKey(stringValue: "event-id"),
              let calendarKey = DynamicCodingKey(stringValue: "calendar-id") else {
            throw DecodingError.keyNotFound(DynamicCodingKey(stringValue: "event-id")!, .init(codingPath: decoder.codingPath, debugDescription: "Missing keys for update event metadata"))
        }

        self.eventID = try container.decode(String.self, forKey: eventKey)
        self.calendarID = try container.decode(String.self, forKey: calendarKey)

        var remaining: [String: AgentJSONValue] = [:]
        for key in container.allKeys where key != eventKey && key != calendarKey {
            remaining[key.stringValue] = try container.decode(AgentJSONValue.self, forKey: key)
        }
        self.changes = remaining
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: DynamicCodingKey.self)

        if let eventKey = DynamicCodingKey(stringValue: "event-id") {
            try container.encode(eventID, forKey: eventKey)
        }

        if let calendarKey = DynamicCodingKey(stringValue: "calendar-id") {
            try container.encode(calendarID, forKey: calendarKey)
        }

        for (key, value) in changes {
            if let codingKey = DynamicCodingKey(stringValue: key) {
                try container.encode(value, forKey: codingKey)
            }
        }
    }
}

struct DeleteEventMetadata: Codable, Sendable {
    let eventID: String
    let calendarID: String

    private enum CodingKeys: String, CodingKey {
        case eventID = "event-id"
        case calendarID = "calendar-id"
    }
}

struct NoActionMetadata: Codable, Sendable {
    let reason: String
}

// MARK: - Helpers

struct DynamicCodingKey: CodingKey, Hashable {
    var stringValue: String
    var intValue: Int? { nil }

    init?(stringValue: String) {
        self.stringValue = stringValue
    }

    init?(intValue: Int) {
        nil
    }
}

enum AgentJSONValue: Codable, Hashable, Sendable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: AgentJSONValue])
    case array([AgentJSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if container.decodeNil() {
            self = .null
            return
        }

        if let boolValue = try? container.decode(Bool.self) {
            self = .bool(boolValue)
            return
        }

        if let doubleValue = try? container.decode(Double.self) {
            self = .number(doubleValue)
            return
        }

        if let stringValue = try? container.decode(String.self) {
            self = .string(stringValue)
            return
        }

        if let arrayValue = try? container.decode([AgentJSONValue].self) {
            self = .array(arrayValue)
            return
        }

        if let objectValue = try? container.decode([String: AgentJSONValue].self) {
            self = .object(objectValue)
            return
        }

        throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported JSON value")
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .number(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        case .object(let value):
            try container.encode(value)
        case .array(let value):
            try container.encode(value)
        case .null:
            try container.encodeNil()
        }
    }
}

