from typing import List, Optional
from pydantic import BaseModel, Field

# Definición de esquemas de datos (Pydantic Models) para peticiones y respuestas

class Message(BaseModel):
    role: str = Field(..., description="El rol del emisor del mensaje (por ejemplo, 'user', 'assistant')")
    content: str = Field(..., description="El contenido del mensaje")

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = Field(None, description="El modelo de IA solicitado (por ejemplo, 'llama3.2:3b')")
    messages: Optional[List[Message]] = Field(None, description="La lista de mensajes de la conversación")
    prompt: Optional[str] = Field(None, description="El prompt directo (alternativa compatible)")

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: ChatCompletionResponseUsage
