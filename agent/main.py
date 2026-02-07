"""Calendar scheduling agent using LangGraph and OpenAI."""

import sys
import os
from pathlib import Path

# Add parent directory to Python path to allow importing agent package
# This is needed when main.py is loaded directly (e.g., by LangChain)
_current_file = Path(__file__).resolve()
_parent_dir = _current_file.parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

import logging
import time
from langgraph.graph import StateGraph, END, START
from typing_extensions import TypedDict
from typing import Literal, Any, List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage

from agent.tools import ALL_TOOLS, INTERNAL_TOOLS, EXTERNAL_TOOLS, set_auth_context
from agent.schemas.agent_response import ErrorResponse
from agent.validation import validate_request
from agent.timing_logger import log_step, log_start
from agent.time_reference import generate_time_reference
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Initialize OpenAI LLM
# ChatOpenAI will automatically read OPENAI_API_KEY from environment
# if not explicitly provided, so we don't need to pass it explicitly
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables - LLM calls may fail")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    model_kwargs={"tool_choice": "required"},  # Force tool usage at model level
)

# Bind all tools to the LLM
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Create a tool lookup dictionary
TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}
INTERNAL_TOOL_NAMES = {tool.name for tool in INTERNAL_TOOLS}
EXTERNAL_TOOL_NAMES = {tool.name for tool in EXTERNAL_TOOLS}

logger.info(f"Tool mapping: {len(TOOL_MAP)} tools total")
logger.info(f"Internal tools: {INTERNAL_TOOL_NAMES}")
logger.info(f"External tools: {EXTERNAL_TOOL_NAMES}")


# ============================================================================
# System Prompt Builder Functions
# ============================================================================

def _build_agent_identity_section() -> str:
    """Agent Identity - WHO/WHAT the agent is and core behavioral requirements"""
    return """
    You are a calendar scheduling agent. Your job is to process user queries about their 
    calendar and use the available tools to respond.
    
    Note: the queries you recieve are trascribed from audio, so they may not be perfect - don't take everything literally."""


def _build_architecture_section(writable_calendars: Optional[List[Dict[str, Any]]] = None) -> str:
    """Agent Architecture - HOW the agent operates internally"""
    base = """
AGENT ARCHITECTURE:
- SINGLE-TURN interaction. Respond with exactly ONE external tool call.
- Cycle: User Query → (Optional Internal Tools) → External Tool → Terminate
- If validation error occurs, retry with corrected information."""

    # If writable calendars are pre-fetched, include them directly
    if writable_calendars:
        # Format calendars for the prompt
        calendar_lines = []
        primary_id = None
        for cal in writable_calendars:
            name = cal.get("name", "Unknown")
            cal_id = cal.get("id", "")
            is_primary = cal.get("is_primary", False)
            if is_primary:
                primary_id = cal_id
                calendar_lines.append(f"  - {name} (PRIMARY): {cal_id}")
            else:
                calendar_lines.append(f"  - {name}: {cal_id}")

        calendars_str = "\n".join(calendar_lines)
        calendar_section = f"""

WRITABLE CALENDARS (pre-fetched, use directly — do NOT call list_calendars):
{calendars_str}

CALENDAR SELECTION (for write operations):
- Use calendar_id values from WRITABLE CALENDARS above.
- Prefer primary calendar when available.
- Use full calendar_id format with @ suffix (never truncate)."""
    else:
        # Fallback: instruct to call list_calendars
        calendar_section = """

CALENDAR SELECTION (for write operations):
- MUST call list_calendars() first for create/update/delete operations.
- Use ONLY calendar_id values from list_calendars() results (not from event reads).
- Prefer primary calendar (is_primary: true).
- Use full calendar_id format with @ suffix (never truncate)."""

    return base + calendar_section


def _build_time_date_handling_section(
    current_datetime: datetime,
    user_timezone: str
) -> str:
    """Time & Date Handling (dynamic)"""
    # Generate time reference (calendar view and relative dates cheat sheet)
    time_reference = generate_time_reference(current_datetime, user_timezone)
    
    return f"""TIME & DATE HANDLING:

It is currently
- Time: {current_datetime.strftime("%H:%M:%S")}
- Date: {current_datetime.strftime("%Y-%m-%d")}
- Timezone: {user_timezone}

To do your job, you may need to choose times to put events, search for events, or display schedules, so it is important to
1. choose the right times for tool inputs
2. format those time inputs properly

CHOOSING THE RIGHT TIME INPUTS:

Here are the values of some relative dates given the current time, date, and timezone:

{time_reference}

FORMATTING TIME INPUTS PROPERLY:
- ALWAYS use timezone-aware ISO strings with offset (e.g., "2026-01-14T00:00:00-08:00") when calling tools with datetime parameters.
- ✅ Correct: "2026-01-14T00:00:00-08:00" (timezone-aware with offset in user's timezone)
- ❌ Wrong: "2026-01-14T00:00:00Z" (UTC, not user timezone)
- ❌ Wrong: "2026-01-14T00:00:00" (no timezone info)"""


def _build_query_patterns_section() -> str:
    """Query Intent Patterns - Consolidated patterns and rules"""
    return """QUERY PATTERNS:

1. VIEW SCHEDULE: show_schedule(start_time, end_time)
   "What's on tomorrow?" → show_schedule(tomorrow 00:00, tomorrow 23:59)
   "Show me this weekend" → show_schedule(Saturday 00:00, Sunday 23:59)

2. FIND EVENT: search_events → show_event
   "When is my haircut?" → search_events("haircut", ...) → show_event(event_id, calendar_id)
   - Extract keywords: "meeting with andrew" → "andrew", "my haircut" → "haircut"
   - Use event_id AND calendar_id from the SAME search result
   - Fallback: use read_schedule if search fails, then find event manually

3. CREATE EVENT: list_calendars → request_create_event
   "Schedule haircut next week" → list_calendars() → request_create_event(summary, calendar_id, times)
   - All-day events: use start_date/end_date (end_date is exclusive, day after event)
   - "Put Lola's birthday Feb 2" → request_create_event(summary, start_date="2026-02-02", end_date="2026-02-03")
   - Only add description if user explicitly requests it

4. UPDATE EVENT: search_events → request_update_event
   "Move haircut to Thursday" → search_events("haircut") → request_update_event(event_id, calendar_id, new_times)
   - Only update fields user mentions

5. DELETE EVENT: search_events → request_delete_event
   "Cancel my haircut" → search_events("haircut") → request_delete_event(event_id, calendar_id)

6. UNSUPPORTED: do_nothing(reason)

CRITICAL RULES:
- Weekend = Saturday-Sunday ONLY
- "next week" = Monday-Friday of following week
- "next Thursday" = Thursday of next week (after this weekend)
- Always use event_id AND calendar_id from same event in results
- For write ops: list_calendars() FIRST, prefer primary calendar
- Use full calendar_id with @ suffix (never truncate)
- On validation error: retry with corrected info"""



def _build_system_prompt(
    current_time: str,
    user_timezone: str,
    writable_calendars: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Assemble complete system prompt from all sections"""
    # Parse ISO string to datetime object
    try:
        current_datetime = datetime.fromisoformat(current_time)
        # Ensure timezone is set
        if current_datetime.tzinfo is None:
            tz = ZoneInfo(user_timezone)
            current_datetime = current_datetime.replace(tzinfo=tz)
        else:
            # Convert to user's timezone
            tz = ZoneInfo(user_timezone)
            current_datetime = current_datetime.astimezone(tz)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to parse current_time '{current_time}': {e}")
        # Fallback: try to create datetime from string parts
        # This should not happen in normal operation, but provides a fallback
        raise ValueError(f"Invalid current_time format: {current_time}") from e

    sections = [
        _build_agent_identity_section(),
        _build_architecture_section(writable_calendars),
        _build_time_date_handling_section(current_datetime, user_timezone),
        _build_query_patterns_section(),  # Combined patterns, examples, and processing rules
    ]

    return "\n\n".join(filter(None, sections))  # Filter out empty sections


# ============================================================================


class State(TypedDict):
    query: str
    auth: dict
    success: bool
    type: Optional[Literal[
        "show-event",
        "show-schedule",
        "create-event",
        "update-event",
        "delete-event",
        "no-action",
    ]]
    metadata: dict[str, Any]
    messages: List[BaseMessage]
    tool_results: Dict[str, Any]
    terminated: bool
    message: Optional[str]  # For error responses
    current_time: Optional[str]  # ISO format datetime string in user's timezone with offset (e.g., "2026-01-13T08:47:00-08:00")
    timezone: Optional[str]  # IANA timezone name (e.g., "America/Los_Angeles")
    current_day_of_week: Optional[str]  # Full day name (e.g., "Monday", "Tuesday")
    _cached_system_prompt: Optional[str]  # Cached system prompt to avoid rebuilding on each iteration
    writable_calendars: Optional[List[Dict[str, Any]]]  # Pre-fetched calendars for write operations


class OutputState(TypedDict):
    success: bool
    type: Optional[Literal[
        "show-event",
        "show-schedule",
        "create-event",
        "update-event",
        "delete-event",
        "no-action",
    ]]
    metadata: Dict[str, Any]
    message: Optional[str]  # For error responses
    query: str  # The transcribed text that was passed to the agent


def agent_node(state: State) -> Dict[str, Any]:
    """
    Main agent node that processes queries with LLM and tool calling.
    """
    node_start_time = time.time()
    query = state.get("query", "")
    messages = state.get("messages", [])
    terminated = state.get("terminated", False)
    
    log_start("agent_node", details=f"query_length={len(query)}")

    # === DEBUG: Log incoming query and iteration ===
    iteration = len([m for m in messages if isinstance(m, HumanMessage) or isinstance(m, ToolMessage)])
    print(f"\n{'#'*60}")
    print(f"🤖 AGENT NODE (iteration {iteration})")
    print(f"   Query: \"{query}\"")
    print(f"{'#'*60}\n")

    # Get time context from state
    current_time = state.get("current_time")
    user_timezone = state.get("timezone")
    current_day_of_week = state.get("current_day_of_week")

    # Validate critical time context information
    if not current_time:
        logger.error("CRITICAL: current_time is missing from state")
        raise ValueError("current_time is required in state but was not provided")
    if not user_timezone:
        logger.error("CRITICAL: timezone is missing from state")
        raise ValueError("timezone is required in state but was not provided")
    if not current_day_of_week:
        logger.error("CRITICAL: current_day_of_week is missing from state")
        raise ValueError("current_day_of_week is required in state but was not provided")

    # Use cached system prompt if available, otherwise build and cache it
    cached_prompt = state.get("_cached_system_prompt")
    if cached_prompt:
        system_instruction = SystemMessage(content=cached_prompt)
    else:
        prompt_start_time = time.time()
        writable_calendars = state.get("writable_calendars")
        prompt_content = _build_system_prompt(current_time, user_timezone, writable_calendars)
        prompt_duration = time.time() - prompt_start_time
        log_step("agent_node.build_system_prompt", prompt_duration)
        system_instruction = SystemMessage(content=prompt_content)
    
    # Initialize messages if empty
    if not messages:
        messages = [system_instruction, HumanMessage(content=query)]
    else:
        # Ensure system message is first if messages already exist
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [system_instruction] + messages
    
    try:
        # Invoke LLM with tools (tool_choice="required" set at model level)
        llm_start_time = time.time()
        response = llm_with_tools.invoke(messages)
        llm_duration = time.time() - llm_start_time
        tool_call_count = len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0
        log_step("agent_node.llm_invoke", llm_duration, details=f"tool_calls={tool_call_count}")
        logger.info(f"LLM response received, tool_calls: {len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0}")
        
        # Add AI message to conversation
        new_messages = messages + [response]
        
        # Check if LLM made tool calls (should always be true with tool_choice="required")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Convert LangChain ToolCall objects to dictionaries
            # LangChain tool_calls are typically objects with .name, .args, .id attributes
            tool_calls_dict = []
            for tool_call in response.tool_calls:
                if isinstance(tool_call, dict):
                    tool_calls_dict.append(tool_call)
                else:
                    # It's a ToolCall object - extract attributes
                    tool_calls_dict.append({
                        "name": getattr(tool_call, "name", ""),
                        "args": getattr(tool_call, "args", {}),
                        "id": getattr(tool_call, "id", ""),
                    })
            
            logger.info(f"Converted {len(tool_calls_dict)} tool calls: {[tc.get('name', 'unknown') for tc in tool_calls_dict]}")
            logger.info(f"Tool calls dict structure: {tool_calls_dict}")
            # === DEBUG: Log each tool call with full arguments ===
            for tc in tool_calls_dict:
                tc_name = tc.get('name', 'unknown')
                tc_args = tc.get('args', {})
                print(f"\n{'='*60}")
                print(f"🔧 AGENT DECISION: call {tc_name}")
                for arg_key, arg_val in tc_args.items():
                    print(f"   {arg_key}: {arg_val}")
                print(f"{'='*60}\n")
            # Return state with tool calls for tool execution node
            # Ensure success is True (or at least not False) so routing works correctly
            node_duration = time.time() - node_start_time
            tool_names = [tc.get('name', 'unknown') for tc in tool_calls_dict]
            log_step("agent_node", node_duration, details=f"tools={tool_names}")
            return {
                "messages": new_messages,
                "success": True,  # Set success to True so should_continue routes to tool_execution
                "tool_results": {
                    "tool_calls": tool_calls_dict,
                },
                "_cached_system_prompt": cached_prompt or system_instruction.content,  # Cache for subsequent iterations
            }
        else:
            # No tool calls - this should not happen with tool_choice="required"
            # Return error instead of no-action
            logger.error("No tool calls detected despite tool_choice='required' - this is an error")
            content = response.content if hasattr(response, 'content') else str(response)
            node_duration = time.time() - node_start_time
            log_step("agent_node", node_duration, details="error=no_tool_calls")
            return {
                "success": False,
                "message": f"Agent failed to call tools. LLM response: {content[:200] if content else 'No response'}",
                "terminated": True,
                "messages": new_messages,
            }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in agent node: {error_msg}", exc_info=True)
        # Return error state that will be picked up by format_response_node
        node_duration = time.time() - node_start_time
        log_step("agent_node", node_duration, details=f"ERROR: {error_msg[:100]}")
        return {
            "success": False,
            "message": f"Agent error: {error_msg}",
            "terminated": True,
            "tool_results": {
                "external_tool_result": None,  # Explicitly set to None to avoid confusion
            },
        }


async def tool_execution_node(state: State) -> Dict[str, Any]:
    """
    Execute tools based on LLM tool calls.
    Distinguishes between internal and external tools.
    """
    node_start_time = time.time()
    try:
        tool_results = state.get("tool_results", {})
        tool_calls = tool_results.get("tool_calls", [])
        messages = state.get("messages", [])
        auth = state.get("auth")  # Get auth from state
        
        log_start("tool_execution_node", details=f"tool_count={len(tool_calls)}")
        
        if not tool_calls:
            logger.warning("No tool calls to execute")
            return {"terminated": True}
        
        # ARCHITECTURAL CONSTRAINT: Only ONE external tool call allowed per turn
        external_tool_calls = [tc for tc in tool_calls if tc.get("name", "") in EXTERNAL_TOOL_NAMES]
        if len(external_tool_calls) > 1:
            error_msg = f"ARCHITECTURE VIOLATION: Multiple external tool calls detected ({len(external_tool_calls)}). Only ONE external tool call is allowed per turn. You called: {[tc.get('name') for tc in external_tool_calls]}. Please call only ONE external tool that matches the user's request."
            logger.error(error_msg)
            # Return error ToolMessages for all external tool calls
            tool_messages = []
            for tc in external_tool_calls:
                tool_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tc.get("id", ""),
                    )
                )
            # Also handle any internal tools that were called
            internal_tool_calls = [tc for tc in tool_calls if tc.get("name", "") not in EXTERNAL_TOOL_NAMES]
            if internal_tool_calls:
                # Execute internal tools first, then return the error
                set_auth_context(auth)
                for tc in internal_tool_calls:
                    tool_name = tc.get("name", "")
                    tool_args = tc.get("args", {})
                    tool_id = tc.get("id", "")
                    if tool_name in TOOL_MAP:
                        try:
                            tool = TOOL_MAP[tool_name]
                            result = tool.invoke(tool_args)
                            tool_messages.append(
                                ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_id,
                                )
                            )
                        except Exception as e:
                            tool_messages.append(
                                ToolMessage(
                                    content=f"Error executing {tool_name}: {str(e)}",
                                    tool_call_id=tool_id,
                                )
                            )
            return {
                "messages": messages + tool_messages,
                "tool_results": {},
                "terminated": False,  # Continue agent loop so it can retry with single external tool
            }
        
        # Set auth context for tools to access
        set_auth_context(auth)
        
        tool_messages = []
        has_external_tool = False
        external_tool_result = None
        
        # Track calendars cache for validation optimization
        calendars_cache = tool_results.get("calendars_cache")

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "")

            logger.info(f"Executing tool: {tool_name} with args: {list(tool_args.keys())}")
            logger.info(f"Tool name in TOOL_MAP: {tool_name in TOOL_MAP}")
            logger.info(f"Tool name in EXTERNAL_TOOL_NAMES: {tool_name in EXTERNAL_TOOL_NAMES}")
            # === DEBUG: Log tool execution with full args ===
            print(f"\n{'='*60}")
            print(f"⚡ EXECUTING: {tool_name}")
            for arg_key, arg_val in tool_args.items():
                print(f"   {arg_key}: {arg_val}")
            print(f"{'='*60}")
            
            if tool_name not in TOOL_MAP:
                logger.error(f"Unknown tool: {tool_name}. Available tools: {list(TOOL_MAP.keys())}")
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: Unknown tool {tool_name}",
                        tool_call_id=tool_id,
                    )
                )
                continue
            
            try:
                # Execute the tool (async tools use ainvoke, sync tools use invoke)
                tool = TOOL_MAP[tool_name]
                tool_start_time = time.time()
                # Check if tool is async (internal tools are async, external tools are sync)
                if tool_name in INTERNAL_TOOL_NAMES:
                    # Async tool - use ainvoke
                    result = await tool.ainvoke(tool_args)
                else:
                    result = tool.invoke(tool_args)
                tool_duration = time.time() - tool_start_time
                log_step(f"tool_execution_node.tool.{tool_name}", tool_duration)
                logger.info(f"Tool {tool_name} executed successfully, result type: {type(result)}")
                
                # === DEBUG: Log tool result ===
                if isinstance(result, list):
                    print(f"   ✅ RESULT: {len(result)} items returned")
                    for i, item in enumerate(result[:5]):  # Show first 5
                        summary = item.get('summary', 'N/A') if isinstance(item, dict) else str(item)[:80]
                        print(f"      [{i}] {summary}")
                    if len(result) > 5:
                        print(f"      ... and {len(result) - 5} more")
                elif isinstance(result, dict):
                    result_type = result.get('type', result.get('summary', 'N/A'))
                    print(f"   ✅ RESULT: {result_type}")
                else:
                    print(f"   ✅ RESULT: {str(result)[:200]}")
                print()

                # Check if this is an external tool
                if tool_name in EXTERNAL_TOOL_NAMES:
                    has_external_tool = True
                    external_tool_result = result
                    logger.info(f"External tool {tool_name} executed, result: {result}")
                    logger.info(f"External tool result type field: {result.get('type', 'MISSING')}")
                    # Add ToolMessage for external tools too - required by OpenAI API
                    # Every tool_call_id must have a ToolMessage response before next LLM call
                    tool_messages.append(
                        ToolMessage(
                            content=f"Tool executed successfully. Result type: {result.get('type', 'unknown')}",
                            tool_call_id=tool_id,
                        )
                    )
                else:
                    # Internal tool - add result to messages
                    tool_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_id,
                        )
                    )
                    logger.info(f"Internal tool {tool_name} executed, result length: {len(str(result))}")

                    # Cache list_calendars result to avoid redundant calls in validation
                    if tool_name == "list_calendars" and isinstance(result, list):
                        calendars_cache = result
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error executing tool {tool_name}: {error_msg}", exc_info=True)
                tool_messages.append(
                    ToolMessage(
                        content=f"Error executing {tool_name}: {error_msg}",
                        tool_call_id=tool_id,
                    )
                )
        
        # Update state
        new_messages = messages + tool_messages
        
        node_duration = time.time() - node_start_time
        if has_external_tool:
            # External tool was called - DON'T terminate yet, let validation_node decide
            # Validation will run before termination
            log_step("tool_execution_node", node_duration, details="external tool executed")
            tool_results_dict = {"external_tool_result": external_tool_result}
            if calendars_cache is not None:
                tool_results_dict["calendars_cache"] = calendars_cache
            return {
                "messages": new_messages,
                "tool_results": tool_results_dict,
                "terminated": False,  # Don't terminate yet - validation will decide
            }
        else:
            # Only internal tools - continue agent loop
            log_step("tool_execution_node", node_duration, details="result=internal_tools_only")
            tool_results_dict = {}
            if calendars_cache is not None:
                tool_results_dict["calendars_cache"] = calendars_cache
            return {
                "messages": new_messages,
                "tool_results": tool_results_dict,
            }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in tool_execution_node: {error_msg}", exc_info=True)
        node_duration = time.time() - node_start_time
        log_step("tool_execution_node", node_duration, details=f"ERROR: {error_msg[:100]}")
        return {
            "success": False,
            "message": f"Tool execution error: {error_msg}",
            "terminated": True,
        }


def validation_node(state: State) -> Dict[str, Any]:
    """
    Validate external tool results before termination.
    
    If validation fails, return error as ToolMessage to agent loop so it can retry.
    If validation passes, proceed to format_response.
    """
    node_start_time = time.time()
    try:
        tool_results = state.get("tool_results", {})
        external_tool_result = tool_results.get("external_tool_result")
        calendars_cache = tool_results.get("calendars_cache")  # Use cached calendars if available
        messages = state.get("messages", [])
        auth = state.get("auth")

        log_start("validation_node")

        # If no external tool result, nothing to validate - proceed
        if not external_tool_result:
            logger.info("No external tool result to validate - proceeding")
            node_duration = time.time() - node_start_time
            log_step("validation_node", node_duration, details="result=no_external_tool")
            return {
                "terminated": True,
            }

        # Extract request type from external tool result
        result_type = external_tool_result.get("type")
        logger.info(f"Validating request type: {result_type}")

        # Validate the request (pass calendars_cache to avoid redundant HTTP calls)
        validate_start_time = time.time()
        validation_error = validate_request(external_tool_result, auth, calendars_cache=calendars_cache)
        validate_duration = time.time() - validate_start_time
        log_step("validation_node.validate_request", validate_duration)
        
        if validation_error:
            # Validation failed - return error to agent loop
            logger.info(f"Validation failed: {validation_error}")
            
            # Convert validation error to ToolMessage
            # We need to find the last AIMessage with tool_calls to attach this error
            # Find all tool_call_ids that need responses
            tool_call_ids_to_replace = []
            for msg in reversed(messages):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Extract tool_call_ids from all tool calls
                    for tool_call in msg.tool_calls:
                        if isinstance(tool_call, dict):
                            tool_call_id = tool_call.get("id", "")
                        else:
                            tool_call_id = getattr(tool_call, "id", "")
                        
                        if tool_call_id:
                            tool_call_ids_to_replace.append(tool_call_id)
                    break  # Only process the last AIMessage with tool_calls
            
            # Filter out existing ToolMessages for these tool_call_ids (from tool_execution_node)
            # and add validation error ToolMessages
            filtered_messages = []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    # Keep ToolMessages that don't match the tool_call_ids we're replacing
                    if msg.tool_call_id not in tool_call_ids_to_replace:
                        filtered_messages.append(msg)
                else:
                    filtered_messages.append(msg)
            
            # Add validation error ToolMessages for each tool_call_id
            validation_tool_messages = []
            if tool_call_ids_to_replace:
                for tool_call_id in tool_call_ids_to_replace:
                    validation_tool_messages.append(
                        ToolMessage(
                            content=validation_error,
                            tool_call_id=tool_call_id,
                        )
                    )
            else:
                # Fallback if we couldn't find tool_call_ids
                validation_tool_messages = [
                    ToolMessage(
                        content=validation_error,
                        tool_call_id="validation-error",
                    )
                ]
            
            # Clear external_tool_result and set terminated to False to continue agent loop
            new_messages = filtered_messages + validation_tool_messages
            node_duration = time.time() - node_start_time
            log_step("validation_node", node_duration, details="FAILED")
            return {
                "messages": new_messages,
                "tool_results": {},  # Clear external_tool_result
                "terminated": False,  # Continue agent loop
            }
        else:
            # Validation passed - proceed to format_response
            # Keep external_tool_result and terminated=True so format_response can use it
            logger.info("Validation passed - proceeding to format_response")
            node_duration = time.time() - node_start_time
            log_step("validation_node", node_duration, details="result=validation_passed")
            return {
                "tool_results": {
                    "external_tool_result": external_tool_result,  # Preserve for format_response
                },
                "terminated": True,  # Proceed to format_response
            }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in validation_node: {error_msg}", exc_info=True)
        # On validation node error, fail safe - proceed to format_response
        # (better to let the request through than block everything)
        node_duration = time.time() - node_start_time
        log_step("validation_node", node_duration, details=f"ERROR: {error_msg[:100]}")
        return {
            "terminated": True,
        }


def format_response_node(state: State) -> Dict[str, Any]:
    """
    Format the final response for the frontend.
    Returns dict with type to match OutputState schema.
    Backend will pass through type to frontend.
    """
    node_start_time = time.time()
    tool_results = state.get("tool_results", {})
    external_tool_result = tool_results.get("external_tool_result")
    terminated = state.get("terminated", False)
    success = state.get("success", True)
    message = state.get("message")
    query = state.get("query", "")
    
    log_start("format_response_node")
    logger.info(f"State keys: {list(state.keys())}")
    logger.info(f"Query from state: {query}")
    logger.info(f"External tool result: {external_tool_result}")
    logger.info(f"Success: {success}, Message: {message}")
    
    # Check if we have an error
    if not success and message:
        logger.info(f"Returning error response: {message}")
        error_response = ErrorResponse(message=message, query=query)
        node_duration = time.time() - node_start_time
        log_step("format_response_node", node_duration, details="result=error")
        return error_response.model_dump()
    
    # Check if we have an external tool result
    # Tools now return properly formatted response dicts via .model_dump()
    # which already include success, type, and metadata fields
    if external_tool_result:
        response_type = external_tool_result.get("type")
        logger.info(f"Formatted response: {response_type}")
        # Add query to the external tool result dict
        external_tool_result["query"] = query
        node_duration = time.time() - node_start_time
        log_step("format_response_node", node_duration, details=f"type: {response_type}")
        return external_tool_result
    
    # Fallback: should not happen if agent is working correctly
    # Return error instead of no-action
    logger.error("No external tool result and no error - this should not happen")
    error_response = ErrorResponse(
        message="Agent failed to produce a valid response. No tool was called to handle the query.",
        query=query
    )
    node_duration = time.time() - node_start_time
    log_step("format_response_node", node_duration, details="result=fallback_error")
    return error_response.model_dump()


def should_continue(state: State) -> str:
    """
    Determine the next node based on state.
    """
    terminated = state.get("terminated", False)
    success = state.get("success", True)
    tool_results = state.get("tool_results", {})
    tool_calls = tool_results.get("tool_calls", [])
    external_tool_result = tool_results.get("external_tool_result")
    messages = state.get("messages", [])
    
    logger.info(f"should_continue: terminated={terminated}, success={success}, tool_calls={len(tool_calls) if tool_calls else 0}, external_result={external_tool_result is not None}")
    
    # Priority 1: If external tool result exists and we haven't validated yet, go to validation
    # Check if we're coming from tool_execution with an external_tool_result
    if external_tool_result and not terminated:
        logger.info("Routing to validation: external_tool_result exists, needs validation")
        return "validation"
    
    # Priority 2: If external tool result exists after validation (terminated=True), format the response
    if external_tool_result and terminated:
        logger.info("Routing to format_response: external_tool_result validated and ready")
        return "format_response"
    
    # Priority 3: If there's an error (success=False and terminated), go to format_response
    if terminated and not success:
        logger.info("Routing to format_response: error state")
        return "format_response"
    
    # Priority 4: If there are tool calls, execute them
    if tool_calls:
        logger.info("Routing to tool_execution: tool calls exist")
        return "tool_execution"
    
    # Priority 5: If terminated (but no error), format response
    if terminated:
        logger.info("Routing to format_response: terminated")
        return "format_response"
    
    # Priority 6: Check if we have ToolMessages from internal tools or validation errors - if so, continue to agent
    # This handles the case where internal tools returned results or validation failed and we need to process them
    from langchain_core.messages import ToolMessage
    has_tool_messages = any(isinstance(msg, ToolMessage) for msg in messages)
    if has_tool_messages and not terminated:
        # Check if the last message is a ToolMessage (indicating we just got results from an internal tool or validation error)
        if messages and isinstance(messages[-1], ToolMessage):
            logger.info("Routing to agent: ToolMessage from internal tool or validation error needs processing")
            return "agent"
    
    # Default to format_response (shouldn't happen)
    logger.warning("Routing to format_response: default fallback")
    return "format_response"


# Build the LangGraph
logger.info("Building LangGraph for calendar scheduling agent")

graph_builder = StateGraph(State, output_schema=OutputState)

# Add nodes
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tool_execution", tool_execution_node)
graph_builder.add_node("validation", validation_node)
graph_builder.add_node("format_response", format_response_node)

# Set entry point
graph_builder.set_entry_point("agent")

# Add conditional edges
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tool_execution": "tool_execution",
        "format_response": "format_response",
    },
)

graph_builder.add_conditional_edges(
    "tool_execution",
    should_continue,
    {
        "validation": "validation",  # New validation step for external tools
        "agent": "agent",
        "format_response": "format_response",
    },
)

graph_builder.add_conditional_edges(
    "validation",
    should_continue,
    {
        "agent": "agent",  # Validation failed, retry
        "format_response": "format_response",  # Validation passed
    },
)

# Format response always goes to END
graph_builder.add_edge("format_response", END)

# Compile the graph
graph = graph_builder.compile()

# Export as noon_graph (required by langgraph.json)
noon_graph = graph

logger.info("LangGraph compilation complete")
