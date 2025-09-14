# Text-to-SQL Evaluation

## Before running
Prepare a eval_set.xlsx file with following column names:
- gt_sql (Grount Truth SQL Query)
- pred_sql (Predicted SQL Query)

## Content matching based evaluation
to run the the semantic sql matcher agent 
```python
python -m evaluation.main
```

## Execution based evaluation
to run the the execution results eval agent
```python
python -m evaluation.main2
```