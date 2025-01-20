from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.db.schemas import ChatMessageModel, AllConversationsResponseModel, MessagesResponseModel, MonthlyBilling

class DBInterface(ABC):
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def create_conversation(self, conversation_id: str, subject: str, user_id: str) -> None:
        """Create a new conversation in the database"""
        pass
    
    @abstractmethod
    async def post_chat(self, conversation_id: str, user_id: str, role: str, message: str, msg_summary: str) -> ChatMessageModel:
        """Post a chat message to the database"""
        pass
    
    @abstractmethod
    async def post_feedback(self, message_id: str, is_like: bool) -> None:
        pass
    
    @abstractmethod
    async def post_rating(self, message_id: str, rating: int) -> None:
        pass
    
    @abstractmethod
    def get_all_feedbacks(self, page_number: int = 1, page_size: int = 10) -> Any:
        pass
    
    @abstractmethod
    async def post_two_chats(
        self,
        conversation_id: str,
        first_msg_id: str,
        first_user_id: str,
        first_role: str,
        first_message: str,
        first_msg_summary: str,
        second_user_id: str,
        second_msg_id: str,
        second_role: str,
        second_message: str,
        second_msg_summary: str,
        input_token: int = 0,
        output_token: int = 0
    ) -> tuple[ChatMessageModel, ChatMessageModel]:
        """
        Post two chat messages together to the database
        
        Args:
            conversation_id: ID of the conversation for both messages
            first_user_id: User ID for first message
            first_role: Role for first message
            first_message: Content of first message
            first_msg_summary: Summary of first message
            second_user_id: User ID for second message
            second_role: Role for second message
            second_message: Content of second message
            second_msg_summary: Summary of second message
            
        Returns:
            tuple[ChatMessageModel, ChatMessageModel]: Tuple containing two ChatMessageModel 
            objects representing the created messages
        """
        pass
    
    @abstractmethod
    def get_chat_by_page(self, conversation_id: str, page_number: int, limit: int) -> MessagesResponseModel:
        """Get a list of chat conversations and messages, sorted by the latest message's timestamp"""
        pass
    
    @abstractmethod
    def delete_chat_by_conversation_id(self, conversation_id: str):
        """Delete a conversation by its ID"""
        pass
    
    @abstractmethod
    def get_chat_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the chat context for a given conversation id"""
        pass
    
    # get all conversations of a user
    @abstractmethod
    def get_all_conversations(self, user_id: str, page_number: int = 1, page_size: int = 10) -> AllConversationsResponseModel:
        """Get all conversations of a user"""
        pass
    
    @abstractmethod
    def get_billing_by_user(self, user_id: str) -> List[MonthlyBilling]:
        """Get a conversation by its ID"""
        pass
    
    @abstractmethod
    def update_conversation_subject(self, conversation_id: str, subject: str) -> None:
        """Update the subject of a conversation"""
        pass