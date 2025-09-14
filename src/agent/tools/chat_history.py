from langchain_core.messages import ToolMessage, HumanMessage

def get_chat_history(messages):
    chat_log = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            chat_log.append(f"\n\nUser: {msg.content}")
        elif isinstance(msg, ToolMessage):
            label = "Data Extracted" if msg.name == 'sql_db_query' else "SQL Query"
            chat_log.append(f"\n{label}:\n{msg.content}")
    result = ''.join(chat_log)
    return result


