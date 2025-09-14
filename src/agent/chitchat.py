from langchain_core.prompts import ChatPromptTemplate
from src.schemas.chat_response import ResponseSchemaChitchat, ResponseSchemaMod

class ChitchatReactAgent:
    """React Agent specifically for handling chitchat queries"""
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_template(
            """
            You are a friendly conversational assistant that engages in casual chat and small talk.
            Use the chat history to maintain context and make conversations feel natural and engaging.
            Keep responses warm, brief, and conversational. You can help to answer connected database related query. 
            
            --- Chat History ---
            {chat_history}
            
            Current User Query: {query}
            
            Provide a friendly, contextual response. 
            """
        )

    def execute(self, query, chat_history):
        """Execute chitchat response and return ResponseSchemaChitchat"""
        try:
            # Use structured output for chitchat
            structured_llm = self.llm.with_structured_output(ResponseSchemaChitchat)
            prompt_messages = self.prompt_template.format_prompt(
                query=query,
                chat_history=chat_history or "No previous conversation."
            ).to_messages()
            
            response = structured_llm.invoke(prompt_messages)
            return response
            
        except Exception as e:
            print(f"Chitchat agent error: {e}")
            return ResponseSchemaMod(
                answer="Hey! How can I help you today?",
                sql_query='',
                suggested_visualization_type=[],
                model_error=True,
                query_type='chitchat'
            )
        