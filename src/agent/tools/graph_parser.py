from src.agent.tools.graph_analyzer import PromptBuilder, ChartSuggester
from src.models.graph_models import Table, LineChartSuggestion, BarChartSuggestion, PieChartSuggestion

schema = {
    "line": LineChartSuggestion, 
    'bar': BarChartSuggestion,
    'pie': PieChartSuggestion,
    'table': Table
    }

def recommend_graph_object(data_extracted_from_database, output, llm, chat_history, latest_user_query, query):
    column_names = list(data_extracted_from_database[0].keys())
    print(column_names)
    results = []
    graph_types = set(output.suggested_visualization_type) 
    agent_response_summary = output.answer
    supported_types = {"line", "bar", "pie", 'table'}
    valid_graph_types = graph_types & supported_types
    print(f"{valid_graph_types=}")
    for g_type in valid_graph_types:
        print(f"Graph type Detected: {g_type}")
        if g_type == "table" or len(data_extracted_from_database) == 1:
            args = Table(graph_type='table', args=None)
            results.append(args)
            continue
        elif g_type in supported_types:
            prompt = PromptBuilder(
            data_sample=data_extracted_from_database,
            sql_query=query,
            graph_type=g_type,
            chat_history=chat_history,
            latest_user_query=latest_user_query,
            column_names=column_names,
            agent_response_summary = agent_response_summary,
            ).build()
            suggester = ChartSuggester(llm=llm)

            args = suggester.suggest_chart(prompt=prompt, schema=schema.get(g_type))
            
            if args:
                results.append({"graph_type": g_type , "args": args})
    return results


