from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
import asyncio

# 现有的导入
from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIResponse
from .loop import sampling_loop, APIProvider, PROVIDER_TO_DEFAULT_MODEL_NAME
from .tools import ToolResult
from anthropic.types.beta import (
    BetaContentBlock,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

class StepType(str, Enum):
    MODEL_CALL = "model_call"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    ERROR = "error"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ConversationStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: StepType
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    details: Dict[str, Any] = {}
    error: Optional[str] = None

class ConversationSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    steps: List[ConversationStep] = []
    messages: List[BetaMessageParam] = []
    status: StepStatus = StepStatus.PENDING

class ConversationRequest(BaseModel):
    messages: List[BetaMessageParam]
    system_prompt_suffix: Optional[str] = ""
    provider: APIProvider = APIProvider.ANTHROPIC
    model: Optional[str] = None
    api_key: str
    only_n_most_recent_images: Optional[int] = None
    max_tokens: int = 4096

class ConversationResponse(BaseModel):
    session_id: UUID
    status: StepStatus
    messages: List[BetaMessageParam]

# 存储活动会话
sessions: Dict[UUID, ConversationSession] = {}

app = FastAPI(
    title="计算机使用控制 API",
    description="带有详细步骤追踪的计算机控制 API",
    version="1.0.0"
)

class EnhancedCallbackStore:
    def __init__(self, session_id: UUID):
        self.session_id = session_id
        self.current_step: Optional[ConversationStep] = None
        
    def _add_step(self, step_type: StepType, details: Dict[str, Any] = {}) -> ConversationStep:
        step = ConversationStep(
            type=step_type,
            status=StepStatus.RUNNING,
            start_time=datetime.now(),
            details=details
        )
        sessions[self.session_id].steps.append(step)
        self.current_step = step
        return step
        
    def _complete_step(self, error: Optional[str] = None):
        if self.current_step:
            self.current_step.end_time = datetime.now()
            self.current_step.status = StepStatus.FAILED if error else StepStatus.COMPLETED
            if error:
                self.current_step.error = error
            self.current_step = None
            
    async def content_callback(self, block: BetaContentBlock):
        step = self._add_step(StepType.MODEL_CALL, {
            "content_type": block.type,
            "content": block.dict()
        })
        self._complete_step()
        
    async def tool_callback(self, result: ToolResult, tool_id: str):
        step = self._add_step(StepType.TOOL_USE, {
            "tool_id": tool_id,
            "result": {
                "output": result.output,
                "error": result.error,
                "has_image": bool(result.base64_image)
            }
        })
        self._complete_step(result.error)
        
    async def api_callback(self, response: APIResponse[BetaMessage]):
        step = self._add_step(StepType.TOOL_RESULT, {
            "status_code": response.http_response.status_code,
            "headers": dict(response.headers)
        })
        self._complete_step()

@app.post("/conversation", response_model=ConversationResponse)
async def create_conversation(request: ConversationRequest):
    """创建新的对话会话"""
    try:
        session_id = uuid4()
        session = ConversationSession(id=session_id, messages=request.messages)
        sessions[session_id] = session
        
        if not request.model:
            request.model = PROVIDER_TO_DEFAULT_MODEL_NAME[request.provider]
        
        callbacks = EnhancedCallbackStore(session_id)
        
        # 运行采样循环
        messages = await sampling_loop(
            model=request.model,
            provider=request.provider,
            system_prompt_suffix=request.system_prompt_suffix,
            messages=request.messages,
            output_callback=callbacks.content_callback,
            tool_output_callback=callbacks.tool_callback,
            api_response_callback=callbacks.api_callback,
            api_key=request.api_key,
            only_n_most_recent_images=request.only_n_most_recent_images,
            max_tokens=request.max_tokens
        )
        
        session.messages = messages
        session.status = StepStatus.COMPLETED
        session.updated_at = datetime.now()
        
        return ConversationResponse(
            session_id=session_id,
            status=session.status,
            messages=messages
        )
        
    except Exception as e:
        if session_id in sessions:
            sessions[session_id].status = StepStatus.FAILED
            error_step = ConversationStep(
                type=StepType.ERROR,
                status=StepStatus.FAILED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error=str(e)
            )
            sessions[session_id].steps.append(error_step)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}", response_model=ConversationSession)
async def get_conversation(session_id: UUID):
    """获取会话的详细信息"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话未找到")
    return sessions[session_id]

@app.get("/conversation/{session_id}/steps")
async def get_conversation_steps(
    session_id: UUID,
    step_type: Optional[StepType] = None,
    status: Optional[StepStatus] = None
):
    """获取会话的步骤详情,支持按类型和状态筛选"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话未找到")
        
    steps = sessions[session_id].steps
    
    if step_type:
        steps = [step for step in steps if step.type == step_type]
    if status:
        steps = [step for step in steps if step.status == status]
        
    return steps

@app.get("/conversation/{session_id}/summary")
async def get_conversation_summary(session_id: UUID):
    """获取会话的统计摘要"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话未找到")
        
    session = sessions[session_id]
    
    # 计算统计信息
    step_counts = {step_type: 0 for step_type in StepType}
    status_counts = {status: 0 for status in StepStatus}
    total_duration = datetime.now() - session.created_at
    
    for step in session.steps:
        step_counts[step.type] += 1
        status_counts[step.status] += 1
    
    return {
        "session_id": session_id,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "total_duration": str(total_duration),
        "total_steps": len(session.steps),
        "step_type_counts": step_counts,
        "status_counts": status_counts,
        "messages_count": len(session.messages)
    }

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)