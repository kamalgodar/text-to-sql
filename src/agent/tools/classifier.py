from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model


class Classification(BaseModel):
    query_type: Literal["database", "chitchat", "general"] = Field(..., 
                                                                   description=(
                                                                       "database if user query or part of user query is realted to database. if it's about accessing/querying data from the database "
                                                                       "chitchat if it's casual conversation or small talk"
                                                                       "general anything else not clearly about the database or casual chitchat."))

class QueryClassifier:
    def __init__(self, data_dictionary: str, chat_history: str, model):
        self.data_dictionary = data_dictionary
        self.chat_history = chat_history
        self.prompt_template = ChatPromptTemplate.from_template(
            """
            You are a classifier that determines whether a user query is:
            Read the following data dictionary and chat history and current user query to do classification. 
            Take into account:
            1. The database structure or Dtabase Data Dictionary
            2. The previous messages in the conversation (chat history)
            3. If User Query has both chitchat and database realted topics the classification should be database

            --- Database Data Dictionary ---
            {data_dictionary}

            --- Chat History ---
            {chat_history}

            --- Current User Query ---
            {input}

            Respond with the field:
            - query_type: "database", "chitchat", or "general"
            """
        )
        self.llm = model.with_structured_output(Classification)

    def classify_query(self, user_query: str) -> Classification:
        prompt_messages = self.prompt_template.format_prompt(
            input=user_query,
            chat_history=self.chat_history,
            data_dictionary=self.data_dictionary
        ).to_messages()
        result = self.llm.invoke(prompt_messages)
        print("The classification is ", result)
        return result



# === Example Usage ===
if __name__ == "__main__":
    # from src.agent.tools.chat_history import get_chat_history
    data_dictionary = """
    Tables:
    - users (id, name, email, signup_date)
    - orders (order_id, user_id, product, price, order_date)
    - products (product_id, name, category, price)
    """
    chat_history = ""

    model_id = "us.amazon.nova-pro-v1:0"  # your model id

    # Initialize Bedrock model
    bedrock_model = init_chat_model(model=model_id, model_provider='bedrock')

    # Initialize classifier with data dictionary, chat history, and model
    classifier = QueryClassifier(data_dictionary, chat_history, bedrock_model)

    # Example user query
    user_query = "Show me all users who signed up in May."

    # Classify the query
    classification_result = classifier.classify_query(user_query)

    print(classification_result)
