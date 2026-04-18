/*
=============================================================================
TABULAR EDITOR BATCH SCRIPT: LOAN DEFAULT MEASURES
=============================================================================
Instructions:
1. Open Tabular Editor with your Power BI model.
2. Go to the "Advanced Scripting" tab.
3. Paste this code and click "Run".
4. This will create a "Main Measures" table and populate all DAX formulas.
=============================================================================
*/

// --- 1. Create a Measure Table ---
var measureTableName = "Main Measures";
if (!Model.Tables.Contains(measureTableName)) {
    Model.AddTable(measureTableName);
}

var mTable = Model.Tables[measureTableName];

// --- 2. Helper to Add Measures ---
Action<string, string, string, string> AddM = (name, dax, format, folder) => {
    var m = mTable.AddMeasure(name, dax);
    m.FormatString = format;
    m.DisplayFolder = folder;
};

// --- 3. DEFINING MEASURES ---

// KPIs
AddM("Total Applications", "COUNTROWS('fact_loan')", "0", "1. Core KPIs");
AddM("Good Loans", "CALCULATE(COUNTROWS('fact_loan'), 'fact_loan'[loan_condition] = \"Good Loan\")", "0", "1. Core KPIs");
AddM("Bad Loans", "CALCULATE(COUNTROWS('fact_loan'), 'fact_loan'[loan_condition] = \"Bad Loan\")", "0", "1. Core KPIs");
AddM("Approval Rate %", "DIVIDE([Good Loans], [Total Applications])", "0.00%", "1. Core KPIs");
AddM("Default Rate %", "DIVIDE([Bad Loans], [Total Applications])", "0.00%", "1. Core KPIs");
AddM("Total Portfolio £M", "DIVIDE(SUM('fact_loan'[loan_amount]), 1000000)", "\"£\"#,0.00\"M\"", "1. Core KPIs");
AddM("Avg Interest Rate", "AVERAGE('fact_loan'[interest_rate])", "0.00%", "1. Core KPIs");

// Risk Analysis
AddM("Low Risk Loans", "CALCULATE(COUNTROWS('fact_loan'), 'fact_loan'[risk_category] = \"Low Risk\")", "0", "2. Risk Analysis");
AddM("High Risk Loans", "CALCULATE(COUNTROWS('fact_loan'), 'fact_loan'[risk_category] = \"High Risk\")", "0", "2. Risk Analysis");
AddM("High Risk %", "DIVIDE([High Risk Loans], [Total Applications])", "0.00%", "2. Risk Analysis");
AddM("Expected Loss £M", "DIVIDE(SUMX('fact_loan', 'fact_loan'[loan_amount] * IF('fact_loan'[is_bad_loan] = 1, 1, 0)), 1000000)", "\"£\"#,0.00\"M\"", "2. Risk Analysis");

// Affordability
AddM("Avg Annual Income", "AVERAGE('dim_customer'[annual_income])", "\"£\"#,0", "3. Affordability");
AddM("Overextended %", "DIVIDE(CALCULATE(COUNTROWS('fact_loan'), 'fact_loan'[installment_pct_income] > 30), [Total Applications])", "0.0%", "3. Affordability");

// Time Intelligence
AddM("Default Rate YoY Change", "VAR CR = [Default Rate %] VAR PR = CALCULATE([Default Rate %], SAMEPERIODLASTYEAR('dim_date'[full_date])) RETURN IF(NOT ISBLANK(PR), CR - PR, BLANK())", "0.00 pp", "4. Time Intelligence");

"SUCCESS: 14 measures created in 'Main Measures'".Output();
