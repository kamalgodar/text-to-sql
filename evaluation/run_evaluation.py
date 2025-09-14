import uuid
import asyncio
import os
import pandas as pd
import time
from google.adk.sessions import InMemorySessionService
from google.genai import types
from evaluation.agent.sequential_agent import evaluation_pipeline_agent
from src.configs.settings import settings
from src.db.db import fetch_data_from_db
from evaluation.utils.utils import save_results_to_excel, create_session, build_runner, load_config, save_results_to_json, compute_metrics
from google.adk.events import Event, EventActions

config = load_config()

os.environ["AWS_ACCESS_KEY_ID"] = settings.BEDROCK_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = settings.BEDROCK_SECRET_ACCESS_KEY
os.environ["AWS_REGION_NAME"] = settings.BEDROCK_REGION

    
async def run_sql_equivalence_evaluation(runner, APP_NAME, USER_ID, SESSION_ID, session_service, df):
    outputs = []
    for idx, row in df.iterrows():
        print(f"\n\n ---------------------------------------------Row: {idx}----------------------------------------------------------")
        
        gt_sql, pred_sql = row["gt_sql"], row["pred_sql"]
        
        try:
            gt_data = fetch_data_from_db(gt_sql)
            length_of_gt_data = len(gt_data) if gt_data is not None else 0
        except Exception as e:
            print(f"Error executing ground truth SQL: {str(e)}")
            gt_data = None
            length_of_gt_data = "Error fetching data"
            
        try:
            pred_data = fetch_data_from_db(pred_sql)
            length_of_pred_data = len(pred_data) if pred_data is not None else 0
        except Exception as e:
            print(f"Error executing predicted SQL: {str(e)}")
            pred_data = None
            length_of_pred_data = "Error fetching data"
        
        len_reason_msg = ""
        if isinstance(length_of_gt_data, int) and isinstance(length_of_pred_data, int):
            if length_of_gt_data != length_of_pred_data:
                len_reason_msg = f"Data length mismatch: GT Data Length = {length_of_gt_data}, Pred Data Length = {length_of_pred_data}"
                print(len_reason_msg)
        else:
            len_reason_msg = f"Error comparing data lengths: GT={length_of_gt_data}, Pred={length_of_pred_data}"
            print(len_reason_msg)
            
        user_input = "Are the given two SQL queries equivalent and data from execution of these two SQL queries identical?"
        
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )
        
        print(f"Ground Truth SQL: {gt_sql}")
        print(f"Ground Truth Data: {gt_data}")
        print("\n")
        print(f"Predicted SQL: {pred_sql}")
        print(f"Predicted Data: {pred_data}")

        
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        current_time = time.time()
        state_changes = {
            "ground_truth_sql": gt_sql,
            "predicted_sql": pred_sql,
            "ground_truth_data": str(gt_data),
            "predicted_data": str(pred_data),
            }
        actions_with_update = EventActions(state_delta=state_changes)
        system_event = Event(
            invocation_id=str(uuid.uuid4()),
            author="system",
            actions=actions_with_update,
            timestamp=current_time
        )
        await session_service.append_event(session, system_event)

        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=new_message,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = event.content.parts[0].text
                        print(f"\nSQL Equivalance: {response_text}\n")
                        
        except Exception as e:
            print(f"Error during runner execution: {str(e)}")
            response_text = "Error in evaluation"
            
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        semantic_equivalence_value = session.state.get("semantic_sql_equivalence", {}).get("sql_equivalence_value", "No value set")
        semantic_model_reason = session.state.get("semantic_sql_equivalence", {}).get("model_reason", "No reason provided")
        
        execution_equivalence_value = session.state.get("execution_results_equivalence", {}).get("execution_data_equivalence_value", "No value set")
        execution_model_reason = session.state.get("execution_results_equivalence", {}).get("model_reason", "No reason provided")
        execution_final_model_reason = len_reason_msg + "" + execution_model_reason if len_reason_msg else execution_model_reason
        
        outputs.append(
            {"gt_sql": gt_sql, "pred_sql": pred_sql, "semantic_equivalence": semantic_equivalence_value, "semantic_model_reason": semantic_model_reason, "gt_data": gt_data, "pred_data": pred_data, "execution_equivalence": execution_equivalence_value, "execution_model_reason": execution_final_model_reason}
        )    
    return outputs


async def main():
    df = pd.read_excel(config["evaluation"]["eval_file"], sheet_name="Sheet4")

    session_service = InMemorySessionService()
    
    APP_NAME = config["evaluation"]["app_name"]
    USER_ID = config["evaluation"]["user_id"]
    
    stateful_session, session_id = await create_session(session_service, APP_NAME, USER_ID)
    runner = build_runner(evaluation_pipeline_agent, APP_NAME, session_service)
    outputs = await run_sql_equivalence_evaluation(runner, APP_NAME, USER_ID, session_id, session_service, df)
    
    eval_metrics = compute_metrics(outputs)
    breakpoint()
    save_results_to_json(eval_metrics, config["evaluation"]["output_eval_pipeline_metrics_file"])
    save_results_to_excel(outputs, config["evaluation"]["output_eval_pipeline_results_file"])


if __name__ == "__main__":
    asyncio.run(main())
