from typing import Dict, Any
import google.generativeai as genai

from src.chat.llm_factory.prompts.generate_conversation_title import generate_conversation_title, ConversationTitleResponse
from src.chat.llm_factory.llm_interface import LLMInterface
from src.chat.llm_factory.prompts.chat_prompt import get_chat_prompt, AssistantResponse
from src.chat.llm_factory.prompts.guardrail import get_guardrail_prompt, GurdrailResponse

from src.rag.rag_factory.weviate.weviate import WeviateDatabaseInistance

class OpenAiLLM(LLMInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.configure(api_key=self.api_key)

    async def generate_response(self, query: str, user_id: str, conversation_id: str) -> tuple[str, int, int]:
        
        if len(query) > 1200:
            return "Sorry, your question is too long. Please ask a shorter question.", 0, 0
        
        rag_instance = WeviateDatabaseInistance()
        
        rag_instance.connect()        
        rag_context = rag_instance.get_top_k_chunks("PIHR_DATASET", query, 3, True, 0.25)
        rag_instance.disconnect()
        
        rag_context = "\n".join(rag_context)
        
        prompt = get_chat_prompt(query, rag_context)

        model = model=genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=prompt.system_prompt)

        response = model.generate_content(
                prompt=prompt.user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=AssistantResponse
                ),
            )
        
        input_token = 0
        output_token = 0
        
        response = AssistantResponse.model_validate_json(response)
                        
        if response.assistant_response is None:
            return "Sorry, I could not find an answer to your question.", 0, 0
        
        return response.assistant_response, input_token, output_token
    
    async def check_validation(self, query: str) -> GurdrailResponse:
        
        prompt = get_guardrail_prompt(query)
        
        print("check validation for query: " + query)
        
        model = model=genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=prompt.system_prompt)
        
        response = model.generate_content(
                prompt=prompt.user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=GurdrailResponse
                ),
        )                
        
        response = GurdrailResponse.model_validate_json(response)
        
        print(response)
        
        return GurdrailResponse(
            is_safe=response.is_safe,
            reasoning_for_safety_or_danger=response.reasoning_for_safety_or_danger
        )
    
    async def generate_title(self, query: str) -> str:
        prompt = generate_conversation_title(query)
        
        print("Generate title for query : " + query)
        
        model = model=genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=prompt.system_prompt)
        
        response = model.generate_content(
                prompt=prompt.user_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json", response_schema=ConversationTitleResponse
                ),
        )                
        
        response = ConversationTitleResponse.model_validate_json(response)
        
        print(response)
        
        return response.conversation_title