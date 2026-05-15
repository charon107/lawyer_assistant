"""AI Agent WebSocket routes with streaming support (PydanticAI)."""

import json
import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic_ai import (
    Agent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.messages import (
    BinaryContent,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)

from app.agents.assistant import Deps, get_agent
from app.agents.prompts import DEFAULT_SYSTEM_PROMPT
from app.api.deps import CurrentUser, get_conversation_service, get_current_user_ws
from app.core.config import settings
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    ToolCallComplete,
    ToolCallCreate,
)
from app.services.agent import AgentConnectionManager
from app.services.file_storage import get_file_storage

if TYPE_CHECKING:
    from app.schemas.document_analysis import DocumentAnalysisResult

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/agent/models")
async def list_models(user: CurrentUser) -> dict[str, Any]:
    """Return available LLM models grouped by provider.

    If user has configured providers, fetch models from each.
    Otherwise return global defaults with configured=false.
    """
    configs = user.llm_configs
    if not configs:
        return {
            "provider": settings.LLM_PROVIDER,
            "default": settings.AI_MODEL,
            "models": settings.AI_AVAILABLE_MODELS,
            "base_url": settings.LLM_BASE_URL or None,
            "configured": False,
        }

    # Aggregate models from all configured providers
    providers = []
    all_models = []
    for cfg in configs:
        models = _fetch_provider_models(cfg.provider, cfg.api_key, cfg.base_url)
        provider_entry = {
            "id": cfg.id,
            "provider": cfg.provider,
            "model": cfg.model,
            "models": models,
        }
        providers.append(provider_entry)
        for m in models:
            all_models.append({"provider": cfg.provider, "model": m, "config_id": cfg.id})

    # Default: first config's selected model, or first available
    first = configs[0]
    default_model = first.model or settings.AI_MODEL

    return {
        "provider": first.provider,
        "default": default_model,
        "providers": providers,
        "models": [m["model"] for m in all_models],
        "configured": True,
    }


def _fetch_provider_models(provider: str, api_key: str, base_url: str | None) -> list[str]:
    """Fetch available models from a provider's API."""
    # Anthropic: hardcoded list
    if provider == "anthropic":
        return ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]

    # Google AI Studio
    if provider == "google":
        try:
            url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip(
                "/"
            ) + "/models"
            resp = httpx.get(url, params={"key": api_key}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return sorted([m["name"].split("/")[-1] for m in data.get("models", [])])
        except Exception as e:
            logger.warning("Failed to fetch Google models: %s", e)
        return []

    # OpenAI-compatible
    try:
        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
        resp = httpx.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return sorted([m["id"] for m in data.get("data", [])])
    except Exception as e:
        logger.warning("Failed to fetch models: %s", e)
    return []


manager = AgentConnectionManager()

# User-friendly status labels for tool calls (ChatGPT-style)
TOOL_STATUS_LABELS: dict[str, str] = {
    "current_datetime": "获取当前时间",
    "search_law": "检索法律知识库",
    "get_law_article": "查询法律条文",
    "get_domain_expertise": "加载专业分析方法",
}


def _build_case_system_prompt(case_id: str, user_id: str) -> str | None:
    """Build a system prompt that includes case context.

    Returns the augmented system prompt, or None if case loading fails
    (silent degradation — chat works without case context).
    """
    try:
        from contextlib import contextmanager

        from app.services.lpa_case_service import LPACaseService

        with contextmanager(get_db_session)() as db:
            service = LPACaseService(db)
            try:
                case = service.get_without_docs(case_id, user_id=user_id)
            except Exception:
                return None

            documents = service.get_documents(case_id, user_id=user_id)
            analyses = service.get_analyses_by_case(case_id, user_id=user_id)

            doc_sections = []
            for doc in documents:
                section = f"- {doc.filename}"
                if doc.summary:
                    section += f"\n  摘要：{doc.summary}"
                if doc.parsed_content:
                    truncated = doc.parsed_content[:8000]
                    section += f"\n  内容：\n{truncated}"
                # Inject analysis if available
                if doc.id in analyses:
                    analysis_record = analyses[doc.id]
                    if analysis_record.status == "completed" and analysis_record.analysis_json:
                        try:
                            from app.schemas.document_analysis import DocumentAnalysisResult

                            analysis = DocumentAnalysisResult.model_validate_json(
                                analysis_record.analysis_json
                            )
                            section += (
                                f"\n  法律关系分析：\n{_format_analysis_for_prompt(analysis)}"
                            )
                        except Exception:
                            pass  # Graceful degradation
                doc_sections.append(section)

            docs_text = "\n".join(doc_sections) if doc_sections else "暂无材料"

            return f"""{DEFAULT_SYSTEM_PROMPT}

当前案件：{case.name}
案件描述：{case.description or "无"}

相关材料：
{docs_text}

请基于以上案件材料回答用户的问题。引用具体条款时请标明出处。"""
    except Exception as e:
        logger.warning(f"Failed to build case context for case {case_id}: {e}")
        return None


def _format_analysis_for_prompt(analysis: "DocumentAnalysisResult") -> str:
    """Format structured analysis as a readable text block for the system prompt."""
    parts = []
    if analysis.parties:
        parties_str = "、".join(f"{p.name}({p.role})" for p in analysis.parties)
        parts.append(f"  当事方：{parties_str}")
    parts.append(f"  文件类型：{analysis.contract_type}")
    if analysis.legal_relationships:
        rels = "; ".join(
            f"{r.relationship_type}（{'、'.join(r.parties)}）" for r in analysis.legal_relationships
        )
        parts.append(f"  法律关系：{rels}")
    if analysis.key_terms:
        terms = "; ".join(f"{t.term}: {t.content[:50]}" for t in analysis.key_terms[:5])
        parts.append(f"  关键条款：{terms}")
    if analysis.applicable_laws:
        parts.append(f"  适用法律：{'、'.join(analysis.applicable_laws)}")
    if analysis.risk_points:
        risks = "; ".join(f"[{r.level}] {r.description[:50]}" for r in analysis.risk_points[:3])
        parts.append(f"  风险点：{risks}")
    if analysis.dispute_focal_points:
        parts.append(f"  争议焦点：{'、'.join(analysis.dispute_focal_points[:3])}")
    if analysis.summary:
        parts.append(f"  分析摘要：{analysis.summary[:200]}")
    return "\n".join(parts)


def build_message_history(history: list[dict[str, str]]) -> list[ModelRequest | ModelResponse]:
    """Convert conversation history to PydanticAI message format."""
    model_history: list[ModelRequest | ModelResponse] = []

    for msg in history:
        if msg["role"] == "user":
            model_history.append(ModelRequest(parts=[UserPromptPart(content=msg["content"])]))
        elif msg["role"] == "assistant":
            model_history.append(ModelResponse(parts=[TextPart(content=msg["content"])]))
        elif msg["role"] == "system":
            model_history.append(ModelRequest(parts=[SystemPromptPart(content=msg["content"])]))

    return model_history


@router.websocket("/ws/agent")
async def agent_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_ws),
) -> None:
    """WebSocket endpoint for AI agent with full event streaming.

    Uses PydanticAI iter() to stream all agent events including:
    - user_prompt: When user input is received
    - model_request_start: When model request begins
    - text_delta: Streaming text from the model
    - tool_call_delta: Streaming tool call arguments
    - tool_call: When a tool is called (with full args)
    - tool_result: When a tool returns a result
    - final_result: When the final result is ready
    - complete: When processing is complete
    - error: When an error occurs

    Expected input message format:
    {
        "message": "user message here",
        "history": [{"role": "user|assistant|system", "content": "..."}],
        "conversation_id": "optional-uuid-to-continue-existing-conversation"
    }

    Authentication: Requires a valid JWT token passed as a query parameter or header.

    Persistence: Set 'conversation_id' to continue an existing conversation.
    If not provided, a new conversation is created. The conversation_id is
    returned in the 'conversation_created' event.
    """
    # JWT auth is handled by get_current_user_ws dependency
    # If auth failed, WebSocket was already closed and user is None
    if user is None:
        return

    await manager.connect(websocket)

    # Conversation state per connection
    conversation_history: list[dict[str, str]] = []
    deps = Deps()
    current_conversation_id: str | None = None
    current_case_id: str | None = None

    try:
        while True:
            # Receive user message
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            file_ids = data.get("file_ids", [])
            case_id = data.get("case_id")
            if case_id:
                current_case_id = case_id

            if not user_message and not file_ids:
                await manager.send_event(websocket, "error", {"message": "Empty message"})
                continue

            # Handle conversation persistence
            try:
                with contextmanager(get_db_session)() as db:
                    conv_service = get_conversation_service(db)

                    # Get or create conversation
                    requested_conv_id = data.get("conversation_id")
                    if requested_conv_id:
                        current_conversation_id = requested_conv_id
                        conv = conv_service.get_conversation(
                            requested_conv_id, user_id=str(user.id)
                        )
                        if not conv.title and user_message:
                            title = user_message[:50] if len(user_message) > 50 else user_message
                            conv_service.update_conversation(
                                requested_conv_id,
                                ConversationUpdate(title=title),
                                user_id=str(user.id),
                            )
                    elif not current_conversation_id:
                        # Create new conversation
                        conv_data = ConversationCreate(
                            user_id=str(user.id),
                            title=user_message[:50] if len(user_message) > 50 else user_message,
                            case_id=current_case_id,
                        )
                        conversation = conv_service.create_conversation(conv_data)
                        current_conversation_id = str(conversation.id)
                        await manager.send_event(
                            websocket,
                            "conversation_created",
                            {"conversation_id": current_conversation_id},
                        )

                    # Save user message
                    user_msg = conv_service.add_message(
                        current_conversation_id,
                        MessageCreate(role="user", content=user_message),
                    )
                    # Link uploaded files to this message
                    if file_ids:
                        try:
                            conv_service.link_files_to_message(user_msg.id, file_ids)
                        except Exception as e:
                            logger.warning(f"Failed to link files: {e}")
            except Exception as e:
                logger.warning(f"Failed to persist conversation: {e}")
                # Continue without persistence

            await manager.send_event(websocket, "user_prompt", {"content": user_message})

            try:
                selected_model = data.get("model")

                # Resolve per-user LLM config from user's configured providers
                user_provider = None
                user_base_url = None
                user_api_key = None
                if user.llm_configs:
                    # Use first config as default, or find config matching selected model
                    cfg = user.llm_configs[0]
                    for c in user.llm_configs:
                        if selected_model and c.model == selected_model:
                            cfg = c
                            break
                    user_provider = cfg.provider
                    user_base_url = cfg.base_url or None
                    user_api_key = cfg.api_key or None
                    if not selected_model:
                        selected_model = cfg.model

                # Build system prompt with case context if applicable
                system_prompt = None
                if current_case_id:
                    system_prompt = _build_case_system_prompt(current_case_id, str(user.id))

                assistant = get_agent(
                    model_name=selected_model,
                    provider=user_provider,
                    api_key=user_api_key,
                    base_url=user_base_url,
                    system_prompt=system_prompt,
                )
                model_history = build_message_history(conversation_history)

                # Collect tool calls during streaming for persistence
                collected_tool_calls: list[dict[str, Any]] = []
                # Load attached files and build multimodal input
                user_input: str | list[Any] = user_message
                file_context_parts: list[str] = []

                if file_ids:
                    storage = get_file_storage()
                    image_parts = []
                    with contextmanager(get_db_session)() as file_db:
                        attached_files = get_conversation_service(file_db).list_attached_files(
                            file_ids
                        )
                        for chat_file in attached_files:
                            try:
                                if chat_file.file_type == "image":
                                    file_data = await storage.load(chat_file.storage_path)
                                    image_parts.append(
                                        BinaryContent(
                                            data=file_data, media_type=chat_file.mime_type
                                        )
                                    )
                                elif chat_file.parsed_content:
                                    file_context_parts.append(
                                        f"\n---\nAttached file: {chat_file.filename}\n```\n{chat_file.parsed_content}\n```"
                                    )
                            except Exception as e:
                                logger.warning(f"Failed to load file {chat_file.id}: {e}")

                    if image_parts:
                        full_text = user_message + "".join(file_context_parts)
                        user_input = [full_text, *image_parts]
                    elif file_context_parts:
                        user_input = user_message + "".join(file_context_parts)

                # Use iter() on the underlying PydanticAI agent to stream all events
                async with assistant.agent.iter(
                    user_input,
                    deps=deps,
                    message_history=model_history,
                ) as agent_run:
                    async for node in agent_run:
                        if Agent.is_user_prompt_node(node):
                            prompt_text = (
                                node.user_prompt
                                if isinstance(node.user_prompt, str)
                                else user_message
                            )
                            await manager.send_event(
                                websocket,
                                "user_prompt_processed",
                                {"prompt": prompt_text},
                            )

                        elif Agent.is_model_request_node(node):
                            await manager.send_event(websocket, "model_request_start", {})

                            async with node.stream(agent_run.ctx) as request_stream:
                                async for event in request_stream:
                                    if isinstance(event, PartStartEvent):
                                        await manager.send_event(
                                            websocket,
                                            "part_start",
                                            {
                                                "index": event.index,
                                                "part_type": type(event.part).__name__,
                                            },
                                        )
                                        # Send initial content from TextPart if present
                                        if isinstance(event.part, TextPart) and event.part.content:
                                            await manager.send_event(
                                                websocket,
                                                "text_delta",
                                                {
                                                    "index": event.index,
                                                    "content": event.part.content,
                                                },
                                            )

                                    elif isinstance(event, PartDeltaEvent):
                                        if isinstance(event.delta, TextPartDelta):
                                            await manager.send_event(
                                                websocket,
                                                "text_delta",
                                                {
                                                    "index": event.index,
                                                    "content": event.delta.content_delta,
                                                },
                                            )
                                        elif isinstance(event.delta, ToolCallPartDelta):
                                            await manager.send_event(
                                                websocket,
                                                "tool_call_delta",
                                                {
                                                    "index": event.index,
                                                    "args_delta": event.delta.args_delta,
                                                },
                                            )

                                    elif isinstance(event, FinalResultEvent):
                                        await manager.send_event(
                                            websocket,
                                            "final_result_start",
                                            {"tool_name": event.tool_name},
                                        )

                        elif Agent.is_call_tools_node(node):
                            await manager.send_event(websocket, "call_tools_start", {})

                            async with node.stream(agent_run.ctx) as handle_stream:
                                async for tool_event in handle_stream:
                                    if isinstance(tool_event, FunctionToolCallEvent):
                                        collected_tool_calls.append(
                                            {
                                                "tool_call_id": tool_event.part.tool_call_id,
                                                "tool_name": tool_event.part.tool_name,
                                                "args": tool_event.part.args,
                                            }
                                        )
                                        # Send user-friendly status before raw tool_call
                                        status_label = TOOL_STATUS_LABELS.get(
                                            tool_event.part.tool_name, "正在处理"
                                        )
                                        await manager.send_event(
                                            websocket,
                                            "tool_status",
                                            {
                                                "tool_name": tool_event.part.tool_name,
                                                "label": status_label,
                                            },
                                        )
                                        await manager.send_event(
                                            websocket,
                                            "tool_call",
                                            {
                                                "tool_name": tool_event.part.tool_name,
                                                "args": tool_event.part.args,
                                                "tool_call_id": tool_event.part.tool_call_id,
                                            },
                                        )

                                    elif isinstance(tool_event, FunctionToolResultEvent):
                                        for tc in collected_tool_calls:
                                            if tc["tool_call_id"] == tool_event.tool_call_id:
                                                tc["result"] = str(tool_event.result.content)
                                                break
                                        await manager.send_event(
                                            websocket,
                                            "tool_result",
                                            {
                                                "tool_call_id": tool_event.tool_call_id,
                                                "content": str(tool_event.result.content),
                                            },
                                        )

                        elif Agent.is_end_node(node) and agent_run.result is not None:
                            await manager.send_event(
                                websocket,
                                "final_result",
                                {"output": agent_run.result.output},
                            )

                # Update conversation history
                conversation_history.append({"role": "user", "content": user_message})
                if agent_run.result:
                    conversation_history.append(
                        {"role": "assistant", "content": agent_run.result.output}
                    )

                # Save assistant response to database
                if current_conversation_id and agent_run.result:
                    try:
                        with contextmanager(get_db_session)() as db:
                            conv_service = get_conversation_service(db)
                            assistant_msg = conv_service.add_message(
                                current_conversation_id,
                                MessageCreate(
                                    role="assistant",
                                    content=agent_run.result.output,
                                    model_name=assistant.model_name
                                    if hasattr(assistant, "model_name")
                                    else None,
                                ),
                            )
                            assistant_msg_id = str(assistant_msg.id)
                            # Save tool calls
                            for tc in collected_tool_calls:
                                try:
                                    args_dict = tc.get("args", {})
                                    if isinstance(args_dict, str):
                                        args_dict = (
                                            json.loads(args_dict) if args_dict.strip() else {}
                                        )
                                    if args_dict is None:
                                        args_dict = {}
                                    tc_obj = conv_service.start_tool_call(
                                        assistant_msg.id,
                                        ToolCallCreate(
                                            tool_call_id=tc["tool_call_id"],
                                            tool_name=tc["tool_name"],
                                            args=args_dict,
                                            started_at=datetime.now(UTC),
                                        ),
                                    )
                                    if tc.get("result"):
                                        conv_service.complete_tool_call(
                                            tc_obj.id,
                                            ToolCallComplete(
                                                result=tc["result"],
                                                completed_at=datetime.now(UTC),
                                                success=True,
                                            ),
                                        )
                                except Exception as e:
                                    logger.warning(f"Failed to persist tool call: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to persist assistant response: {e}")

                # Notify frontend that assistant message was saved with real database ID
                if assistant_msg_id:
                    await manager.send_event(
                        websocket,
                        "message_saved",
                        {
                            "message_id": assistant_msg_id,
                            "conversation_id": current_conversation_id,
                        },
                    )

                await manager.send_event(
                    websocket,
                    "complete",
                    {
                        "conversation_id": current_conversation_id,
                    },
                )

            except WebSocketDisconnect:
                # Client disconnected during processing - this is normal
                logger.info("Client disconnected during agent processing")
                break
            except Exception as e:
                logger.exception(f"Error processing agent request: {e}")
                # Try to send error, but don't fail if connection is closed
                await manager.send_event(websocket, "error", {"message": str(e)})

    except WebSocketDisconnect:
        pass  # Normal disconnect
    finally:
        manager.disconnect(websocket)
