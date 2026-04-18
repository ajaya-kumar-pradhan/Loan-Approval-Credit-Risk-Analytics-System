import pandas as pd

CSV_PATH = r"D:\loan default prediction fulll stack project\loan_final313__1.csv"
df = pd.read_csv(CSV_PATH, low_memory=False, nrows=5)
print("Raw 'issue_d' column values:")
if "issue_d" in df.columns:
    print(df["issue_d"].tolist())
elif "issue_d" in df.columns.str.strip().str.lower().str.replace(" ", "_"):
    col = [c for c in df.columns if c.strip().lower().replace(" ", "_") == "issue_d"][0]
    print(df[col].tolist())
else:
    print(df.columns)
