# text-to-sql

### Creating a virtual environment:
```bash
python --version # > 3.12
python -m venv .venv
source .venv/bin/activate # Linux
.venv/Scripts/activate # Windows
```

### Installation:
```bash
pip install -r requirements.txt
```

### Running the application:
```bash
python app.py
```

### Running the evaluation pipeline:
```bash
python -m evaluation.run_evaluation
```

Sample Example of Output:

User Query: Which Employee Role Name has the highest number of discounts? Plot a count of these by Role?

SQL Query: SELECT employee_role_name, COUNT(reduction_amt) AS discount_count FROM combined_order_data WHERE reduction_amt IS NOT NULL GROUP BY employee_role_name ORDER BY discount_count DESC LIMIT 19

Plot:
![Bar Plot](./barplot.png)
