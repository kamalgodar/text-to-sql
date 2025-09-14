from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class LineChartSuggestion(BaseModel):
    title: str = Field(..., description="Chart title")
    x_axis: str = Field(..., description="X-axis column name")
    y_axis: str = Field(..., description="Y-axis column name")
    line_type: Literal["single", "multi-line"] = Field(default="single", description="multi-line only if group_by is not null or None.")
    group_by: Optional[str] = Field(None, description="Split column")
    linestyle: Optional[Literal["solid", "dashed"]] = Field("solid", description="Line style")
    marker: str = Field("o", description="Point marker")
    xlabel: str = Field(..., description="X-axis label")
    ylabel: str = Field(..., description="Y-axis label")


class BarChartSuggestion(BaseModel):
    title: str = Field(..., description="Chart title")
    x_axis: str = Field(..., description="X-axis column name")
    y_axis: str = Field(..., description="Y-axis column name")
    bar_type: Literal["single", "grouped", "stacked"] = Field(default="single", description="grouped or stacked only if group_by is not null or None.")
    group_by: Optional[str] = Field(None, description="Split column")
    xlabel: str = Field(..., description="X-axis title")
    ylabel: str = Field(..., description="Y-axis title")


class PieChartSuggestion(BaseModel):
    title: str = Field(..., description="Chart title")
    label: str = Field(..., description="Categorical column name")
    value: str = Field(..., description="Value column name or percentage or count")
    group_by: Optional[str] = Field(None, description="Split column")
    legend_title: Optional[str] = Field(None, description="Legend title")


class Table(BaseModel):
    graph_type: Literal['table'] = "table"
    args: None