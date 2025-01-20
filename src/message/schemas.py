from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FeedbackModel(BaseModel):
    is_liked: bool
    
class RatingModel(BaseModel):
    rating: int