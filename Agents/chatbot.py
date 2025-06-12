# Agents/chatbot.py

import time
from typing import Optional

# Import necessary functions from other modules
from Agents.llms_manager_agent import LLMManager
from Agents.search_agent import SearchAgent

class ChatbotAgent:
    """
    A class to handle conversational interactions with a user, simulating a
    board-certified dermatologist AI assistant. It uses an LLM to generate responses
    based on user queries and conversation history, potentially augmented with web search results.
    """

    def __init__(self):
        
        
        self.llm = LLMManager()  # Initialize the LLM manager
        self.search = SearchAgent()  # Initialize the search agent

        
    def generate_chat_response(self, user_query: str) -> str:
        """
        Generates a conversational response using the LLM, potentially augmenting
        with web search results. Maintains the dermatologist persona set in the model's
        system instructions and uses the provided chat session history.

        Args:
            chat_session: The active ChatSession object containing conversation history.
            user_query: The latest message/query from the user.

        Returns:
            The LLM's response string, or an error string beginning with "Error:".
        """
        print(f"Processing chat query within Chatbot Agent: '{user_query[:100]}...'")

        search_context = ""
        max_search_chars = 5000 # Limit context size from search

        # --- 1. Perform Web Search (if available) ---
        print("  Performing web search for context...")
        
        # Using specific search_type="web"
        search_context = self.search.deepsearch(user_query, max_results=3)
            
        # --- 2. Construct Prompt for LLM ---
        # We provide the user query and any supplemental search context.
        if search_context:
            prompt = (f"""
            User Query: "{user_query}"

            Potentially relevant context from a web search:
            --- START SEARCH CONTEXT ---
            {search_context[:max_search_chars]}
            --- END SEARCH CONTEXT ---

            Considering the conversation history AND the search context above, please respond to the User Query. Maintain your persona as a helpful, board-certified dermatologist AI assistant .
            """)
        else:
            # If no search context, just pass the user query directly
            prompt = user_query # Simpler prompt, relying on history and system instruction

        # --- 3. Send to LLM ---
        # print("Sending query (with search context if available) to LLM via send_message_to_llm...")
        # Use the imported send_message_to_llm function and the passed chat_session
        llm_response = self.llm.send_message_to_llm(prompt)

        # --- 4. Handle Response ---
        # send_message_to_llm returns either the text response or an "Error: ..." string
        if isinstance(llm_response, str) and llm_response.startswith("Error:"):
            print(f"❌ LLM error reported by send_message_to_llm: {llm_response}")
            return llm_response
        elif not isinstance(llm_response, str) or not llm_response.strip():
            print("❌ LLM returned an empty or invalid response for chat query.")
            return "Error: Received an empty response from the assistant."
        else:
            print("✅ Chatbot Agent received valid LLM response.")
            # History in chat_session is automatically updated by the call to send_message_to_llm
            return llm_response.strip()