from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatPost(BaseModel):
    conversation_id: str
    user_id: str
    role: str
    message: str
    msg_summary: str

class ChatQuery(BaseModel):
    conversation_id: str
    page_number: int
    
class ChatMessageModel(BaseModel):
    message_id: str
    conversation_id: str
    user_id: str
    role: str
    message: str
    msg_summary: str
    created_at: datetime
    updated_at: datetime
    
class ConversationModel(BaseModel):
    id: str
    user_id: str
    subject: str
    created_at: datetime
    updated_at: datetime

class MetadataModel(BaseModel):
    total: Optional[int] = Field(None, description="Total number of entries")
    page_number: int
    total_pages: int
    page_size: int

class AllConversationsResponseModel(BaseModel):
    conversations: List[ConversationModel]
    metadata: MetadataModel
    
class MessageModel(BaseModel):
    id: str
    content: str
    role: str
    timestamp: datetime

class MessagesResponseModel(BaseModel):
    messages: List[MessageModel]
    metadata: MetadataModel
    
class MonthlyBilling(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format")
    total_input_tokens: int = Field(0, description="Total input tokens for the month")
    total_output_tokens: int = Field(0, description="Total output tokens for the month")
    billing_amount: float = Field(0.0, description="Total billing amount for the month")
    

class FeedbacksResponseModel(BaseModel):
    feedbacks: List[Dict[str, Any]]
    metadata: MetadataModel
    
class TitleChangeRequest(BaseModel):    
    title: str