"""Agent endpoint for invoking the LangGraph calendar agent."""

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from langgraph_sdk import get_client

from schemas.user import AuthenticatedUser
from schemas.agent_response import AgentResponse, ErrorResponse
from schemas.confirm_action import ConfirmActionRequest
from core.dependencies import get_current_user
from core.config import get_settings
from domains.transcription.service import TranscriptionService
from services import agent_calendar_service
from db.session import get_service_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

# Initialize transcription service
transcription_service = TranscriptionService()


@router.post("/action")
async def agent_action(
    request: Request,
    file: UploadFile = File(..., description="Audio file to transcribe and process"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Invoke the LangGraph calendar agent with an audio file.

    The audio file is first transcribed using Deepgram, then the transcribed text
    is passed to the agent which will classify intent and extract metadata for calendar operations.
    """
    try:
        # Extract Supabase access token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authentication token",
            )
        supabase_access_token = auth_header.replace("Bearer ", "", 1)

        # Prepare auth data with Supabase token
        auth = {
            "user_id": current_user.id,
            "supabase_access_token": supabase_access_token,
        }

        # Validate file
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Transcribe audio file
        try:
            # Reset file pointer to beginning in case it was read already
            await file.seek(0)
            transcribed_text = await transcription_service.transcribe(
                file=file.file, filename=file.filename, mime_type=file.content_type
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Transcription error: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Transcription failed user_id={current_user.id} file={file.filename}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to transcribe audio: {str(e)}"
            )

        if not transcribed_text or not transcribed_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Transcription resulted in empty text. Please ensure the audio file contains speech.",
            )

        # Create LangGraph SDK client and invoke agent
        settings = get_settings()

        parsed_url = urlparse(settings.langgraph_agent_url)
        is_local_agent = parsed_url.hostname in {"localhost", "127.0.0.1"}

        api_key = settings.langsmith_api_key or settings.langgraph_api_key

        if api_key is None and not is_local_agent:
            logger.error(
                f"LangGraph agent API key is missing for remote agent URL user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=500,
                detail="Agent service is not configured with LangSmith authentication credentials."
            )

        client = get_client(
            url=settings.langgraph_agent_url,
            api_key=api_key,
        )

        # Get user timezone from users table
        supabase_client = get_service_client()
        user_timezone = None
        try:
            user_result = (
                supabase_client.table("users")
                .select("timezone")
                .eq("id", current_user.id)
                .single()
                .execute()
            )
            
            if user_result.data:
                user_timezone = user_result.data.get("timezone")
            else:
                logger.error(f"No user data returned user_id={current_user.id}")
                
        except Exception as e:
            logger.error(
                f"Failed to get user timezone user_id={current_user.id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve user timezone: {str(e)}"
            )
        
        # Validate timezone is set and not default 'UTC'
        if not user_timezone or user_timezone.strip() == "":
            logger.error(f"User timezone not configured user_id={current_user.id}")
            raise HTTPException(
                status_code=400,
                detail="User timezone is not configured. Please set your timezone in your account settings."
            )
        
        if user_timezone.upper() == "UTC":
            raise HTTPException(
                status_code=400,
                detail="User timezone is not configured. Please set your timezone in your account settings."
            )
        
        # Validate timezone is a valid IANA timezone
        current_utc = datetime.now(timezone.utc)
        try:
            user_tz = ZoneInfo(user_timezone)
            current_user_time = current_utc.astimezone(user_tz)
            current_time_str = current_user_time.isoformat()
        except Exception as e:
            logger.error(
                f"Invalid timezone user_id={current_user.id} timezone={user_timezone}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timezone configuration: {user_timezone}. Please set a valid timezone in your account settings."
            )

        input_state = {
            "query": transcribed_text,
            "auth": auth,
            "success": False,
            "type": None,
            "metadata": {},
            "messages": [],
            "tool_results": {},
            "terminated": False,
            "current_time": current_time_str,
            "timezone": user_timezone,
        }

        logger.info(
            f"Invoking agent user_id={current_user.id} query_length={len(transcribed_text)}"
        )

        # Invoke and wait for completion
        result = await client.runs.wait(
            thread_id=None,
            assistant_id="agent",
            input=input_state,
        )

        logger.info(
            f"Agent completed user_id={current_user.id} "
            f"type={result.get('type')} success={result.get('success')}"
        )

        # Pass through agent response directly
        # Ensure success is always a boolean for Swift decoder
        result_success = bool(result.get("success", False))
        
        if "message" in result:
            # Error response - ensure success is False
            return {
                "success": False,  # Always False for error responses
                "message": result.get("message", "Unknown error"),
            }
        elif "type" in result:
            # Success response - pass through as-is, ensure success is True
            return {
                "success": True,  # Always True for success responses
                "type": result.get("type"),
                "metadata": result.get("metadata", {}),
            }
        else:
            # Fallback for unexpected responses - treat as error
            logger.warning(
                f"Unexpected result format user_id={current_user.id} "
                f"keys={list(result.keys())}"
            )
            return {
                "success": False,
                "message": f"Unexpected response format from agent: {list(result.keys())}",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Agent invocation failed user_id={current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invoke agent: {str(e)}"
        )


@router.post("/confirm-action", response_model=AgentResponse)
async def confirm_action(
    payload: ConfirmActionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Confirm and execute a calendar action based on the agent's request.
    
    Handles write operations that require confirmation:
    - create-event: Create a new event
    - update-event: Update an existing event
    - delete-event: Delete an event
    """
    try:
        result = await agent_calendar_service.confirm_calendar_action(
            user_id=current_user.id,
            payload=payload,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to confirm action user_id={current_user.id}: {e}",
            exc_info=True,
        )
        return ErrorResponse(
            success="false",
            message=f"Failed to confirm action: {str(e)}"
        )
