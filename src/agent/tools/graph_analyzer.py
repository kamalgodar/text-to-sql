from typing import List
from pydantic import BaseModel
# from langchain.chat_models import init_chat_model
from trustcall import create_extractor
from src.data_dictionary.extract import explanations
from src.agent.prompts.graphing import graph_prompt

class PromptBuilder:
    def __init__(
        self,
        data_sample: List[dict],
        sql_query: str,
        graph_type: str,
        chat_history: str,
        latest_user_query: str,
        column_names:List,
        agent_response_summary:str,
    ):
        self.data_sample = data_sample
        self.sql_query = sql_query
        self.graph_type = graph_type
        self.chat_history = chat_history
        self.latest_user_query = latest_user_query
        self.column_names = column_names
        self.data_dictionary= explanations()
        self.agent_response_summary = agent_response_summary

    def build(self) -> str:
        return graph_prompt.format(data_sample=self.data_sample,
                                   sql_query=self.sql_query,
                                   graph_type=self.graph_type,
                                   chat_history=self.chat_history,
                                   latest_user_query=self.latest_user_query,
                                   column_names=self.column_names,
                                   data_dictionary=self.data_dictionary,
                                   agent_response_summary=self.agent_response_summary,)


class ChartSuggester:
    def __init__(self, llm):
        self.llm = llm
    def suggest_chart(self, prompt: str, schema: BaseModel) -> dict:
        try:
            extractor = create_extractor(self.llm, tools=[schema])
            response = extractor.invoke({"messages": [{"role": "user", "content": prompt}]})
            # print("Raw Response:", response)
            if "responses" in response and response["responses"]:
                return response["responses"][0].model_dump()
            else:
                return {}
        except Exception as e:
            print("Exception during extraction:", e)
            return {}


# === Example Usage ===
if __name__ == "__main__":
    from src.models.graph_models import LineChartSuggestion, BarChartSuggestion, PieChartSuggestion, Table
    data_sample = [
        {"date": "2023-01-01", "sales": 1500, "category": "Electronics", "discount": 10},
        {"date": "2023-01-01", "sales": 800, "category": "Clothing", "discount": 97},
        {"date": "2023-01-02", "sales": 1600, "category": "Electronics", "discount": 250},
        {"date": "2023-01-02", "sales": 950, "category": "Clothing", "discount": 50},
    ]
    sql_query = "SELECT date, sales, category, SUM(discount) as discount FROM sales_data GROUP BY date, category"
    chat_history = ""
    user_query = "Display the category sales and their discounts on Jan 2023"
    graph_type = "line"
    
    prompt = PromptBuilder(
        data_sample=data_sample[:20],
        sql_query=sql_query,
        graph_type=graph_type,
        chat_history=chat_history,
        latest_user_query=user_query,
    ).build()
    llm = init_chat_model(model='us.amazon.nova-pro-v1:0', model_provider='bedrock')
    suggester = ChartSuggester(llm=llm)
    output = suggester.suggest_chart(prompt, LineChartSuggestion if graph_type == 'line' else '')

    print("Final Output:")
    print(output)
