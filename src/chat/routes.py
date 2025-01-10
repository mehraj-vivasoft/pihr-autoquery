from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Union
from src.chat.llm_factory.llm_interface import LLMInterface
from src.chat.schema import ChatRequest, NewConversationModel, MessageModel, ReplyModel
from src.chat.llm_factory.openai.openai import OpenAiLLM
from src.db.db_factory.db_interface import DBInterface
from src.db.db_factory.mongo.mongo import MongoDB
from datetime import datetime
from dotenv import load_dotenv
import os

# Initialize FastAPI router
router = APIRouter()

async def get_llm() -> LLMInterface:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OpenAI API key")

    llm_instance = OpenAiLLM(api_key=api_key)

    try:
        print("Connected to LLM")
        yield llm_instance
    finally:
        # Perform cleanup if needed
        llm_instance = None

async def get_db() -> DBInterface:
    """Dependency to ensure MongoDB is connected with proper error handling."""
    db_instance = None
    try:
        db_instance = MongoDB(uri="mongodb://admin:kothinAdminPass@mongodb:27017", db_name="chat_db")
        db_instance.connect()
        
        if db_instance.db is None:
            raise HTTPException(
                status_code=503, 
                detail="Database connection not available"
            )
            
        yield db_instance
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )
    finally:
        if db_instance:
            db_instance.disconnect()

async def post_chat_pair_in_bg(chat_init: ChatRequest, assistant_response: str, current_timestamp: str, input_token: int = 0, output_token: int = 0):
    
    db = MongoDB(uri="mongodb://admin:kothinAdminPass@mongodb:27017", db_name="chat_db")
    db.connect()
    
    if chat_init.is_new:        
        # conv_title = await llm.generate_title(chat_init.question)
        conv_title = chat_init.question
        
        db.create_conversation(
            conversation_id=chat_init.conversation_id,
            subject=conv_title,
            user_id=chat_init.user_id
        )
        
        one, two = db.post_two_chats(
            conversation_id=chat_init.conversation_id,
            first_user_id=chat_init.user_id,
            first_msg_id=chat_init.user_id + current_timestamp + "usr",
            first_role="user",
            first_message=chat_init.question,
            first_msg_summary=chat_init.question,
            second_user_id=chat_init.user_id,
            second_msg_id=chat_init.user_id + current_timestamp + "ai",
            second_role="assistant",
            second_message=assistant_response,
            second_msg_summary=assistant_response
        )
        
        print("Chat pair posted in the background")
        
    else:
                            
        db.post_two_chats(
            conversation_id=chat_init.conversation_id,
            first_user_id=chat_init.user_id,
            first_msg_id=chat_init.user_id + current_timestamp + "usr",
            first_role="user",
            first_message=chat_init.question,
            first_msg_summary=chat_init.question,
            second_user_id=chat_init.user_id,
            second_msg_id=chat_init.user_id + current_timestamp + "ai",
            second_role="assistant",
            second_message=assistant_response,
            second_msg_summary=assistant_response,
            input_token=input_token,
            output_token=output_token
        )
        
        print("Chat pair posted in the background")
    
    db.disconnect()

@router.post("/", response_model=Union[NewConversationModel, MessageModel])
async def complete_query(chat_init: ChatRequest, background_tasks: BackgroundTasks, llm: LLMInterface = Depends(get_llm)):
    """
    Endpoint to generate a response based on previous messages.

    Args:
    - chat_init (ChatRequest): Contains user_id, conversation_id, and query

    Returns:
    - str: Contains the response
    """    
    
    # assistant_response = None
    # validation_chk = await llm.check_validation(chat_init.question)
    
    # if validation_chk.is_safe:        
    #     assistant_response = await llm.generate_response(
    #         query=chat_init.question, user_id=chat_init.user_id, conversation_id=chat_init.conversation_id
    #     )
    # else:        
    #     assistant_response = validation_chk.reasoning_for_safety_or_danger
    
    assistant_response, input_token, output_token = await llm.generate_response(
            query=chat_init.question, user_id=chat_init.user_id, conversation_id=chat_init.conversation_id
        )
    
    current_timestamp = datetime.now().isoformat() + "Z"
    
    background_tasks.add_task(post_chat_pair_in_bg, chat_init, assistant_response, current_timestamp, input_token, output_token)
    
    if chat_init.is_new:
        print("responded")
        return NewConversationModel(conversation_id=chat_init.conversation_id, 
                                    user_id=chat_init.user_id,
                                    subject=chat_init.question,
                                    created_at=current_timestamp,
                                    updated_at=current_timestamp,
                                    is_new=True,
                                    reply=ReplyModel(
                                        id=chat_init.user_id + current_timestamp + "ai",
                                        content=assistant_response,
                                        timestamp=current_timestamp
                                    ))
        
    else:
        print("responded")
        return MessageModel(message_id=chat_init.user_id + current_timestamp + "ai",
                            conversation_id=chat_init.conversation_id,
                            content=assistant_response,
                            timestamp=current_timestamp,
                            is_new=False)