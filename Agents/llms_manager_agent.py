from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import GEMINI_API, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
import logging
import re 
import json
from config import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS
from typing import List, Union, Dict

class LLMManager:
    def __init__(self, model=None, api_key=GEMINI_API, temperature=None, max_tokens=None, timeout=None):
        self._model = model or LLM_MODEL
        self._api_key = api_key 
        self._temperature = temperature if temperature is not None else LLM_TEMPERATURE
        self._max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        self._timeout = timeout
        self.SYSTEM_INSTRUCTIONS =  SystemMessage(content= """You are a highly experienced, board-certified dermatologist. 
        Always think step-by-step, reference clinical reasoning, and answer strictly in JSON if asked. 
        When diagnosing, cite visual features, propose differentials, and state confidence levels.""")
        
        # Use proper message types and maintain conversation history
        self.conversation_history: str = '' # Initialize as empty string to hold conversation history including  HumanMessage, AIMessage
        self.prompt = ChatPromptTemplate.from_messages([
            self.SYSTEM_INSTRUCTIONS,
            ("human", "{user_input}"),
]) 

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=self._model,
                api_key=self._api_key,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                max_retries=2,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini LLM: {e}")

    def invoke_llm(self, messages:str):
        """Handle both new messages and conversation history"""
        try:
            chain = self.prompt | self.llm | StrOutputParser()
            return chain.invoke({'user_input': messages})
        
        except Exception as e:
            logging.error(f'LLM invocation failed: {e}')
            raise RuntimeError(f'LLM invocation error: {e}')

    def send_message_to_llm(self, user_prompt: str) -> str:
        """Maintain full conversation context with proper message types"""
        # Append user message
        self.conversation_history += f"USER: {user_prompt}\n"
        
        try:
            response = self.invoke_llm(self.conversation_history)
            # Append and store assistant response
            self.conversation_history += f"AI_RESPONSE :{response}\n"
            return self.parse_response(response)
            
        except Exception as e:
            logging.error(f'Conversation failed: {e}')
            # Remove last user message if failed
            self.conversation_history = self.conversation_history.rsplit(f"USER: {user_prompt}\n", 1)[0]
            raise e

    def describe_visuals(self, visual_url: str, mime_type: str) -> str:
        """Handle visual analysis with proper message types"""
        prompt = (
            "Analyze the visuals (i.e., image/video) provided as a board-certified dermatologist. "
            "1) List **all** observable skin features under these headings: Color, Morphology, Surface Changes, Texture, Distribution, Hair/Nails, Secondary Signs.  "
            "2) Highlight any subtle or atypical findings.  "
            "3) Be purely descriptive—no diagnosis or assumptions.  "
            "Format your answer as a Markdown bullet list."
        )
        
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url" if mime_type in ALLOWED_IMAGE_EXTENSIONS else "video_url", 
             "image_url" if mime_type in ALLOWED_IMAGE_EXTENSIONS else "video_url": visual_url}
        ]
        
        try:
            response = self.invoke_llm([HumanMessage(content=content)])
            return response.content
        except Exception as e:
            logging.error(f'Visual analysis failed: {e}')
            return f"Error analyzing visuals: {str(e)}"

    @staticmethod
    def parse_response(response):
        if hasattr(response, 'content'):
            response_raw = response.content.strip()
        else:
            response_raw = str(response).strip()
            response_raw = response_raw.replace('``````', '').strip()
            response_clean = re.search(r'(\[.*\]|\{.*\})', response_raw, re.DOTALL)
        try:
            response_str = response_clean.group(0)
            return json.loads(response_str)
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            raise ValueError(f"JSON decoding failed. Raw response: {response_raw}\nError: {e}")

  

