from typing import Any, Type

from pydantic import BaseModel

class Prompt(BaseModel):
    system_prompt: str
    user_prompt: str
    response_format: Type[BaseModel]
    
class ConversationTitleResponse(BaseModel):
    conversation_title: str

def generate_conversation_title(query: str) -> Prompt:
    
    system_prompt = f"""
    You are a conversation title generator that generates a conversation title based on the user query.
    The conversation is about PiHR, which is a SaaS based fully integrated HR and payroll software management system and
    user can ask for any information from PiHR Service and how to use it.    
    """
    
    user_prompt = f"""
    The User Query is: 
    {query}
    
    Now, you have to generate a conversation title based on the user query.
    """
    
    return Prompt(system_prompt=system_prompt, user_prompt=user_prompt, response_format=ConversationTitleResponse)