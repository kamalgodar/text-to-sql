from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from src.configs.settings import settings
from .response_schema import SemanticSQLEquivalence
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types
from typing import Optional

MODEL_ID = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"
    
    
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    print("Before Agent Callback:")
    callback_context.state["agent_input"] = "Identify if the two SQL queries are semantically equivalent or not."
    
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
    
    
semantic_sql_matcher_agent = Agent(
    name="semantic_sql_matcher_agent",
    model=LiteLlm(model=MODEL_ID),
    description="Semantic matcher of the two SQL queries",
    instruction="""
    You are an expert SQL evaluator. Your task is to determine if two SQL queries are **semantically equivalent**, meaning they will always produce the same logical result (given the same schema and data), even if written differently. Your judgment must be based on rigorous logic and hold true for any possible database state.
    
    Context:
    You will be provided with the two SQL queries (Ground Truth SQL Query and Predicted SQL Query). And based on your understanding of SQL semantics, you need to classify them as either `Equivalent` or `Not Equivalent` or `Unsure`. 
    - Equivalent: If two queries produce the same multiset of rows for any possible valid database instance, even if they look different, they are semantically equivalent.
    - Not Equivalent: If two queries cannot produce the same multiset of rows, they are not semantically equivalent.
    - Unsure: If you are doubtful on whether they are semantically equivalent or not and need the help of dataset after execution of sql queries, classify them as Unsure.
    
    Ground Truth SQL Query: {ground_truth_sql}
    Predicted SQL Query: {predicted_sql}
    
    Instructions:
    - **STRICTLY IGNORE** the Ground Truth Data and Predicted Data while examining the semantic equivalence of Ground Truth SQL query and predicted SQL query
    - **STRICTLY IGNORE** the effect of LIMIT, ORDER BY and ALIAS names present in SQL Queries while comparing the semantic equivalence of two SQL queries as they do not change the logical meaning of the queries
    - Break down each query into its core components and compare them logically, not syntactically.
    
    - **Schema Compatibility Check:** 
        -First, verify that the two queries project a compatible set of columns (i.e., the same number of columns with logically comparable data types). If they do not, they are immediately Not Equivalent. 
        - Ignore the order of SELECT columns. The order of columns does not change semantic meaning for the purpose of data content.
        
    - **Ignore these syntactic differences:** 
        - Table/column aliases
        - order of predicates in `WHERE`/`ON` 
        - order of tables in `FROM` for `INNER JOIN`
        
    - **Pay extreme attention to these semantic differences:**
        - `INNER JOIN` vs `LEFT JOIN` vs `RIGHT JOIN` vs `FULL OUTER JOIN`
        - `UNION` vs `UNION ALL`
        - `EXCEPT` vs `NOT IN`
        - `INTERSECT` vs `INNER JOIN`
        - `WHERE` vs `HAVING`
        - `NULL` handling (e.g., `IS NULL`, `IS NOT NULL`, `NULL` in joins)
        - `DISTINCT` keyword
        - Aggregation functions and `GROUP BY` clauses
        
    - **Complex Queries:** For queries involving subqueries, CTEs, or nested structures, ensure you analyze the logical flow and data transformations at each level.
    
    - First, reason step by step before giving your final answer.
    
    {agent_input}
    
    Output:
    sql_equivalence_value: A  value indicating if the two SQL queries are semantically equivalent or not. Return only one value. Possible values: `Equivalent`, `Not Equivalent`, `Unsure`.
    model_reason: Provide a detailed reasoning for why you assigned the sql_equivalence_value.
    
    """,
    output_key="semantic_sql_equivalence",
    output_schema=SemanticSQLEquivalence,
    before_agent_callback=before_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
