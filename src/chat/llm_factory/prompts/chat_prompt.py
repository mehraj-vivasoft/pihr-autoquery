
# from user query, rag context of the query, and chat history: generate chat prompt
from typing import Any

from pydantic import BaseModel

class AssistantResponse(BaseModel):
    assistant_response: str    

class Prompt(BaseModel):
    system_prompt: str
    user_prompt: str    

def get_chat_prompt(query: str, rag_context: str) -> Prompt:
    
    system_prompt = f"""
    You are a chatbot that answers questions about PiHR, which is a SaaS based fully integrated HR and payroll software management system and 
    user can ask for any information from PiHR Service and how to use it. 
    
    You will be provided with a user query and some background context related to the user query. 
    
    Use the relevant information from the background context, and ignore the irrelevant information in the background context to answer the user query.
    If you cannot answer the user query based on the background context, you should tell the user that you cannot answer the user query. If the user asks 
    for any irrelevant information, you should tell the user that you cannot answer the user query except for the information related to PiHR. You may do 
    general information like greetings or general information which may be relevant to PiHR. Also if the user asks for any destructive actions like 
    delete, update, edit, create etc. then you should tell the user that you are not authorized to do that action.
    
    - Make sure that the response is not too long.
    
    Do not use bangla transliterations like "eta holo banglish kotha" instead use this type of tone in bangla -> "eta holo banglish kotha"
    ALSO DO NOT MIX UP BANGLA AND ENGLISH CHARACTERS EITHER RESPONSE IN BANGLA OR IN ENGLISH
    """
    
    user_prompt = f"""
    # Here is the user query:
    ## User Query: 
    - {query}
    
    # Here is some background information related to the user query:
    ## Background Context related to the user query: 
    - {rag_context}
    
    Now, respond to the user query based on the background context.
    
    Do not use bangla transliterations like "eta holo banglish kotha" instead use this type of tone in bangla -> "eta holo banglish kotha"
    ALSO DO NOT MIX UP BANGLA AND ENGLISH CHARACTERS EITHER RESPONSE IN BANGLA OR IN ENGLISH
    """
    
    return Prompt(system_prompt=system_prompt, user_prompt=user_prompt)