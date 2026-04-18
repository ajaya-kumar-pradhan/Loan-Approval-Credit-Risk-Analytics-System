import mysql.connector
import pandas as pd
import json

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Ajaya1@2&3",
    "database": "loan_default_db",
    "charset":  "utf8mb4",
}

def run_query(query, name):
    conn = mysql.connector.connect(**DB_CONFIG)
    # Using pandas read_sql to execute and get dataframes
    df = pd.read_sql(query, conn)
    conn.close()
    # Convert dataframe to list of dicts for JSON
    return {
        "name": name,
        "sql": query.strip(),
        "results": df.to_dict(orient="records")
    }

queries = [
    # 1. Executive Summary
    ("""
    SELECT 
        COUNT(*)                                                AS Total_Apps,
        SUM(CASE WHEN is_bad_loan = 0 THEN 1 ELSE 0 END)        AS Good_Loans,
        SUM(CASE WHEN is_bad_loan = 1 THEN 1 ELSE 0 END)        AS Bad_Loans,
        ROUND(SUM(CASE WHEN is_bad_loan = 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Approval_Rate_Pct,
        ROUND(AVG(loan_amount), 0)                              AS Avg_Loan_Amt,
        ROUND(SUM(loan_amount) / 1000000.0, 2)                  AS Portfolio_M
    FROM fact_loan;
    """, "Executive Portfolio Summary"),

    # 2. Performance by Grade
    ("""
    SELECT 
        g.grade AS Grade,
        g.grade_label AS Label,
        COUNT(f.loan_id) AS Loans,
        ROUND(AVG(f.interest_rate), 2) AS Avg_Rate_Pct,
        ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
    FROM fact_loan f
    JOIN dim_loan_grade g ON f.grade_key = g.grade_key
    GROUP BY g.grade, g.grade_label
    ORDER BY g.grade;
    """, "Default Rate by Credit Grade"),

    # 3. Regional Performance
    ("""
    SELECT 
        dp.region AS Region,
        COUNT(fl.loan_id) AS Apps,
        ROUND(SUM(fl.loan_amount)/1000000.0, 2) AS Principal_M,
        ROUND(SUM(CASE WHEN fl.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
    FROM fact_loan fl
    JOIN dim_property dp ON fl.property_key = dp.property_key
    GROUP BY dp.region
    ORDER BY Default_Rate_Pct DESC;
    """, "Regional Risk Performance"),

    # 4. Purpose Risk
    ("""
    SELECT 
        p.purpose AS Purpose,
        COUNT(f.loan_id) AS Count,
        ROUND(AVG(f.interest_rate), 2) AS Avg_Rate,
        ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
    FROM fact_loan f
    JOIN dim_purpose p ON f.purpose_key = p.purpose_key
    GROUP BY p.purpose
    ORDER BY Default_Rate_Pct DESC
    LIMIT 10;
    """, "Top 10 High-Risk Loan Purposes"),

    # 5. Income Band Analysis
    ("""
    SELECT 
        c.income_band AS Income_Band,
        COUNT(f.loan_id) AS Loans,
        ROUND(AVG(f.loan_amount), 0) AS Avg_Loan,
        ROUND(AVG(f.lti_ratio), 2) AS Avg_LTI,
        ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
    FROM fact_loan f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.income_band
    ORDER BY Default_Rate_Pct DESC;
    """, "Affordability by Income Band")
]

results = []
for q_sql, q_name in queries:
    print(f"Executing: {q_name}...")
    try:
        results.append(run_query(q_sql, q_name))
    except Exception as e:
        print(f"Error in {q_name}: {e}")

with open("sql_results.json", "w") as f:
    json.dump(results, f)
print("SUCCESS: Results saved to sql_results.json")
