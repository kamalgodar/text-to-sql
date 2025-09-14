from pydantic import BaseModel, Field

class SemanticSQLEquivalence(BaseModel):
    sql_equivalence_value: str = Field(
        ..., 
        description="If two SQL queries are semantically equivalent or not. Possible values: `Equivalent`, `Not Equivalent`, `Unsure`"
    )
    model_reason: str = Field(
        ..., 
        description="Detailed reasoning for why the language model assigned the sql_equivalence_value"
    )