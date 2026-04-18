-- =============================================================================
-- LOAN DEFAULT PREDICTION & CREDIT RISK ANALYTICS
-- Advanced Business Analysis Queries (MySQL 8.0+)
-- =============================================================================
-- These queries answer critical business questions regarding portfolio health,
-- risk concentration, and lending strategy.
-- =============================================================================

-- QUESTION 01: EXECUTIVE KPI DASHBOARD
-- Total volume, approval rate, default rate, and portfolio value.
SELECT
    COUNT(*)                                                            AS Total_Apps,
    SUM(CASE WHEN is_bad_loan = 0 THEN 1 ELSE 0 END)                    AS Good_Loans,
    SUM(CASE WHEN is_bad_loan = 1 THEN 1 ELSE 0 END)                    AS Bad_Loans,
    ROUND(SUM(CASE WHEN is_bad_loan = 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Approval_Rate_Pct,
    ROUND(SUM(CASE WHEN is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    ROUND(SUM(loan_amount) / 1000000.0, 2)                              AS Total_Portfolio_M,
    ROUND(AVG(loan_amount), 0)                                          AS Avg_Loan_Amt,
    ROUND(AVG(interest_rate), 2)                                        AS Avg_Rate_Pct
FROM fact_loan;


-- QUESTION 02: CREDIT GRADE RISK-PROFILING
-- Does our internal risk grading (A-G) align with actual default outcomes?
SELECT
    g.grade,
    g.grade_label,
    COUNT(f.loan_id)                                                    AS Total_Loans,
    ROUND(AVG(f.interest_rate), 2)                                      AS Avg_Rate,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Actual_Default_Rate_Pct,
    ROUND(AVG(f.dti), 2)                                                AS Avg_DTI
FROM fact_loan f
JOIN dim_loan_grade g ON f.grade_key = g.grade_key
GROUP BY g.grade, g.grade_label
ORDER BY g.grade;


-- QUESTION 03: REGIONAL RISK CONCENTRATION
-- Which geographic regions present the highest default risk for the bank?
SELECT
    p.region,
    COUNT(f.loan_id)                                                    AS Apps,
    ROUND(SUM(f.loan_amount) / 1000000.0, 2)                            AS Principal_M,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    RANK() OVER (ORDER BY SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) DESC) AS Risk_Rank
FROM fact_loan f
JOIN dim_property p ON f.property_key = p.property_key
GROUP BY p.region
ORDER BY Default_Rate_Pct DESC;


-- QUESTION 04: "DANGER ZONE" ANALYSIS (HIGH DTI + HIGH RATE)
-- Identifying the segment responsible for disproportionate defaults.
-- Criteria: DTI > 30% and Interest Rate > 15%
SELECT
    CASE WHEN dti > 30 AND interest_rate > 15 THEN 'High Risk Danger Zone' ELSE 'Standard Segment' END AS Risk_Segment,
    COUNT(*) AS Loan_Count,
    ROUND(SUM(CASE WHEN is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    ROUND(AVG(loan_amount), 0) AS Avg_Loan
FROM fact_loan
GROUP BY Risk_Segment;


-- QUESTION 05: INCOME AFFORDABILITY STRESS TEST
-- How does borrower income category impact the likelihood of default?
SELECT
    c.income_category,
    COUNT(f.loan_id)                                                    AS Count,
    ROUND(AVG(f.loan_amount), 0)                                        AS Avg_Loan,
    ROUND(AVG(f.installment_pct_income), 2)                              AS Avg_Payment_Burden_Pct,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
FROM fact_loan f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.income_category
ORDER BY Default_Rate_Pct DESC;


-- QUESTION 06: LOAN PURPOSE vs PERFORMANCE
-- Which loan purposes are the "safest" for our portfolio?
SELECT
    p.purpose,
    COUNT(f.loan_id)                                                    AS Count,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    ROUND(AVG(f.interest_rate), 2)                                      AS Avg_Rate
FROM fact_loan f
JOIN dim_purpose p ON f.purpose_key = p.purpose_key
GROUP BY p.purpose
ORDER BY Default_Rate_Pct ASC;


-- QUESTION 07: YEAR-OVER-YEAR QUALITY TREND
-- Tracking if our portfolio quality is improving or deteriorating annually.
SELECT
    d.issue_year,
    COUNT(f.loan_id)                                                    AS Apps,
    ROUND(SUM(f.loan_amount) / 1000000.0, 2)                            AS Principal_M,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    LAG(ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2)) OVER (ORDER BY d.issue_year) AS Prev_Year_Rate,
    ROUND(
        (SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100) - 
        LAG(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100) OVER (ORDER BY d.issue_year)
    , 2) AS YoY_Change_Percentage_Points
FROM fact_loan f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.issue_year
ORDER BY d.issue_year;


-- QUESTION 08: HOME OWNERSHIP vs RISK
-- Is there a measurable difference in risk between renters and homeowners?
SELECT
    c.home_ownership,
    COUNT(f.loan_id)                                                    AS Total_Loans,
    ROUND(SUM(CASE WHEN f.is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct,
    ROUND(AVG(f.loan_amount), 0)                                        AS Avg_Loan
FROM fact_loan f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.home_ownership
ORDER BY Default_Rate_Pct DESC;


-- QUESTION 09: LOAN TERM IMPACT
-- Comparison of 36-month vs 60-month loan performance.
SELECT
    loan_term_months,
    COUNT(*) AS Count,
    ROUND(AVG(interest_rate), 2) AS Avg_Rate,
    ROUND(SUM(CASE WHEN is_bad_loan = 1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS Default_Rate_Pct
FROM fact_loan
GROUP BY loan_term_months;


-- QUESTION 10: BOTTOM 1% "TOXIC" LOANS (manual review queue)
-- Identifying specific loans with extreme DTI and Interest Rates for immediate review.
SELECT
    loan_id,
    loan_amount,
    interest_rate,
    dti,
    risk_category,
    loan_condition
FROM fact_loan
WHERE dti > 35 AND interest_rate > 22
ORDER BY dti DESC
LIMIT 20;
