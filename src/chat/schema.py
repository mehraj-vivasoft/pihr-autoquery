from pydantic import BaseModel

from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    is_new: bool = False
    conversation_id: str
    user_id: str
    
class ReplyModel(BaseModel):
    id: str
    content: str
    timestamp: datetime

class NewConversationModel(BaseModel):
    conversation_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    subject: str
    reply: ReplyModel
    is_new: bool


class MessageModel(BaseModel):
    message_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    is_new: bool