"""
Loan Default Prediction — SQL Data Loader
==========================================
Reads loan_final313__1.csv, transforms it into the Star Schema,
and loads it into MySQL loan_default_db.

Author: Ajaya Kumar Pradhan
"""

import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Ajaya1@2&3",
    "database": "loan_default_db",
    "charset":  "utf8mb4",
}

CSV_PATH = r"D:\loan default prediction fulll stack project\loan_final313__1.csv"
BATCH_SIZE = 2000  # rows per insert batch

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def connect():
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn

def log(msg):
    print(f"  [OK]  {msg}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — LOAD & CLEAN CSV
# ─────────────────────────────────────────────────────────────────────────────
def load_csv():
    print("\n[1/6] Loading CSV …")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    log(f"Loaded {len(df):,} rows | {df.shape[1]} columns")

    # Standardise column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Keep only required columns (handle detected CSV structure)
    col_map = {
        "loan_amount":  "loan_amount",
        "interest_rate": "interest_rate",
        "annual_inc":   "annual_income",
        "emp_length_int":"employment_years",
        "home_ownership": "home_ownership",
        "loan_condition": "loan_condition",
        "purpose":      "purpose",
        "grade":        "grade",
        "issue_d":      "issue_d",
        "dti":          "dti",
        "installment":  "installment",
        "term":         "term",
        "id":           "loan_id",
        "region":       "region"
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # ── interest_rate: strip % if string ──
    if df["interest_rate"].dtype == object:
        df["interest_rate"] = df["interest_rate"].str.replace("%", "").str.strip().astype(float)

    # ── employment_years: already numerical in this CSV (emp_length_int) ──
    df["employment_years"] = pd.to_numeric(df["employment_years"], errors="coerce").fillna(0).astype(float)

    # ── loan_term_months ──
    df["loan_term_months"] = df["term"].astype(str).str.extract(r"(\d+)").astype(float).fillna(36).astype(int)

    # ── income_category ──
    def income_cat(inc):
        if   inc < 40000:  return "Low"
        elif inc < 80000:  return "Medium"
        else:              return "High"
    df["income_category"] = df["annual_income"].apply(income_cat)

    # ── Derived metrics ──
    df["income_to_loan_ratio"] = (df["annual_income"] / df["loan_amount"].replace(0, np.nan)).clip(0, 500)
    df["lti_ratio"]            = (df["loan_amount"] / df["annual_income"].replace(0, np.nan)).clip(0, 5)
    df["installment_pct_income"] = (df["installment"] / (df["annual_income"].replace(0, np.nan) / 12)).clip(0, 1) * 100

    # ── Risk segment ──
    def risk_seg(row):
        g = str(row.get("grade", "C")).upper()
        dti = row.get("dti", 15)
        if   g in ("A", "B") and dti <= 20:  return "Low Risk"
        elif g in ("E", "F", "G") or dti > 35: return "High Risk"
        else:                                  return "Medium Risk"
    df["risk_category"] = df.apply(risk_seg, axis=1)

    # ── date_key (YYYYMMDD mapped to 1st of the month) ──
    def parse_date_key(val):
        try:
            # The CSV format is DD-MM-YYYY, e.g. 01-07-2013
            dt = pd.to_datetime(val, format="%d-%m-%Y")
            return int(dt.strftime("%Y%m01"))
        except:
            return 20070101
    df["date_key"] = df["issue_d"].apply(parse_date_key)

    # ── loan_id: ensure unique int ──
    if "loan_id" not in df.columns or df["loan_id"].isnull().any():
        df["loan_id"] = range(1, len(df) + 1)
    df["loan_id"] = pd.to_numeric(df["loan_id"], errors="coerce").fillna(0).astype(int)
    # deduplicate
    df = df.drop_duplicates(subset=["loan_id"])
    df = df[df["loan_id"] > 0]

    # ── grade: uppercase, keep only A-G ──
    df["grade"] = df["grade"].str.upper().str.strip()
    df = df[df["grade"].isin(list("ABCDEFG"))]

    # ── purpose: lowercase, strip ──
    known_purposes = {
        "debt_consolidation","credit_card","home_improvement","major_purchase",
        "car","medical","wedding","vacation","moving","house",
        "small_business","educational","renewable_energy","other"
    }
    df["purpose"] = df["purpose"].str.lower().str.strip().str.replace(" ", "_")
    df["purpose"] = df["purpose"].apply(lambda p: p if p in known_purposes else "other")

    # ── home_ownership: uppercase ──
    df["home_ownership"] = df["home_ownership"].str.upper().str.strip()
    df["home_ownership"] = df["home_ownership"].apply(
        lambda h: h if h in ("MORTGAGE","RENT","OWN","OTHER") else "OTHER"
    )

    # Drop nulls in critical columns
    df = df.dropna(subset=["loan_amount","interest_rate","annual_income","dti","installment"])
    log(f"Clean dataset: {len(df):,} rows ready for loading")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — SEED dim_date (2007-2015)
# ─────────────────────────────────────────────────────────────────────────────
def seed_dim_date(conn):
    print("\n[2/6] Seeding complete daily dim_date (2007-2016) …")
    cur = conn.cursor()
    
    # Generate all daily dates from Jan 1, 2007 to Dec 31, 2016
    start_date = pd.to_datetime("2007-01-01")
    end_date = pd.to_datetime("2016-12-31")
    date_range = pd.date_range(start_date, end_date)
    
    rows = []
    for dt in date_range:
        date_key     = int(dt.strftime("%Y%m%d"))
        full_date    = dt.strftime("%Y-%m-%d")
        day_of_month = dt.day
        month_number = dt.month
        month_name   = dt.strftime("%B")
        quarter      = (dt.month - 1) // 3 + 1
        year         = dt.year
        day_of_week  = dt.dayofweek + 1    # Monday=1, Sunday=7
        day_name     = dt.strftime("%A")
        is_weekend   = 1 if dt.dayofweek >= 5 else 0
        
        rows.append((date_key, full_date, day_of_month, month_number, month_name,
                     quarter, year, day_of_week, day_name, is_weekend))

    cur.executemany(
        """INSERT IGNORE INTO dim_date 
           (date_key, full_date, day_of_month, month_number, month_name, 
            quarter, year, day_of_week, day_name, is_weekend) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        rows
    )
    conn.commit()
    log(f"Inserted {len(rows)} daily date rows")
    cur.close()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — LOAD dim_customer, return key map
# ─────────────────────────────────────────────────────────────────────────────
def load_dim_customer(df, conn):
    print("\n[3/6] Loading dim_customer …")
    cur = conn.cursor()

    customers = df[["annual_income","income_category","employment_years","home_ownership"]].copy()
    customers = customers.drop_duplicates().reset_index(drop=True)

    rows = list(customers.itertuples(index=False, name=None))
    cur.executemany(
        "INSERT INTO dim_customer (annual_income, income_category, employment_years, home_ownership) "
        "VALUES (%s, %s, %s, %s)",
        rows
    )
    conn.commit()

    # Fetch back to build lookup map
    cur.execute("SELECT customer_key, annual_income, income_category, employment_years, home_ownership FROM dim_customer")
    rows_back = cur.fetchall()
    cust_map = {}
    for row in rows_back:
        k = (row[1], row[2], row[3], row[4])
        cust_map[k] = row[0]

    log(f"Loaded {len(cust_map):,} unique customers")
    cur.close()
    return cust_map


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Fetch lookup maps (grade, purpose, property)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_lookup_maps(conn):
    print("\n[4/6] Fetching lookup maps …")
    cur = conn.cursor()

    cur.execute("SELECT grade_key, grade FROM dim_loan_grade")
    grade_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT purpose_key, purpose FROM dim_purpose")
    purpose_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT property_key, region FROM dim_property")
    prop_rows = cur.fetchall()
    prop_map = {row[1].lower(): row[0] for row in prop_rows}
    default_prop_key = prop_map.get("other", 1)

    log(f"Grades: {len(grade_map)} | Purposes: {len(purpose_map)} | Regions: {len(prop_map)}")
    cur.close()
    return grade_map, purpose_map, prop_map, default_prop_key


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — LOAD fact_loan in batches
# ─────────────────────────────────────────────────────────────────────────────
def load_fact_loan(df, conn, cust_map, grade_map, purpose_map, prop_map, default_prop_key):
    print(f"\n[5/6] Loading fact_loan ({len(df):,} rows in batches of {BATCH_SIZE}) …")
    cur = conn.cursor()

    sql = """
        INSERT IGNORE INTO fact_loan
            (loan_id, customer_key, property_key, grade_key, date_key, purpose_key,
             loan_amount, interest_rate, installment, loan_term_months, dti,
             income_to_loan_ratio, lti_ratio, installment_pct_income,
             loan_condition, risk_category)
        VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    batch = []
    loaded = 0
    skipped = 0
    t0 = time.time()

    for _, row in df.iterrows():
        try:
            cust_key = cust_map.get(
                (row["annual_income"], row["income_category"],
                 row["employment_years"], row["home_ownership"])
            )
            if cust_key is None:
                skipped += 1
                continue

            grade_key   = grade_map.get(row["grade"])
            purpose_key = purpose_map.get(row["purpose"])
            prop_key    = prop_map.get(str(row["region"]).lower(), default_prop_key)
            
            if grade_key is None or purpose_key is None:
                skipped += 1
                continue

            batch.append((
                int(row["loan_id"]),
                cust_key,
                prop_key,
                grade_key,
                int(row["date_key"]),
                purpose_key,
                float(row["loan_amount"]),
                float(row["interest_rate"]),
                float(row["installment"]),
                int(row["loan_term_months"]),
                float(row["dti"]),
                float(row["income_to_loan_ratio"]) if pd.notna(row["income_to_loan_ratio"]) else None,
                float(row["lti_ratio"])             if pd.notna(row["lti_ratio"])            else None,
                float(row["installment_pct_income"])if pd.notna(row["installment_pct_income"])else None,
                row["loan_condition"],
                row["risk_category"],
            ))

            if len(batch) >= BATCH_SIZE:
                cur.executemany(sql, batch)
                conn.commit()
                loaded += len(batch)
                batch  = []
                elapsed = time.time() - t0
                print(f"     … {loaded:,} rows loaded ({elapsed:.0f}s)", end="\r")

        except Exception as e:
            skipped += 1
            continue

    if batch:
        cur.executemany(sql, batch)
        conn.commit()
        loaded += len(batch)

    elapsed = time.time() - t0
    log(f"fact_loan: {loaded:,} rows loaded, {skipped:,} skipped in {elapsed:.1f}s")
    cur.close()
    return loaded


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — VERIFY
# ─────────────────────────────────────────────────────────────────────────────
def verify(conn):
    print("\n[6/6] Verification …")
    cur = conn.cursor()
    tables = ["dim_customer","dim_loan_grade","dim_purpose","dim_date","dim_property","fact_loan"]
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        log(f"{t}: {count:,} rows")
    cur.close()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Loan Default Prediction — MySQL Star Schema Loader")
    print("=" * 60)

    df = load_csv()

    conn = connect()
    try:
        seed_dim_date(conn)
        cust_map = load_dim_customer(df, conn)
        grade_map, purpose_map, prop_map, default_prop_key = fetch_lookup_maps(conn)
        load_fact_loan(df, conn, cust_map, grade_map, purpose_map, prop_map, default_prop_key)
        verify(conn)
        print("\n[OK] All done! Database loan_default_db is ready.\n")
    except Error as e:
        print(f"\n❌ MySQL Error: {e}")
        conn.rollback()
    finally:
        conn.close()
