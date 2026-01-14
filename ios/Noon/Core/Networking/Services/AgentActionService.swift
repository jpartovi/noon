//
//  AgentActionService.swift
//  Noon
//
//  Created by GPT-5 Codex on 11/9/25.
//

import Foundation

protocol AgentActionServicing {
    func performAgentAction(request: AgentActionRequest, accessToken: String) async throws -> AgentActionResult
}

struct AgentActionService: AgentActionServicing {
    enum ServiceError: Error {
        case invalidURL
        case unexpectedResponse
        case decodingFailed(underlying: Error)
    }

    func performAgentAction(request: AgentActionRequest, accessToken: String) async throws -> AgentActionResult {
        let baseURL = AppConfiguration.agentBaseURL
        guard let endpoint = URL(string: "/api/v1/agent/action", relativeTo: baseURL) else {
            throw ServiceError.invalidURL
        }

        var urlRequest = URLRequest(url: endpoint)
        urlRequest.httpMethod = "POST"
        urlRequest.addValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let boundary = UUID().uuidString
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let bodyData = try buildMultipartBody(request: request, boundary: boundary)
        urlRequest.httpBody = bodyData

        let (data, response) = try await NetworkSession.shared.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw ServiceError.unexpectedResponse
        }

        let statusCode = httpResponse.statusCode
        guard 200..<300 ~= statusCode else {
            let message = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw ServerError(statusCode: statusCode, message: message)
        }

        do {
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            let agentResponse = try decoder.decode(AgentResponse.self, from: data)

            return AgentActionResult(statusCode: statusCode, data: data, agentResponse: agentResponse)
        } catch {
            throw ServiceError.decodingFailed(underlying: error)
        }
    }
}

private extension AgentActionService {
    func buildMultipartBody(request: AgentActionRequest, boundary: String) throws -> Data {
        var body = Data()
        let fileData = try Data(contentsOf: request.fileURL)

        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(request.filename)\"\r\n")
        body.append("Content-Type: audio/wav\r\n\r\n")
        body.append(fileData)
        body.append("\r\n")
        body.append("--\(boundary)--\r\n")

        return body
    }
}

private extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}

