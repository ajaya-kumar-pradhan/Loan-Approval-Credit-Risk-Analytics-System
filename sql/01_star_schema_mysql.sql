-- =============================================================================
-- LOAN DEFAULT PREDICTION — SQL LAYER
-- Star Schema Design + Advanced Analytical Queries
-- Database: MySQL 8.0+
-- Author: Ajaya Kumar Pradhan | Senior Data Analyst / Data Scientist
-- =============================================================================

CREATE DATABASE IF NOT EXISTS loan_default_db;
USE loan_default_db;

-- =============================================================================
-- SECTION 1: DROP TABLES (clean slate)
-- =============================================================================
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS fact_loan;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_property;
DROP TABLE IF EXISTS dim_loan_grade;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_purpose;
SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- SECTION 2: DIMENSION TABLES
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION: dim_customer
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE dim_customer (
    customer_key        INT             AUTO_INCREMENT PRIMARY KEY,
    annual_income       DECIMAL(12,2)   NOT NULL,
    income_category     VARCHAR(10)     NOT NULL,      -- Low / Medium / High
    employment_years    DECIMAL(4,1)    NOT NULL,
    home_ownership      VARCHAR(20)     NOT NULL,      -- MORTGAGE/RENT/OWN/OTHER
    employment_stable   TINYINT(1)      GENERATED ALWAYS AS (employment_years >= 5) STORED,
    owns_property       TINYINT(1)      GENERATED ALWAYS AS (home_ownership IN ('MORTGAGE','OWN')) STORED,
    income_band         VARCHAR(20)     GENERATED ALWAYS AS (
                            CASE
                                WHEN annual_income < 30000  THEN 'Under 30K'
                                WHEN annual_income < 60000  THEN '30K-60K'
                                WHEN annual_income < 100000 THEN '60K-100K'
                                ELSE                             'Over 100K'
                            END
                        ) STORED,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
) COMMENT = 'Customer dimension: borrower demographics, income, and housing stability metrics.';


-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION: dim_property (Region)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE dim_property (
    property_key        INT             AUTO_INCREMENT PRIMARY KEY,
    region              VARCHAR(30)     NOT NULL,
    region_type         VARCHAR(20)     NOT NULL
) COMMENT = 'Geographic / region dimension for loan applications.';

INSERT INTO dim_property (region, region_type) VALUES
    ('ulster',       'Ireland'),
    ('leinster',     'Ireland'),
    ('munster',      'Ireland'),
    ('cannught',     'Ireland'),
    ('Northern-Irl', 'Northern-Ireland'),
    ('Other',        'Other');


-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION: dim_loan_grade
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE dim_loan_grade (
    grade_key           INT             AUTO_INCREMENT PRIMARY KEY,
    grade               CHAR(1)         NOT NULL,
    grade_label         VARCHAR(20)     NOT NULL,
    risk_level          VARCHAR(20)     NOT NULL,
    min_interest_rate   DECIMAL(5,2),
    max_interest_rate   DECIMAL(5,2)
) COMMENT = 'Credit grade dimension with risk classification and rate bands.';

INSERT INTO dim_loan_grade (grade, grade_label, risk_level, min_interest_rate, max_interest_rate) VALUES
    ('A', 'Prime',        'Low Risk',     5.42,  9.99),
    ('B', 'Near-Prime',   'Low Risk',    10.00, 13.99),
    ('C', 'Standard',     'Medium Risk', 14.00, 16.99),
    ('D', 'Near-Subprime','Medium Risk', 17.00, 19.99),
    ('E', 'Subprime',     'High Risk',   20.00, 22.99),
    ('F', 'Deep-Subprime','High Risk',   23.00, 25.00),
    ('G', 'Distressed',   'High Risk',   25.01, 26.06);


-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION: dim_date
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE dim_date (
    date_key            INT             PRIMARY KEY,   -- YYYYMMDD integer
    full_date           DATE            NOT NULL,
    day_of_month        SMALLINT        NOT NULL,
    month_number        SMALLINT        NOT NULL,
    month_name          VARCHAR(10)     NOT NULL,
    quarter             SMALLINT        NOT NULL,
    year                SMALLINT        NOT NULL,
    day_of_week         SMALLINT        NOT NULL,
    day_name            VARCHAR(10)     NOT NULL,
    is_weekend          TINYINT(1)      NOT NULL,
    is_financial_crisis TINYINT(1)      GENERATED ALWAYS AS (year BETWEEN 2008 AND 2010) STORED
) COMMENT = 'Complete daily Date dimension seeded for years 2007-2016.';


-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION: dim_purpose
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE dim_purpose (
    purpose_key         INT             AUTO_INCREMENT PRIMARY KEY,
    purpose             VARCHAR(50)     NOT NULL,
    purpose_category    VARCHAR(30)     NOT NULL,
    is_high_risk        TINYINT(1)      NOT NULL DEFAULT 0
) COMMENT = 'Loan purpose dimension with risk classification.';

INSERT INTO dim_purpose (purpose, purpose_category, is_high_risk) VALUES
    ('debt_consolidation', 'Debt Management',  0),
    ('credit_card',        'Debt Management',  0),
    ('home_improvement',   'Asset Investment', 0),
    ('major_purchase',     'Personal',         0),
    ('car',                'Personal',         0),
    ('medical',            'Personal',         0),
    ('wedding',            'Personal',         0),
    ('vacation',           'Personal',         0),
    ('moving',             'Personal',         0),
    ('house',              'Asset Investment', 0),
    ('small_business',     'Business',         1),
    ('educational',        'Education',        0),
    ('renewable_energy',   'Asset Investment', 0),
    ('other',              'Other',            0);


-- =============================================================================
-- SECTION 3: FACT TABLE
-- =============================================================================
CREATE TABLE fact_loan (
    loan_id                 BIGINT          PRIMARY KEY,
    customer_key            INT             NOT NULL,
    property_key            INT             NOT NULL,
    grade_key               INT             NOT NULL,
    date_key                INT             NOT NULL,
    purpose_key             INT             NOT NULL,

    -- Loan financials
    loan_amount             DECIMAL(10,2)   NOT NULL,
    interest_rate           DECIMAL(5,2)    NOT NULL,
    installment             DECIMAL(10,2)   NOT NULL,
    loan_term_months        SMALLINT        NOT NULL,
    dti                     DECIMAL(5,2)    NOT NULL,

    -- Derived risk metrics
    income_to_loan_ratio    DECIMAL(8,4),
    lti_ratio               DECIMAL(8,4),
    installment_pct_income  DECIMAL(6,2),

    -- Outcome
    loan_condition          VARCHAR(15)     NOT NULL,
    is_bad_loan             TINYINT(1)      GENERATED ALWAYS AS (loan_condition = 'Bad Loan') STORED,

    -- Risk segment
    risk_category           VARCHAR(15),

    -- Metadata
    loaded_at               TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (property_key) REFERENCES dim_property(property_key),
    FOREIGN KEY (grade_key)    REFERENCES dim_loan_grade(grade_key),
    FOREIGN KEY (date_key)     REFERENCES dim_date(date_key),
    FOREIGN KEY (purpose_key)  REFERENCES dim_purpose(purpose_key)
) COMMENT = 'Central fact table — one row per loan application. Grain = individual loan.';

-- Indexes for analytical query performance
CREATE INDEX idx_fact_loan_grade    ON fact_loan (grade_key);
CREATE INDEX idx_fact_loan_date     ON fact_loan (date_key);
CREATE INDEX idx_fact_loan_customer ON fact_loan (customer_key);
CREATE INDEX idx_fact_loan_region   ON fact_loan (property_key);
CREATE INDEX idx_fact_loan_bad      ON fact_loan (is_bad_loan);
CREATE INDEX idx_fact_loan_risk     ON fact_loan (risk_category);


-- =============================================================================
-- SECTION 4: ANALYTICAL VIEW FOR POWER BI
-- =============================================================================
CREATE OR REPLACE VIEW vw_loan_analytics AS
SELECT
    f.loan_id,
    d.full_date,
    d.year                                                   AS issue_year,
    d.quarter                                                AS issue_quarter,
    d.month_name,
    d.is_financial_crisis,
    g.grade,
    g.grade_label,
    g.risk_level                                             AS grade_risk_level,
    p2.region,
    p2.region_type,
    pu.purpose,
    pu.purpose_category,
    c.income_category,
    c.income_band,
    c.employment_years,
    c.home_ownership,
    c.employment_stable,
    c.owns_property,
    f.loan_amount,
    f.interest_rate,
    f.installment,
    f.loan_term_months,
    f.dti,
    f.income_to_loan_ratio,
    f.lti_ratio,
    f.installment_pct_income,
    f.loan_condition,
    f.is_bad_loan,
    f.risk_category
FROM fact_loan       f
JOIN dim_date        d   ON f.date_key      = d.date_key
JOIN dim_loan_grade  g   ON f.grade_key     = g.grade_key
JOIN dim_property    p2  ON f.property_key  = p2.property_key
JOIN dim_purpose     pu  ON f.purpose_key   = pu.purpose_key
JOIN dim_customer    c   ON f.customer_key  = c.customer_key;
