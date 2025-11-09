from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Literal, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, validator, root_validator

try:
	from openai import OpenAI  # type: ignore
	_OPENAI_AVAILABLE = True
except Exception:
	_OPENAI_AVAILABLE = False
	OpenAI = None  # type: ignore


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="Noon Calendar Agent Arg Planner", version="0.1.0")


# ---------------------------
# Pydantic Schemas (Arguments)
# ---------------------------

class ReminderOverride(BaseModel):
	method: Literal["email", "popup"]
	minutes: int = Field(..., ge=0)


class Reminders(BaseModel):
	useDefault: bool = True
	overrides: Optional[List[ReminderOverride]] = None

	@validator("overrides", always=True)
	def validate_overrides(cls, v, values):  # noqa: N805
		if values.get("useDefault") is False and (not v or len(v) == 0):
			raise ValueError("overrides must be provided when useDefault is False")
		return v


class EventDateTime(BaseModel):
	dateTime: datetime
	timeZone: Optional[str] = None


class EventAttendee(BaseModel):
	email: EmailStr
	displayName: Optional[str] = None
	optional: Optional[bool] = None
	responseStatus: Optional[Literal["needsAction", "declined", "tentative", "accepted"]] = None


class EventBody(BaseModel):
	summary: str
	location: Optional[str] = None
	description: Optional[str] = None
	start: EventDateTime
	end: EventDateTime
	attendees: Optional[List[EventAttendee]] = None
	recurrence: Optional[List[str]] = None
	reminders: Optional[Reminders] = None

	@validator("end")
	def end_after_start(cls, v, values):  # noqa: N805
		start_obj: Optional[EventDateTime] = values.get("start")
		if start_obj and v and v.dateTime <= start_obj.dateTime:
			raise ValueError("end.dateTime must be after start.dateTime")
		return v


# List Events (GET /calendars/{calendarId}/events)
class ListEventsArgs(BaseModel):
	calendarId: str = Field("primary", description="Calendar ID like 'primary' or a specific ID")
	timeMin: Optional[datetime] = Field(None, description="RFC3339 lower bound for event start time")
	timeMax: Optional[datetime] = Field(None, description="RFC3339 upper bound for event start time")
	singleEvents: Optional[bool] = None
	orderBy: Optional[Literal["startTime", "updated"]] = None
	maxResults: Optional[int] = Field(None, ge=1, le=2500)
	pageToken: Optional[str] = None
	q: Optional[str] = Field(None, description="Free-text search")
	showDeleted: Optional[bool] = None
	timeZone: Optional[str] = None

	@validator("orderBy")
	def validate_order_by_value(cls, v):  # noqa: N805
		return v

	@validator("singleEvents")
	def validate_single_events_value(cls, v):  # noqa: N805
		return v

	@root_validator
	def _ensure_order_single_events_consistency(cls, values: dict) -> dict:  # noqa: N805
		order_by = values.get("orderBy")
		single_events = values.get("singleEvents")
		if order_by == "startTime" and single_events is not True:
			raise ValueError("orderBy='startTime' requires singleEvents=True")
		return values


# Get Event (GET /calendars/{calendarId}/events/{eventId})
class GetEventArgs(BaseModel):
	calendarId: str = "primary"
	eventId: str
	timeZone: Optional[str] = None
	maxAttendees: Optional[int] = Field(None, ge=1)


# Insert Event (POST /calendars/{calendarId}/events)
class InsertEventArgs(BaseModel):
	calendarId: str = "primary"
	body: EventBody
	conferenceDataVersion: Optional[int] = Field(None, ge=0, le=2)
	sendUpdates: Optional[Literal["all", "externalOnly", "none"]] = None
	maxAttendees: Optional[int] = Field(None, ge=1)
	supportsAttachments: Optional[bool] = None


# Update Event (PUT /calendars/{calendarId}/events/{eventId})
class UpdateEventArgs(BaseModel):
	calendarId: str = "primary"
	eventId: str
	body: EventBody
	conferenceDataVersion: Optional[int] = Field(None, ge=0, le=2)
	sendUpdates: Optional[Literal["all", "externalOnly", "none"]] = None
	maxAttendees: Optional[int] = Field(None, ge=1)
	supportsAttachments: Optional[bool] = None


# Delete Event (DELETE /calendars/{calendarId}/events/{eventId})
class DeleteEventArgs(BaseModel):
	calendarId: str = "primary"
	eventId: str
	sendUpdates: Optional[Literal["all", "externalOnly", "none"]] = None


# ---------------------------
# Operation Union (Discriminated)
# ---------------------------

class OperationName(str, Enum):
	list_events = "list_events"
	get_event = "get_event"
	insert_event = "insert_event"
	update_event = "update_event"
	delete_event = "delete_event"


class ListEventsOperation(BaseModel):
	op: Literal[OperationName.list_events]
	args: ListEventsArgs


class GetEventOperation(BaseModel):
	op: Literal[OperationName.get_event]
	args: GetEventArgs


class InsertEventOperation(BaseModel):
	op: Literal[OperationName.insert_event]
	args: InsertEventArgs


class UpdateEventOperation(BaseModel):
	op: Literal[OperationName.update_event]
	args: UpdateEventArgs


class DeleteEventOperation(BaseModel):
	op: Literal[OperationName.delete_event]
	args: DeleteEventArgs


OperationUnion = Union[
	ListEventsOperation,
	GetEventOperation,
	InsertEventOperation,
	UpdateEventOperation,
	DeleteEventOperation,
]


class CalendarAgentPlan(BaseModel):
	model: str = Field(..., description="LLM model used to parse the plan")
	operations: List[OperationUnion] = Field(..., description="Ordered list of Google Calendar operations to execute")
	reasoning: Optional[str] = Field(None, description="Brief rationale for chosen operations")


# ---------------------------
# Request/Response Models
# ---------------------------

class ParseArgsRequest(BaseModel):
	query: str = Field(..., description="Natural language instruction")
	defaultCalendarId: Optional[str] = Field("primary", description="Default calendar ID to use when unspecified")
	now: Optional[datetime] = Field(None, description="Reference time for relative expressions, default is current UTC")
	timeZone: Optional[str] = Field(None, description="IANA timezone to prefer in results, e.g., 'America/Los_Angeles'")
	maxOperations: Optional[int] = Field(5, ge=1, le=20, description="Upper bound on number of operations to return")
	model: Optional[str] = Field(None, description="LLM model override (defaults to 'gpt-5')")


# ---------------------------
# Helpers: JSON Schema for Structured Outputs
# ---------------------------

def _pydantic_schema_for_plan() -> dict:
	"""
	Build a JSON schema compatible with OpenAI structured outputs for CalendarAgentPlan.
	Pydantic's .schema() yields Draft-07 JSON schema; we can use it directly.
	"""
	schema = CalendarAgentPlan.schema()
	# Make schema stricter by default
	def _disallow_additional(obj: dict):
		if isinstance(obj, dict):
			if "type" in obj and obj.get("type") == "object":
				obj.setdefault("additionalProperties", False)
			for v in obj.values():
				_disallow_additional(v) if isinstance(v, dict) else None
			for v in obj.get("properties", {}).values():
				_disallow_additional(v)
			if "items" in obj and isinstance(obj["items"], dict):
				_disallow_additional(obj["items"])

	_disallow_additional(schema)
	return schema


def _default_now_utc() -> datetime:
	return datetime.now(timezone.utc)


# ---------------------------
# Lightweight Rule-based Fallback
# ---------------------------

def _simple_rule_based_plan(req: ParseArgsRequest) -> CalendarAgentPlan:
	"""
	Fallback when LLM is unavailable. Handles a few common phrasings.
	"""
	text = req.query.lower()
	now = req.now or _default_now_utc()
	calendar_id = req.defaultCalendarId or "primary"

	ops: List[OperationUnion] = []

	def day_bounds(dt: datetime) -> tuple[datetime, datetime]:
		start = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
		end = start + timedelta(days=1)
		return start, end

	# Explicit no-op intents
	if any(
		phrase in text
		for phrase in [
			"do nothing",
			"no-op",
			"no op",
			"no change",
			"ignore",
			"never mind",
			"nevermind",
			"cancel that",
			"cancel",
			"nothing",
		]
	):
		return CalendarAgentPlan(model="rule-based", operations=[], reasoning="No action requested")

	# List schedule today/tomorrow/this week
	if any(k in text for k in ["what's on", "whats on", "agenda", "schedule", "show events", "list events", "what do i have"]):
		time_min: Optional[datetime] = None
		time_max: Optional[datetime] = None
		if "today" in text:
			time_min, time_max = day_bounds(now)
		elif "tomorrow" in text:
			tomorrow = now + timedelta(days=1)
			time_min, time_max = day_bounds(tomorrow)
		elif "next week" in text or "coming week" in text:
			# Next 7 days
			time_min = now
			time_max = now + timedelta(days=7)
		op = ListEventsOperation(
			op=OperationName.list_events,
			args=ListEventsArgs(
				calendarId=calendar_id,
				timeMin=time_min,
				timeMax=time_max,
				singleEvents=True,
				orderBy=None,
				maxResults=50,
				timeZone=req.timeZone,
			),
		)
		ops.append(op)

	# Get by event id if phrase contains "event <id>"
	if "event " in text and "details" in text:
		try:
			# crude extract last token as id
			event_id = text.split("event ", 1)[1].split()[0]
			ops.append(GetEventOperation(op=OperationName.get_event, args=GetEventArgs(calendarId=calendar_id, eventId=event_id, timeZone=req.timeZone)))
		except Exception:
			pass

	# If nothing matched, default to a broad list
	if not ops:
		# If user explicitly indicates no intention inferred, return no-op; else broad search
		if any(p in text for p in ["no intent", "no action", "none"]):
			return CalendarAgentPlan(model="rule-based", operations=[], reasoning="No actionable intent recognized")
		else:
			ops.append(
				ListEventsOperation(
					op=OperationName.list_events,
					args=ListEventsArgs(calendarId=calendar_id, q=req.query, singleEvents=True, maxResults=25, timeZone=req.timeZone),
				)
			)

	return CalendarAgentPlan(model="rule-based", operations=ops, reasoning="Rule-based fallback applied")


# ---------------------------
# LLM Planning with Structured Outputs
# ---------------------------

def _llm_plan(req: ParseArgsRequest) -> CalendarAgentPlan:
	if not _OPENAI_AVAILABLE:
		raise RuntimeError("OpenAI SDK not available")

	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY not set")

	# Use a snapshot that supports Structured Outputs
	model = req.model or os.getenv("OPENAI_MODEL", "gpt-4.1")
	client = OpenAI(api_key=api_key)

	now = (req.now or _default_now_utc()).isoformat()

	# System and user prompts engineered for structured decision-making.
	system_prompt = (
		"You are a calendar planning assistant that translates natural language into Google Calendar API operations. "
		"Always respond with structured data that conforms to the provided Pydantic model. "
		"Choose zero or more operations to fully satisfy the user's intent. "
		"Prefer minimal sets of operations; ensure required arguments are present and valid. "
		"If no action is required, return an empty 'operations' array with a concise 'reasoning'. "
		"All datetimes must be RFC3339 with timezone offsets. "
		"Never include extraneous fields beyond the model definition."
	)

	user_prompt = (
		f"Now: {now}\n"
		f"Default calendar: {req.defaultCalendarId or 'primary'}\n"
		f"Preferred timeZone: {req.timeZone or 'unspecified'}\n"
		f"Max operations: {req.maxOperations or 5}\n"
		f"Instruction: {req.query}\n\n"
		"Return operations in execution order. If ambiguous, choose the most probable interpretation and add a short 'reasoning'."
	)

	# Use Responses API with Structured Outputs via Pydantic parsing
	try:
		resp = client.responses.parse(
			model=model,
			input=[
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			text_format=CalendarAgentPlan,
		)
	except TypeError:
		# Backward-compatibility shim for older SDKs that may use a different method name.
		# If parse is not available, fall back to create + manual parsing of output_text.
		raise RuntimeError("Installed openai SDK does not support responses.parse with text_format; please upgrade the SDK.")

	if getattr(resp, "refusal", None):
		# If the model refused, return an empty plan with reasoning.
		return CalendarAgentPlan(model=model, operations=[], reasoning=str(resp.refusal))

	parsed = getattr(resp, "output_parsed", None)
	if parsed is None:
		raise RuntimeError("No parsed output returned from OpenAI Responses API")
	return parsed


# ---------------------------
# Routes
# ---------------------------

@app.get("/")
def health():
	return {"status": "ok", "service": "calendar-agent-arg-planner"}


@app.post("/calendar-agent/get-args", response_model=CalendarAgentPlan)
def get_calendar_args(req: ParseArgsRequest):
	"""
	Accepts a natural language instruction and returns a structured plan
	(a list of Google Calendar operations with validated arguments).
	Uses only the LLM structured parsing path.
	"""
	plan = _llm_plan(req)
	# Trim operations list if needed
	if req.maxOperations and len(plan.operations) > req.maxOperations:
		plan.operations = plan.operations[: req.maxOperations]
	return plan


if __name__ == "__main__":
	# Enable: uvicorn noon-agent.main:app --reload
	import uvicorn

	uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))


