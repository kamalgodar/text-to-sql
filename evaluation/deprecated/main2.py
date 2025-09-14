import uuid
import asyncio
import os
import pandas as pd
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from evaluation.execution_results_eval_agent import execution_results_eval_agent
from src.db.db import fetch_data_from_db
from src.configs.settings import settings
from evaluation.utils.utils import save_results_to_excel, create_session, build_runner, load_config

config = load_config()

os.environ["AWS_ACCESS_KEY_ID"] = settings.BEDROCK_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.BEDROCK_SECRET_ACCESS_KEY
os.environ["AWS_REGION_NAME"] = settings.BEDROCK_REGION


def get_data_using_sql(query: str):
    try:
        data = fetch_data_from_db(query)
        return data
    except Exception as e:
        print(f"Error fetching data for query: {query}\nError: {e}")
        return None
    
    
async def run_execution_results_equivalence_evaluation(runner, APP_NAME, USER_ID, SESSION_ID, session_service, df):
    outputs = []
    for idx, row in df.iterrows():
        print(f"\n ---------------------------------------------Row: {idx}----------------------------------------------------------")
        
        gt_sql, pred_sql = row["gt_sql"], row["pred_sql"]
        gt_data = get_data_using_sql(gt_sql)
        pred_data = get_data_using_sql(pred_sql)
        length_of_gt_data = len(gt_data) if gt_data else "Error fetching data"
        length_of_pred_data = len(pred_data) if pred_data else "Error fetching data"
        
        print(f"GT SQL: {gt_sql}")
        print(f"GT Data: {gt_data}")
        print(f"Length of GT Data: {len(gt_data) if gt_data else 'Error fetching data'}")
        print(f"\n")
        print(f"Pred SQL: {pred_sql}")
        print(f"Pred Data: {pred_data}")
        print(f"Length of Pred Data: {len(pred_data) if pred_data else 'Error fetching data'}")
        
        
        len_reason_msg = ""
        if length_of_gt_data != length_of_pred_data:
            len_reason_msg = f"Data length mismatch: GT Data Length = {length_of_gt_data}, Pred Data Length = {length_of_pred_data}"
            print(len_reason_msg)
        
        print(f"Processing row {idx}")
        user_input = f"Are these following data from execution of two SQL queries identical?\n\nQuery 1: {gt_sql}\nQuery 2: {pred_data}\n\nData 1: {gt_data}\nData 2: {pred_data}."
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )

        response_text = None

        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                    print(f"Equivalence value: {response_text}")
                    print(f"------------------------------------------------------------------------------------------------------------------\n\n")
    
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        equivalence_value = session.state.get("execution_results_equivalence", {}).get("execution_data_equivalence_value", "No value set")
        model_reason = session.state.get("execution_results_equivalence", {}).get("model_reason", "No reason provided")
        reason_msg = len_reason_msg + " " + model_reason if len_reason_msg else model_reason
        
        outputs.append(
            {"gt_sql": gt_sql, "pred_sql": pred_sql, "gt_data": gt_data, "pred_data": pred_data, "equivalence_value": equivalence_value, "reason": reason_msg}
        )
        
    return outputs
    
    
async def main():
    df = pd.read_excel(config["evaluation"]["eval_file"], sheet_name="Sheet1") 

    session_service = InMemorySessionService()

    APP_NAME = config["evaluation"]["app_name"]
    USER_ID = config["evaluation"]["user_id"]

    stateful_session, session_id = await create_session(session_service, APP_NAME, USER_ID)
    runner = build_runner(execution_results_eval_agent, APP_NAME, session_service)
    outputs = await run_execution_results_equivalence_evaluation(runner, APP_NAME, USER_ID, session_id, session_service, df)

    equivalent_count = len([x for x in outputs if x["equivalence_value"] == "Identical"])
    total_queries = len(outputs)
    accuracy = equivalent_count / total_queries if total_queries > 0 else 0
    print(f"Execution Results Equivalence Accuracy: {accuracy}")
        
    save_results_to_excel(outputs, config["evaluation"]["execution_results_equivalence_result_file"])

    
if __name__ == "__main__":
    asyncio.run(main())
