from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from src.db.db_factory.db_interface import DBInterface
from src.db.db_factory.mongo.mongo import MongoDB
from src.message.schemas import FeedbackModel, RatingModel

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


@router.post("/{message_id}/feedback", response_model=Any)
async def post_feedback(message_id: str, feedback: FeedbackModel, db: DBInterface = Depends(get_db)):
    """Endpoint to post feedback."""
    try:        
        chats = db.post_feedback(message_id, feedback.is_liked)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post feedback: {e}")
    

@router.post("/{message_id}/rating", response_model=Any)
async def post_rating(message_id: str, rating: RatingModel, db: DBInterface = Depends(get_db)):
    """Endpoint to post rating."""
    try:
        chats = db.post_rating(message_id, rating.rating)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post rating: {e}")

@router.get("/feedbacks", response_model=Any)
async def get_feedbacks(db: DBInterface = Depends(get_db)):
    """Endpoint to get feedbacks."""
    try:        
        chats = db.get_all_feedbacks()
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedbacks: {e}")