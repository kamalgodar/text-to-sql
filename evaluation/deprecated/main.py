import uuid
import asyncio
import os
import pandas as pd
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from evaluation.semantic_sql_matcher_agent import semantic_sql_matcher_agent
from src.configs.settings import settings
from evaluation.utils.utils import save_results_to_excel, create_session, build_runner, load_config

config = load_config()

os.environ["AWS_ACCESS_KEY_ID"] = settings.BEDROCK_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.BEDROCK_SECRET_ACCESS_KEY
os.environ["AWS_REGION_NAME"] = settings.BEDROCK_REGION

    
async def run_semantic_sql_equivalence_evaluation(runner, APP_NAME, USER_ID, SESSION_ID, session_service, df):
    outputs = []
    for idx, row in df.iterrows():
        print(f"\n ---------------------------------------------Row: {idx}----------------------------------------------------------")
        
        gt_sql, pred_sql = row["gt_sql"], row["pred_sql"]
        user_input = f"Are these two SQL queries equivalent?\n\nQuery 1: {gt_sql}\nQuery 2: {pred_sql}"
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )
        
        print(f"Grond Truth SQL: {gt_sql}")
        print(f"Predicted SQL: {pred_sql}")

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    
                    print(f"SQL Equivalance: {response_text}\n")
                    print(f"------------------------------------------------------------------------------------------------------------------\n\n")
        
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        equivalence_value = session.state.get("semantic_sql_equivalence", {}).get("sql_equivalence_value", "No value set")
        model_reason = session.state.get("semantic_sql_equivalence", {}).get("model_reason", "No reason provided")
        outputs.append(
            {"gt_sql": gt_sql, "pred_sql": pred_sql, "sql_equivalence": equivalence_value, "model_reason": model_reason}
        )    
    return outputs
    
    
async def main():
    df = pd.read_excel(config["evaluation"]["eval_file"], sheet_name="Sheet1") 

    session_service = InMemorySessionService()
    
    APP_NAME = config["evaluation"]["app_name"]
    USER_ID = config["evaluation"]["user_id"]
    
    stateful_session, session_id = await create_session(session_service, APP_NAME, USER_ID)
    runner = build_runner(semantic_sql_matcher_agent, APP_NAME, session_service)
    outputs = await run_semantic_sql_equivalence_evaluation(runner, APP_NAME, USER_ID, session_id, session_service, df)

    equivalent_count = len([x for x in outputs if x['sql_equivalence'] == 'Equivalent'])
    total_queries = len(outputs)
    accuracy = equivalent_count / total_queries if total_queries > 0 else 0
    print(f"Semantic SQL Matcher Accuracy: {accuracy}")
    
    save_results_to_excel(outputs, config["evaluation"]["semantic_sql_equivalence_result_file"])


if __name__ == "__main__":
    asyncio.run(main())
