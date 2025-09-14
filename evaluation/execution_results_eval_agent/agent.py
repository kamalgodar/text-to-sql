from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from src.configs.settings import settings
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from typing import Optional
from .response_schema import ExecutionResultsEquivalence


MODEL_ID = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"
    
    
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    print("Before Agent Callback:")
    callback_context.state["agent_input"] = "Identify if the two result sets generated from execution of two SQL queries are identical or not."
    
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    print(f"Agent Name: {agent_name}\n Invocation_id: {invocation_id}\n Current_state: {current_state}\n")
    
    
def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    print("Before Model Callback:")
    print(f"System Prompt: {llm_request.config.system_instruction}\n")

    
def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    print("After Model Callback:")
    print("Agent Name:", callback_context.agent_name)
    print(f"LLM Response: {llm_response.content.parts[0].text}")
    print("\n")
    
    
execution_results_eval_agent = Agent(
    name="execution_results_eval_agent",
    model=LiteLlm(model=MODEL_ID),
    description="Execution results evaluator of the two SQL queries",
    instruction="""
    You are an specialized data quality AI and expert SQL evaluator. Your task is to determine whether two SQL query execution results (datasets) are identical (contains the same data) or not identical by comparing the two result sets, A and B.
    
    Context:
    You will be provided with the two SQL queries (Ground Truth SQL Query and Predicted SQL Query) and their corresponding result sets from execution of the respective queries. And based on your understanding of two results comaprison, you need to classify them as either `Identical` or `Not Identical`. Two result sets are considered identical if they contain the same records, regardless of the order of rows or minor formatting differences.
    - Identical: The two result sets contain the same records, even if they are in a different order or have minor formatting differences.
    - Not Identical: The two result sets differ in content, meaning there are records present in one set that are absent in the other, or there are discrepancies in the data values.
    
    Ground Truth SQL Query: {ground_truth_sql}
    Predicted SQL Query: {predicted_sql}
    
    Ground Truth Result Set: {ground_truth_data}
    Predicted Result Set: {predicted_data}
    
    Instructions:
    - Row Order: Ignore it. Treat the results as unordered sets.
    - Column Order: Ignore it. Compare data by column name, not position.
    - Column Names: They MUST match. A column named employee_id is different from emp_id.
    - NULLs: Consider all NULL values to be equal to each other.
    - Duplicates: [A, A, B] is different from [A, B]. Not identical.
    - Data Types: 
        - Strings vs numbers → "123" and 123 are equivalent if they represent the same value.
        - Floating point numbers → treat values as equal if they differ within a tiny tolerance.
        - Dates: Different formats representing the same date are equal. 2023-10-05, 10/05/2023, and October 5, 2023 are all equal.
    - Case Sensitivity: For this task, consider all string comparisons to be case-sensitive. The string 'Apple' is different from 'apple'.
        
    <examples>
    Example 1:
    Result Set A: [ {"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"} ]
    Result Set B: [ {"name": "Bob", "id": 2}, {"name": "Alice", "id": 1} ]
    Answer: Identical
    Reasoning: The result sets are logically identical. The only differences are the order of the rows and the order of the columns within each row, both of which are explicitly ignored by the comparison rules. Both sets contain the same two rows of data when compared by column name and logical value.
    </examples>
    
    - First, reason step by step before giving your final answer.
    
    {agent_input}
    
    Output:
    sql_equivalence_value: A  value indicating if the two result sets are Identical or not. Return only one value. Possible values: `Identical`, `Not Identical`.
    model_reason: Provide a detailed reasoning for why you assigned the sql_equivalence_value.
    """,
    output_key="execution_results_equivalence",
    output_schema=ExecutionResultsEquivalence,
    before_agent_callback=before_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
