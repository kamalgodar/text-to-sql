from pydantic import BaseModel, Field

class ExecutionResultsEquivalence(BaseModel):
    execution_data_equivalence_value: str = Field(
        ..., 
        description="If the execution results of two SQL queries (their corresponding data) are identical or not. Identical --> The two result sets contain the same records,  Not Identical --> The two result sets differ in content"
    )
    model_reason: str = Field(
        ..., 
        description="Detailed reasoning for why the language model assigned the execution_data_equivalence_value"
    )
    
    