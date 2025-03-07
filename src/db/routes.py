from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from src.db.db_factory.db_interface import DBInterface
from src.db.db_factory.mongo.mongo import MongoDB
from src.db.schemas import ChatPost, ChatQuery, MonthlyBilling, TitleChangeRequest, OverallBillingResponse

# Initialize FastAPI router
router = APIRouter()

# Dependency to ensure MongoDB is connected
async def get_db() -> DBInterface:
    """Dependency to ensure MongoDB is connected with proper error handling."""
    db_instance = None
    try:
        db_instance = MongoDB(uri="mongodb://admin:kothinAdminPass@mongodb:27017", db_name="chat_db")
        db_instance.connect()
        
        if db_instance.db is None:
            print("Database connection not available")            
            raise HTTPException(
                status_code=503, 
                detail="Database connection not available"
            )
            
        yield db_instance
        
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong"
        )
    finally:
        if db_instance:
            db_instance.disconnect()      

# Example API call: GET /conversations?user_id=<user_id>
@router.get("/", response_model=Any)
async def get_conversations(user_id: str, page_number: int = 1, page_size: int = 10, db: DBInterface = Depends(get_db)):
    """Endpoint to get all conversations for a user."""
    try:        
        conversations = db.get_all_conversations(user_id, page_number, page_size)
        print(conversations)
        return conversations
    except Exception as e:
        print(f"Failed to fetch conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations")
    
# Example API call: GET /<conversation_id>?page=<page>&limit=<limit>
@router.get("/{conversation_id}", response_model=Any)
async def get_chats(conversation_id: str, page_number: int = 1, page_size: int = 10, db: DBInterface = Depends(get_db)):
    """Endpoint to get chats by page."""
    try:        
        chats = db.get_chat_by_page(conversation_id, page_number, page_size)
        return chats
    except Exception as e:
        print(f"Failed to fetch chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chats")
    
# Example API call: DELETE /<conversation_id>?page=<page>&limit=<limit>
@router.delete("/{conversation_id}", response_model=Any)
async def delete_chats(conversation_id: str, db: DBInterface = Depends(get_db)):
    """Endpoint to get chats by page."""
    try:        
        chats = db.delete_chat_by_conversation_id(conversation_id)
        return chats
    except Exception as e:
        print(f"Failed to delete chats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chats")

@router.patch("/{conversation_id}", response_model=Any)
async def update_chat(conversation_id: str, title_change_req: TitleChangeRequest, db: DBInterface = Depends(get_db)):
    """Endpoint to get chats by page."""
    try:        
        chats = db.update_conversation_subject(conversation_id, title_change_req.title)
        return chats
    except Exception as e:
        print(f"Failed to update chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update chat")

# Example API call: POST /chats
@router.post("/chats", response_model=dict)
async def post_chat(chat: ChatPost, db: DBInterface = Depends(get_db)):
    """Endpoint to post a chat message."""
    try:
        db.post_chat(
            conversation_id=chat.conversation_id,
            user_id=chat.user_id,
            role=chat.role,
            message=chat.message,
            msg_summary=chat.msg_summary
        )
        return {"message": "Chat posted successfully"}
    except Exception as e:
        print(f"Failed to post chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to post chat")

@router.get("/chat-context", response_model=List[Dict[str, Any]])
async def get_chat_context(conversation_id: str, db: DBInterface = Depends(get_db)):
    """Endpoint to get the last 6 chats for a conversation."""
    try:
        context = db.get_chat_context(conversation_id)
        return context
    except Exception as e:
        print(f"Failed to fetch chat context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat context")
    
@router.get("/stats/feedbacks", response_model=Any)
async def get_feedback_stats(db: DBInterface = Depends(get_db)):
    try:        
        stats = db.count_feedbacks()        
        return stats
    except Exception as e:
        print(f"Failed to fetch feedback stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback stats")

@router.get("/billing/overall", response_model=OverallBillingResponse)
async def get_overall_billing(date_from: str = None, date_to: str = None, frequency: str = "daily", page_number: int = 1, page_size: int = 10, db: DBInterface = Depends(get_db)):
    """Endpoint to get the overall billing."""
    try:
        billing = db.get_overall_billing(date_from, date_to, frequency, page_number, page_size)
        return OverallBillingResponse(**billing)
    except Exception as e:
        print(f"Failed to fetch billing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch billing")

@router.get("/billing/company-wise", response_model=Any)
async def get_overall_billing(date_from: str = None, date_to: str = None, frequency: str = "daily", page_number: int = 1, page_size: int = 10, db: DBInterface = Depends(get_db)):
    """Endpoint to get the overall billing."""
    try:
        billing = db.get_overall_billing_by_company(date_from, date_to, frequency, page_number, page_size)
        return billing
    except Exception as e:
        print(f"Failed to fetch billing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch billing")

@router.get("/billing/company/{company_id}", response_model=OverallBillingResponse)
async def get_overall_billing(company_id: str, date_from: str = None, date_to: str = None, frequency: str = "daily", page_number: int = 1, page_size: int = 10, db: DBInterface = Depends(get_db)):
    """Endpoint to get the overall billing."""
    try:
        billing = db.get_billing_by_company_id(date_from, date_to, frequency, company_id, page_number, page_size)
        return OverallBillingResponse(**billing)
    except Exception as e:
        print(f"Failed to fetch billing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch billing")

@router.get("/billing/user/{user_id}", response_model=List[MonthlyBilling])
async def get_billing_by_user(user_id: str, db: DBInterface = Depends(get_db)):
    """Endpoint to get the monthly billing for a user."""
    try:
        billing = db.get_billing_by_user(user_id)
        return billing
    except Exception as e:
        print(f"Failed to fetch billing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch billing")