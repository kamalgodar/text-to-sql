import uuid
import yaml
import json
import pandas as pd
from google.adk.runners import Runner


def load_config(config_path="evaluation/config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    
    
def save_results_to_excel(outputs, output_file):
    """Save collected results into an Excel file."""
    results_df = pd.DataFrame(outputs)
    results_df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")
    
    
def save_results_to_json(metrics, output_file):
    """Save computed metrics dictionary to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to {output_file}")
    
    
async def create_session(session_service, app_name="EvaluationApp", user_id="user1", initial_state={}):
    """Create and return a new session."""
    SESSION_ID = str(uuid.uuid4())
    stateful_session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=SESSION_ID,
        state=initial_state
    )
    print("CREATED NEW SESSION:")
    print(f"\tSession ID: {SESSION_ID}")
    return stateful_session, SESSION_ID


def build_runner(agent, app_name, session_service):
    """Initialize and return a Runner instance."""
    return Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )
    
    
def compute_metrics(outputs):
    semantic_equivalent_count = len([x for x in outputs if x['semantic_equivalence'] == 'Equivalent'])
    execution_identical_count = len([x for x in outputs if x['execution_equivalence'] == 'Identical'])
    overall_count = len([x for x in outputs if x['semantic_equivalence'] == 'Equivalent' and x['execution_equivalence'] == 'Identical'])

    total_queries = len(outputs)

    semantic_accuracy = semantic_equivalent_count / total_queries if total_queries > 0 else 0
    execution_accuracy = execution_identical_count / total_queries if total_queries > 0 else 0
    overall_accuracy = overall_count / total_queries if total_queries > 0 else 0
    
    print(f"Semantic SQL Matcher Accuracy: {semantic_accuracy}")
    print(f"Execution SQL Matcher Accuracy: {execution_accuracy}")
    print(f"Overall SQL Matcher Accuracy: {overall_accuracy}")
    
    metrics = {
        "total_queries": total_queries,
        "correct_semantic_equivalent_count": semantic_equivalent_count,
        "correct_execution_identical_count": execution_identical_count,
        "correct_semantic_and_execution_count": overall_count,
        "semantic_accuracy": semantic_accuracy,
        "execution_accuracy": execution_accuracy,
        "overall_accuracy": overall_accuracy
    }

    return metrics