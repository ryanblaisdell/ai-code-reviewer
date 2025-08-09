from pydantic import BaseModel

class PromptRequest(BaseModel):
    user_prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    model: str = "claude-3-haiku-20240307"
    system_prompt: str = "Act as a senior engineer reviewing code; respond with only concise, actionable feedback in bullet points or brief sentences—no introductions, no fluff."

class PromptResponse(BaseModel):
    response: str
    model_used: str
    tokens_generated: int
    input_tokens: int

class RegistrationRequest(BaseModel):
    name: str | None = None
    email: str
    password: str

class RegistrationResponse(BaseModel):
    id: str
    email: str
    name: str | None = None