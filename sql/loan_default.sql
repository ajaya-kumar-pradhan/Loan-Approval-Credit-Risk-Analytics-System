use loan_default_db;

-- =============================================================================
-- LOAN DEFAULT PREDICTION & CREDIT RISK ANALYTICS
-- Advanced Business Analysis Queries (MySQL 8.0+)
-- =============================================================================
-- These queries answer critical business questions regarding portfolio health,
-- risk concentration, and lending strategy.
-- =============================================================================

-- QUESTION 01: EXECUTIVE KPI DASHBOARD
-- Total volume, approval rate, default rate, and portfolio value.
WITH base AS (
    SELECT 
        loan_amount,
        interest_rate,
        CASE WHEN is_bad_loan = 1 THEN 1 ELSE 0 END AS bad_loan,
        CASE WHEN is_bad_loan = 0 THEN 1 ELSE 0 END AS good_loan
    FROM fact_loan
)

SELECT
    COUNT(*) AS total_apps,
    SUM(good_loan) AS good_loans,
    SUM(bad_loan) AS bad_loans,
    ROUND(SUM(good_loan) * 100.0 / NULLIF(COUNT(*), 0), 2) AS approval_rate_pct,
    ROUND(SUM(bad_loan) * 100.0 / NULLIF(COUNT(*), 0), 2) AS default_rate_pct,
    ROUND(SUM(loan_amount) / 1000000.0, 2) AS total_portfolio_m,
    ROUND(AVG(loan_amount), 0) AS avg_loan_amt,
    ROUND(AVG(interest_rate), 2) AS avg_rate_pct
FROM base;

-- QUESTION 02: CREDIT GRADE RISK-PROFILING
-- Does our internal risk grading (A-G) align with actual default outcomes?
SELECT
    g.grade,
    g.grade_label,
    COUNT(f.loan_id) AS total_loans,
    ROUND(AVG(f.interest_rate), 2) AS avg_rate,
    ROUND(SUM(f.is_bad_loan) * 100.0 / NULLIF(COUNT(f.loan_id), 0), 2) AS actual_default_rate_pct,
    ROUND(AVG(f.dti), 2) AS avg_dti
FROM fact_loan f
JOIN dim_loan_grade g 
    ON f.grade_key = g.grade_key
GROUP BY g.grade, g.grade_label
ORDER BY g.grade;

-- QUESTION 03: REGIONAL RISK CONCENTRATION
-- Which geographic regions present the highest default risk for the bank?
WITH region_stats AS (
    SELECT
        p.region,
        COUNT(f.loan_id) AS apps,
        SUM(f.loan_amount) AS total_amount,
        SUM(f.is_bad_loan) AS bad_loans
    FROM fact_loan f
    JOIN dim_property p 
        ON f.property_key = p.property_key
    GROUP BY p.region
)

SELECT
    region,
    apps,
    ROUND(total_amount / 1000000.0, 2) AS principal_m,
    ROUND(bad_loans * 100.0 / NULLIF(apps, 0), 2) AS default_rate_pct,
    RANK() OVER (ORDER BY bad_loans * 1.0 / apps DESC) AS risk_rank
FROM region_stats
ORDER BY default_rate_pct DESC;


-- QUESTION 04: "DANGER ZONE" ANALYSIS (HIGH DTI + HIGH RATE)
-- Identifying the segment responsible for disproportionate defaults.
-- Criteria: DTI > 30% and Interest Rate > 15%
SELECT
    CASE 
        WHEN dti > 30 AND interest_rate > 15 THEN 'High Risk Danger Zone'
        ELSE 'Standard Segment'
    END AS risk_segment,
    COUNT(*) AS loan_count,
    ROUND(SUM(is_bad_loan) * 100.0 / NULLIF(COUNT(*), 0), 2) AS default_rate_pct,
    ROUND(AVG(loan_amount), 0) AS avg_loan
FROM fact_loan
GROUP BY risk_segment;


-- QUESTION 05: INCOME AFFORDABILITY STRESS TEST
-- How does borrower income category impact the likelihood of default?
SELECT
    c.income_category,
    COUNT(f.loan_id) AS loan_count,
    ROUND(AVG(f.loan_amount), 0) AS avg_loan,
    ROUND(AVG(f.installment_pct_income), 2) AS avg_payment_burden_pct,
    ROUND(SUM(f.is_bad_loan) * 100.0 / NULLIF(COUNT(f.loan_id), 0), 2) AS default_rate_pct
FROM fact_loan f
JOIN dim_customer c 
    ON f.customer_key = c.customer_key
GROUP BY c.income_category
ORDER BY default_rate_pct DESC;


-- QUESTION 06: LOAN PURPOSE vs PERFORMANCE
-- Which loan purposes are the "safest" for our portfolio?
SELECT
    p.purpose,
    COUNT(f.loan_id) AS loan_count,
    ROUND(SUM(f.is_bad_loan) * 100.0 / NULLIF(COUNT(f.loan_id), 0), 2) AS default_rate_pct,
    ROUND(AVG(f.interest_rate), 2) AS avg_rate
FROM fact_loan f
JOIN dim_purpose p 
    ON f.purpose_key = p.purpose_key
GROUP BY p.purpose
ORDER BY default_rate_pct ASC;


-- QUESTION 07: YEAR-OVER-YEAR QUALITY TREND
-- Tracking if our portfolio quality is improving or deteriorating annually.
WITH yearly_stats AS (
    SELECT
        d.issue_year,
        COUNT(f.loan_id) AS apps,
        SUM(f.loan_amount) AS total_amount,
        SUM(f.is_bad_loan) AS bad_loans
    FROM fact_loan f
    JOIN dim_date d 
        ON f.date_key = d.date_key
    GROUP BY d.issue_year
)

SELECT
    issue_year,
    apps,
    ROUND(total_amount / 1000000.0, 2) AS principal_m,
    ROUND(bad_loans * 100.0 / NULLIF(apps, 0), 2) AS default_rate_pct,
    LAG(ROUND(bad_loans * 100.0 / apps, 2)) 
        OVER (ORDER BY issue_year) AS prev_year_rate,
    ROUND(
        (bad_loans * 100.0 / apps) -
        LAG(bad_loans * 100.0 / apps) OVER (ORDER BY issue_year),
    2) AS yoy_change_percentage_points
FROM yearly_stats
ORDER BY issue_year;


-- QUESTION 08: HOME OWNERSHIP vs RISK
-- Is there a measurable difference in risk between renters and homeowners?
SELECT
    c.home_ownership,
    COUNT(f.loan_id) AS total_loans,
    ROUND(SUM(f.is_bad_loan) * 100.0 / NULLIF(COUNT(f.loan_id), 0), 2) AS default_rate_pct,
    ROUND(AVG(f.loan_amount), 0) AS avg_loan
FROM fact_loan f
JOIN dim_customer c 
    ON f.customer_key = c.customer_key
GROUP BY c.home_ownership
ORDER BY default_rate_pct DESC;


-- QUESTION 09: LOAN TERM IMPACT
-- Comparison of 36-month vs 60-month loan performance.
SELECT
    loan_term_months,
    COUNT(loan_id) AS loan_count,
    ROUND(AVG(interest_rate), 2) AS avg_rate,
    ROUND(SUM(is_bad_loan) * 100.0 / NULLIF(COUNT(loan_id), 0), 2) AS default_rate_pct
FROM fact_loan
GROUP BY loan_term_months
ORDER BY loan_term_months;


-- QUESTION 10: BOTTOM 1% "TOXIC" LOANS (manual review queue)
-- Identifying specific loans with extreme DTI and Interest Rates for immediate review.

WITH scored_loans AS (
    SELECT
        loan_id,
        loan_amount,
        interest_rate,
        dti,
        risk_category,
        loan_condition,
        NTILE(100) OVER (ORDER BY dti DESC, interest_rate DESC) AS risk_percentile
    FROM fact_loan
)

SELECT
    loan_id,
    loan_amount,
    interest_rate,
    dti,
    risk_category,
    loan_condition
FROM scored_loans
WHERE risk_percentile = 1
ORDER BY dti DESC, interest_rate DESC;