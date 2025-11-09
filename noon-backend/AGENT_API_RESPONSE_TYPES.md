# Agent API Response Types

This document outlines the exact JSON response structure for the `/agent/chat` endpoint.

## Endpoint

**POST** `/agent/chat`

**Authentication**: Bearer token required in `Authorization` header

**Request Body**:
```json
{
  "text": "Schedule a meeting tomorrow at 2pm"
}
```

## Response Schema

### Base Response Structure

All responses follow this structure:

```typescript
interface AgentChatResponse {
  tool: string;           // The action/tool that was executed
  summary: string;       // Human-readable summary of what was done
  result: object | null; // Full tool result with structured data from the operation
  success: boolean;      // Whether the operation succeeded
}
```

## Tool Types

The `tool` field can be one of the following values:
- `"create"` - Event was created
- `"read"` - Events were read/listed
- `"search"` - Events were searched
- `"update"` - Event was updated
- `"delete"` - Event was deleted
- `"schedule"` - Schedule was retrieved for a date range

## Response Examples by Tool Type

### 1. Create Event (`tool: "create"`)

**Success Response**:
```json
{
  "tool": "create",
  "summary": "Created event: Team Meeting at 2024-01-15T14:00:00",
  "result": {
    "status": "success",
    "event_id": "abc123xyz",
    "summary": "Team Meeting",
    "start": "2024-01-15T14:00:00",
    "end": "2024-01-15T15:00:00",
    "link": "https://www.google.com/calendar/event?eid=..."
  },
  "success": true
}
```

**Error Response**:
```json
{
  "tool": "create",
  "summary": "Failed to create event: start_time and end_time are required. Parsed: start_time=None, end_time=None",
  "result": {
    "status": "error",
    "error": "start_time and end_time are required"
  },
  "success": false
}
```

### 2. Read Events (`tool: "read"`)

**Success Response** (with events):
```json
{
  "tool": "read",
  "summary": "Found 3 events:\n- Team Meeting at 2024-01-15T14:00:00\n- Lunch with Alice at 2024-01-16T12:00:00\n- Project Review at 2024-01-17T10:00:00",
  "result": {
    "status": "success",
    "count": 3,
    "events": [
      {
        "event_id": "event1",
        "summary": "Team Meeting",
        "start": "2024-01-15T14:00:00",
        "end": "2024-01-15T15:00:00",
        "description": ""
      },
      {
        "event_id": "event2",
        "summary": "Lunch with Alice",
        "start": "2024-01-16T12:00:00",
        "end": "2024-01-16T13:00:00",
        "description": ""
      },
      {
        "event_id": "event3",
        "summary": "Project Review",
        "start": "2024-01-17T10:00:00",
        "end": "2024-01-17T11:00:00",
        "description": ""
      }
    ]
  },
  "success": true
}
```

**Success Response** (no events):
```json
{
  "tool": "read",
  "summary": "No events found.",
  "result": null,
  "success": true
}
```

**Error Response**:
```json
{
  "tool": "read",
  "summary": "Failed to read events: Invalid calendar ID",
  "result": null,
  "success": false
}
```

### 3. Search Events (`tool: "search"`)

**Success Response** (with matches):
```json
{
  "tool": "search",
  "summary": "Found 2 events matching 'meeting':\n- Team Meeting at 2024-01-15T14:00:00\n- Client Meeting at 2024-01-18T15:00:00",
  "result": null,
  "success": true
}
```

**Success Response** (no matches):
```json
{
  "tool": "search",
  "summary": "No events found matching 'conference'",
  "result": null,
  "success": true
}
```

**Error Response**:
```json
{
  "tool": "search",
  "summary": "Error: query is required for search",
  "result": null,
  "success": false
}
```

### 4. Update Event (`tool: "update"`)

**Success Response**:
```json
{
  "tool": "update",
  "summary": "Updated event: Team Meeting",
  "result": null,
  "success": true
}
```

**Error Response** (missing event_id):
```json
{
  "tool": "update",
  "summary": "Error: event_id is required for update",
  "result": null,
  "success": false
}
```

**Error Response** (update failed):
```json
{
  "tool": "update",
  "summary": "Failed to update event: Event not found",
  "result": null,
  "success": false
}
```

### 5. Delete Event (`tool: "delete"`)

**Success Response**:
```json
{
  "tool": "delete",
  "summary": "Deleted event: Team Meeting",
  "result": null,
  "success": true
}
```

**Error Response** (missing event_id):
```json
{
  "tool": "delete",
  "summary": "Error: event_id is required for delete",
  "result": null,
  "success": false
}
```

**Error Response** (delete failed):
```json
{
  "tool": "delete",
  "summary": "Failed to delete event: Event not found",
  "result": null,
  "success": false
}
```

### 6. Get Schedule (`tool: "schedule"`)

**Success Response** (with events):
```json
{
  "tool": "schedule",
  "summary": "Schedule from 2024-01-15T00:00:00 to 2024-01-19T23:59:59:\nFound 5 events:\n- Team Meeting at 2024-01-15T14:00:00 (until 2024-01-15T15:00:00)\n- Lunch with Alice at 2024-01-16T12:00:00 (until 2024-01-16T13:00:00)\n- Project Review at 2024-01-17T10:00:00 (until 2024-01-17T11:00:00)\n- Client Meeting at 2024-01-18T15:00:00 (until 2024-01-18T16:00:00)\n- Weekly Sync at 2024-01-19T09:00:00 (until 2024-01-19T10:00:00)",
  "result": null,
  "success": true
}
```

**Success Response** (no events):
```json
{
  "tool": "schedule",
  "summary": "No events found in the date range from 2024-01-15T00:00:00 to 2024-01-19T23:59:59.",
  "result": null,
  "success": true
}
```

**Error Response** (missing date range):
```json
{
  "tool": "schedule",
  "summary": "Error: start_time and end_time are required for schedule retrieval",
  "result": null,
  "success": false
}
```

## Error Responses (HTTP Level)

### 400 Bad Request

**Missing Google Account**:
```json
{
  "detail": "User has no Google Calendar access token. Please link your Google account first."
}
```

**Failed to Load User Context**:
```json
{
  "detail": "Failed to load user context: User abc123 not found"
}
```

### 401 Unauthorized

**Invalid Token**:
```json
{
  "detail": "Invalid or expired token"
}
```

### 500 Internal Server Error

**Agent Invocation Failed**:
```json
{
  "detail": "Agent invocation failed: <error message>"
}
```

## TypeScript Type Definition

```typescript
type AgentTool = 
  | "create" 
  | "read" 
  | "search" 
  | "update" 
  | "delete" 
  | "schedule";

interface AgentChatResponse {
  tool: AgentTool;
  summary: string;
  result: Record<string, any> | null;
  success: boolean;
}

interface AgentChatRequest {
  text: string;
}

// HTTP Error Response
interface ErrorResponse {
  detail: string;
}
```

## Summary Field Format

The `summary` field is a human-readable string that describes what happened. It may contain:
- Newline characters (`\n`) for multi-line formatting
- Event titles, times, and dates
- Error messages
- Counts of events found

## Result Field Structure

The `result` field contains structured data from the Google Calendar API operation. The structure varies by tool type:

### Create Event Result
```json
{
  "status": "success",
  "event_id": "string",
  "summary": "string",
  "start": "ISO 8601 datetime",
  "end": "ISO 8601 datetime",
  "link": "string (optional)"
}
```

### Read/Search/Schedule Result
```json
{
  "status": "success",
  "count": number,
  "events": [
    {
      "event_id": "string",
      "summary": "string",
      "start": "ISO 8601 datetime",
      "end": "ISO 8601 datetime",
      "description": "string"
    }
  ]
}
```

### Update Event Result
```json
{
  "status": "success",
  "event_id": "string",
  "summary": "string",
  "start": "ISO 8601 datetime",
  "end": "ISO 8601 datetime",
  "link": "string (optional)"
}
```

### Delete Event Result
```json
{
  "status": "success",
  "event_id": "string",
  "summary": "string",
  "message": "string"
}
```

### Error Result
```json
{
  "status": "error",
  "error": "string"
}
```

**Note**: The `result` field will be `null` if an exception occurs during agent execution (not from the Google Calendar API).

