from typing import Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None
