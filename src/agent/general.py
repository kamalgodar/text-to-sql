from src.schemas.chat_response import ResponseSchemaGeneral, ResponseSchemaMod
class GeneralReactAgent:
    """React Agent specifically for handling general queries"""
    
    def __init__(self, llm):
        self.llm = llm

    def execute(self, query):
        """Execute general query response and return ResponseSchemaGeneral"""
        # Use structured output for consistent response
        structured_llm = self.llm.with_structured_output(ResponseSchemaGeneral)
        
        try:
            # Simple prompt for general queries
            prompt = f"User asked: {query}\n Your answer should be: I can only answer from the database. Feel free to ask information from the database."
            response = structured_llm.invoke([{"role": "user", "content": prompt}])
            return response
        except Exception as e:
            print(f"General agent error: {e}")
            return ResponseSchemaGeneral(
                sql_query='',
                suggested_visualization_type=[],
                answer="I can only answer from the database related query please ask about db",
                model_error = True
            )
        