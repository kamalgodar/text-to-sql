from google.adk.agents import SequentialAgent
from evaluation.semantic_sql_matcher_agent import semantic_sql_matcher_agent
from evaluation.execution_results_eval_agent import execution_results_eval_agent

evaluation_pipeline_agent =SequentialAgent(
    name="EvaluationPipelineAgent", 
    sub_agents=[semantic_sql_matcher_agent, execution_results_eval_agent],
    description="executes a sequence of semantic sql matcher agent and execution results eval agent"
    )
