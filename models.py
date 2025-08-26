from datetime import datetime
from typing import Iterable, List, Literal, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from anthropic.types import ToolUnionParam

class PromptRequest(BaseModel):
    chat_id: str
    email: str
    user_prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    model: str = "claude-3-haiku-20240307"
    system_prompt: str = "Act as a senior engineer reviewing code; respond with only concise, actionable feedback in bullet points or brief sentences—no introductions, no fluff."

class PromptResponse(BaseModel):
    response: str
    chat_id: str
    model_used: str
    tokens_generated: int
    input_tokens: int
    message: Optional[str]
    
class GenerateChatTitleInput(BaseModel):
    conversation_summary: str
    keywords: Optional[list[str]] = Field(default_factory=list)
    desired_tone: Optional[Literal["formal", "informal", "informative", "humorous"]] = Field(default="informative",)

GENERATE_CHAT_TITLE_TOOL_SPEC: ToolUnionParam = {
    "name": "generate_chat_title",
    "description": "Generates a concise and relevant title for a chat conversation based on its content.",
    "input_schema": GenerateChatTitleInput.model_json_schema(),
}

class RegistrationRequest(BaseModel):
    name: str | None = None
    email: str
    password: str

class RegistrationResponse(BaseModel):
    id: str
    email: str
    name: str | None = None

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
class ConversationResponse(BaseModel):
    id: str = Field(alias='_id')
    chat_id: str
    email: str
    messages: List[Message] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    title: str | None = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class ConversationRequest(BaseModel):
    chat_id: str
    email: str

class CreateConversationRequest(BaseModel):
    chat_id: str
    email: str
    message: str
    temperature: float = 0.7
    model: str = "claude-3-haiku-20240307"
    system_prompt: str = "Act as a senior engineer reviewing code; respond with only concise, actionable feedback in bullet points or brief sentences—no introductions, no fluff."