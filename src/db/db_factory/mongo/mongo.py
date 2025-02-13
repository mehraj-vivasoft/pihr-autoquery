from pymongo import MongoClient
from typing import List, Any, Dict
from src.db.db_factory.db_interface import DBInterface
from datetime import datetime
from src.db.schemas import ChatMessageModel, AllConversationsResponseModel, MetadataModel, MessageModel, MessagesResponseModel, MonthlyBilling, FeedbacksResponseModel
from fastapi import HTTPException
from datetime import datetime

def parse_date(date: str):
    formats = [
        "%d-%m-%Y",  # Day-Month-Year
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds and UTC (Z)
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO 8601 without timezone
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format. Supported formats: {formats}")

class MongoDB(DBInterface):
    def __init__(self, uri: str, db_name: str):
        """Initialize MongoDB connection parameters"""
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    def connect(self) -> None:
        """Establish database connection"""
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        print(f"Connected to MongoDB database: {self.db_name}")

    def disconnect(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def create_conversation(self, conversation_id: str, subject: str, user_id: str) -> AllConversationsResponseModel:
        """Create a new conversation in the database"""
        conversations_collection = self.db["conversations"]
        if not conversations_collection.find_one({"id": conversation_id}):
            current_timestamp = self._get_current_timestamp()
            conversation_document = {
                "id": conversation_id,
                "subject": subject,
                "user_id": user_id,
                "company_id": conversation_id.split("_")[0],
                "created_at": current_timestamp,
                "updated_at": current_timestamp
            }
            conversations_collection.insert_one(conversation_document)
            print(f"Conversation {conversation_id} created.")

    async def post_chat(self, conversation_id: str, user_id: str, role: str, message: str, msg_summary: str) -> ChatMessageModel:
        """Post a chat message to the database"""      
        chats_collection = self.db["chats"]
        conversations_collection = self.db["conversations"]
        current_timestamp = self._get_current_timestamp()
        
        if not conversations_collection.find_one({"id": conversation_id}):
            self.create_conversation(conversation_id=conversation_id, subject=message, user_id=user_id)
        else:
            conversations_collection.update_one(
                {"id": conversation_id},
                {"$set": {"updated_at": current_timestamp}}
            )
        
        chat_document = {            
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "message": message,
            "msg_summary": msg_summary,
            "created_at": current_timestamp,
            "updated_at": current_timestamp
        }
        result = chats_collection.insert_one(chat_document)
        chat_document["message_id"] = result.inserted_id
        print(f"Chat posted to conversation {conversation_id}.")
        return ChatMessageModel(
            message_id=str(result.inserted_id),
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            message=message,
            msg_summary=msg_summary,
            created_at=current_timestamp,
            updated_at=current_timestamp
        )
    
    def post_two_chats(self, 
        conversation_id: str,
        first_user_id: str,
        first_msg_id: str,
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
            Tuple of two ChatMessageModel objects for the created messages
        """
        chats_collection = self.db["chats"]
        conversations_collection = self.db["conversations"]
        current_timestamp = self._get_current_timestamp()
        
        if not conversations_collection.find_one({"id": conversation_id}):            
            self.create_conversation(conversation_id=conversation_id, subject=first_message, user_id=first_user_id)
        else:
            conversations_collection.update_one(
                {"id": conversation_id},
                {"$set": {"updated_at": current_timestamp}}
            )
                
        first_chat = {
            "message_id": first_msg_id,
            "conversation_id": conversation_id,
            "user_id": first_user_id,
            "company_id": conversation_id.split("_")[0],
            "role": first_role,
            "message": first_message,
            "msg_summary": first_msg_summary,
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "input_token": 0,
            "output_token": 0
        }            
        
        second_chat = {
            "message_id": second_msg_id,
            "conversation_id": conversation_id,
            "user_id": second_user_id,
            "company_id": conversation_id.split("_")[0],
            "role": second_role,
            "message": second_message,
            "msg_summary": second_msg_summary,
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
            "input_token": input_token,
            "output_token": output_token
        }
                
        result = chats_collection.insert_many([first_chat, second_chat])
            
        # first_id, second_id = result.inserted_ids
                
        first_model = ChatMessageModel(
            message_id=first_msg_id,
            conversation_id=conversation_id,
            user_id=first_user_id,
            role=first_role,
            message=first_message,
            msg_summary=first_msg_summary,
            created_at=current_timestamp,
            updated_at=current_timestamp
        )
        
        second_model = ChatMessageModel(
            message_id=second_msg_id,
            conversation_id=conversation_id,
            user_id=second_user_id,
            role=second_role,
            message=second_message,
            msg_summary=second_msg_summary,
            created_at=current_timestamp,
            updated_at=current_timestamp
        )
        
        self.update_billing(date=current_timestamp, company_id=conversation_id.split("_")[0], input_token=input_token, output_token=output_token)
        
        return first_model, second_model      
    
    def update_billing(self, date: str, company_id: str, input_token: int, output_token: int) -> Any:    
        billing_collection = self.db["billing"]
        
        try:
            date_obj = parse_date(date)
        except ValueError as e:
            return {"error": f"Invalid date format. Details: {e}"}

        cost = (input_token * 0.0182 + output_token * 0.0727) / 1000

        def update_frequency(frequency: str, date: str) -> None:
            billing_collection.update_one(
                {"frequency": frequency, "date": date, "company_id": company_id},
                {
                    "$inc": {
                        "input_token": input_token,
                        "output_token": output_token,
                        "cost": cost,
                    },
                },
                upsert=True,  # Create the document if it doesn't exist
            )

        # Daily billing
        daily_date = date_obj.strftime("%d-%m-%Y")
        update_frequency("daily", daily_date)

        # Monthly billing
        monthly_date = date_obj.strftime("%m-%Y")
        update_frequency("monthly", monthly_date)

        # Yearly billing
        yearly_date = date_obj.strftime("%Y")
        update_frequency("yearly", yearly_date)

        return {"message": "Billing updated successfully"}
    
    def get_overall_billing(self, date_from: str = None, date_to: str = None, frequency: str = "daily", page_number: int = 1, page_size: int = 10):
        billing_collection = self.db["billing"]

        # Parse dates if provided
        query = {"frequency": frequency}

        if date_from:
            try:
                date_from_obj = parse_date(date_from)
                query["date"] = {"$gte": date_from_obj.strftime("%d-%m-%Y")}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid date_from format. Details: {e}")

        if date_to:
            try:
                date_to_obj = parse_date(date_to)
                query["date"] = query.get("date", {})
                query["date"].update({"$lte": date_to_obj.strftime("%d-%m-%Y")})
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid date_to format. Details: {e}")

        # Pagination logic
        skip = (page_number - 1) * page_size
        limit = page_size

        # Fetch data from MongoDB
        cursor = billing_collection.find(query).skip(skip).limit(limit)
        billing_data = list(cursor)

        # Calculate totals
        total_cost = 0
        total_input_tokens = 0
        total_output_tokens = 0
        formatted_data = []

        for record in billing_data:
            total_cost += record["cost"]
            total_input_tokens += record["input_token"]
            total_output_tokens += record["output_token"]

            formatted_data.append({ 
                "title": record["date"],
                "total_input_tokens": record["input_token"],
                "total_output_tokens": record["output_token"],
                "billing_amount": record["cost"],
            })

        # Get the total count of documents for metadata
        total_count = billing_collection.count_documents(query)
        total_pages = (total_count + page_size - 1) // page_size

        # Prepare the response
        response = {
            "total_cost": total_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "frequency": frequency,
            "data": formatted_data,
            "metadata": {
                "total": total_count,
                "page_number": page_number,
                "total_pages": total_pages,
                "page_size": page_size,
            },
        }

        return response         
    
    def get_chat_by_page(self, conversation_id: str, page_number: int = None, limit: int = 10) -> MessagesResponseModel:
        """Get the latest page of chat conversations and messages, sorted by the latest message's timestamp"""
        chats_collection = self.db["chats"]
        
        # Calculate total pages and total entries
        total_pages, total_entries = self._get_total_page(conversation_id=conversation_id, page_size=limit)
        
        # If page_number is not provided or is None, fetch the latest page
        if page_number is None or page_number > total_pages:
            page_number = total_pages
        
        # Calculate skip_count for pagination
        skip_count = (page_number - 1) * limit
        
        # Fetch messages from the database
        chats = chats_collection.find({"conversation_id": conversation_id}).sort([("created_at", -1), ("role", 1)]).skip(skip_count).limit(limit)
        chat_list = []
        for chat in chats:
            chat_list.append(MessageModel(id=str(chat["message_id"]), 
                                        content=chat["message"], 
                                        role=chat["role"],                                           
                                        timestamp=chat["created_at"]))
        
        return MessagesResponseModel(messages=chat_list, 
                                    metadata=MetadataModel(total=total_entries, 
                                                            page_number=page_number, 
                                                            total_pages=total_pages, 
                                                            page_size=limit))

    def delete_chat_by_conversation_id(self, conversation_id: str):
        """Delete a conversation by its ID"""
        try:
            self.db["chats"].delete_many({"conversation_id": conversation_id})
            self.db["conversations"].delete_one({"id": conversation_id})
            print(f"Conversation {conversation_id} deleted.")
            return {"message": "Chats deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {e}")
    
    def get_chat_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the recent 6 chats for a given conversation id"""
        chats_collection = self.db["chats"]
        context = chats_collection.find({"conversation_id": conversation_id}).sort("timestamp", -1).limit(6)
        return list(context)
    
    def get_all_conversations(self, user_id: str, page_number: int = 1, page_size: int = 10) -> AllConversationsResponseModel:
        """Get all conversations of a user"""
        conversations_collection = self.db["conversations"]
        total_pages, total_entries = self._get_total_page_overall(user_id=user_id, page_size=page_size)
        skip_count = (page_number - 1) * page_size
        conversations = conversations_collection.find({"user_id": user_id}).sort("updated_at", -1).skip(skip_count).limit(page_size)
        response = []
        for conversation in conversations:
            response.append({
                "id": conversation["id"],
                "user_id": conversation["user_id"],
                "subject": conversation["subject"],
                "created_at": conversation["created_at"],
                "updated_at": conversation["updated_at"]
            })                
        
        return AllConversationsResponseModel(conversations=response, 
                                             metadata=MetadataModel(total=total_entries, 
                                                                    page_number=page_number, 
                                                                    total_pages=total_pages, 
                                                                    page_size=page_size))
    
    def post_feedback(self, message_id: str, is_like: bool) -> None:
        feedback_collection = self.db["feedbacks"]
        message_collection = self.db["chats"]
        current_timestamp = self._get_current_timestamp()
        the_message = message_collection.find_one({"message_id": message_id})
        message_timestamp = the_message["created_at"]
        conversation_id = the_message["conversation_id"]
        user_id = the_message["user_id"]
        if not message_timestamp:
            raise HTTPException(status_code=404, detail="Message not found")
        if not conversation_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        # get ai and user message
        message_pair = message_collection.find({"created_at": message_timestamp, "conversation_id": conversation_id})
        for message in message_pair:
            if message["role"] == "user":
                user_message = message["message"]
            if message["role"] == "assistant":
                ai_message = message["message"]
        # insert feedback        
        feedback_collection.insert_one({"message_id": message_id, "is_like": is_like, "created_at": current_timestamp, "rating": -1,
                                        "user_id": user_id, "conversation_id": conversation_id, "user_message": user_message, "ai_message": ai_message})
        
        return {"message": "Feedback posted successfully"}
    
    def post_rating(self, message_id: str, rating: int) -> None:
        feedback_collection = self.db["feedbacks"]
        feedback_entry = feedback_collection.find_one({"message_id": message_id})
        if not feedback_entry:
            raise HTTPException(status_code=404, detail="Feedback not found")
                
        feedback_collection.update_one({"message_id": message_id}, {"$set": {"rating": rating}})
        return {"message": "Rating updated successfully"}        
    
    def update_conversation_subject(self, conversation_id: str, subject: str) -> None:
        conversations_collection = self.db["conversations"]
        conversations_collection.update_one({"id": conversation_id}, {"$set": {"subject": subject}})
        return {"message": "Conversation subject updated successfully"}

    def get_all_feedbacks(self, is_liked: bool = False, page_number: int = 1, page_size: int = 10) -> FeedbacksResponseModel:
        feedback_collection = self.db["feedbacks"]
        total_pages, total_entries = self._get_total_feedback_page_overall(page_size=page_size, is_liked=is_liked)
        skip_count = (page_number - 1) * page_size
        feedbacks = feedback_collection.find({"is_like": is_liked}).sort("created_at", -1).skip(skip_count).limit(page_size)
        response = []                
        
        for feedback in feedbacks:
            if "user_id" not in feedback:
                feedback["user_id"] = -1
            response.append({
                "id": feedback["message_id"],
                "is_like": feedback["is_like"],
                "rating": feedback["rating"],
                "created_at": feedback["created_at"],
                "conversation_id": feedback["conversation_id"],
                "user_id": feedback["user_id"],
                "user_message": feedback["user_message"],
                "ai_message": feedback["ai_message"]
            })                
        
        return FeedbacksResponseModel(feedbacks=response, 
                                      metadata=MetadataModel(total=total_entries, 
                                                             page_number=page_number, 
                                                             total_pages=total_pages,
                                                             page_size=page_size))
        
    def count_feedbacks(self) -> Any:
        messages_collections = self.db["chats"]
        total_messages = messages_collections.count_documents({}) / 2
        
        feedback_collection = self.db["feedbacks"]
        positive_feedback = feedback_collection.count_documents({"is_like": True})
        negative_feedback = feedback_collection.count_documents({"is_like": False})
        
        return {
            "total_messages": total_messages,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback
        }
    
    def get_billing_by_user(self, user_id: str) -> List[MonthlyBilling]:
        """
        Calculate the monthly billing for a given user_id.

        Args:
            user_id (str): The user_id to filter the records.
            config (MongoDBConfig): Configuration for MongoDB.
            input_rate (float): Billing rate per input token.
            output_rate (float): Billing rate per output token.

        Returns:
            List[MonthlyBilling]: A list of monthly billing details.
        """
        chats_collection = self.db["chats"]
        
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": {"$toDate": "$created_at"}},
                        "month": {"$month": {"$toDate": "$created_at"}}
                    },
                    "total_input_tokens": {"$sum": "$input_token"},
                    "total_output_tokens": {"$sum": "$output_token"},
                }
            },
            {
                "$sort": {"_id.year": 1, "_id.month": 1}
            }
        ]
        
        result = list(chats_collection.aggregate(pipeline))
        
        billing_details = []
        for record in result:
            year = record["_id"]["year"]
            month = record["_id"]["month"]
            total_input_tokens = record["total_input_tokens"]
            total_output_tokens = record["total_output_tokens"]

            billing_amount = (total_input_tokens * 0.018) + (total_output_tokens * 0.072)
            billing_amount = billing_amount / 1000

            billing_details.append(MonthlyBilling(
                month=f"{year}-{month:02d}",
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                billing_amount=billing_amount
            ))

        return billing_details
    
    def _get_total_page(self, conversation_id: str, page_size: int) -> (int, int):
        """Get total number of page of a conversation id"""
        chats_collection = self.db["chats"]
        total_count = chats_collection.count_documents({"conversation_id": conversation_id})        
        return ((total_count + page_size - 1) // page_size, total_count)

    def _get_total_page_overall(self, user_id: str, page_size: int) -> (int, int):
        """Get total number of page of a conversation id"""
        conversations_collection = self.db["conversations"]
        total_count = conversations_collection.count_documents({"user_id": user_id})
        return ((total_count + page_size - 1) // page_size, total_count)

    def _get_total_feedback_page_overall(self, page_size: int, is_liked: bool = False) -> (int, int):
        """Get total number of page of a conversation id"""
        feedbacks_collections = self.db["feedbacks"]
        total_count = feedbacks_collections.count_documents({"is_like": is_liked})
        return ((total_count + page_size - 1) // page_size, total_count)    

    def _get_current_timestamp(self) -> str:
        """Helper method to get the current timestamp in ISO format with Z"""
        return datetime.now().isoformat() + "Z"


# Example usage:
# mongo = MongoDB(uri="mongodb://localhost:27017", db_name="chat_db")
# mongo.connect()
# mongo.post_chat("conversation123", "user456", "user", "Hello!", "Greeting message")
# chats = mongo.get_chat_by_page("conversation123", 1)
# print(chats)
# context = mongo.get_chat_context("conversation123")
# print(context)
# mongo.disconnect()


