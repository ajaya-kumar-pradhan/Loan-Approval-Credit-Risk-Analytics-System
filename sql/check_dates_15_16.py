import pandas as pd

CSV_PATH = r"D:\loan default prediction fulll stack project\loan_final313__1.csv"
df = pd.read_csv(CSV_PATH, low_memory=False, usecols=["issue_d"])

# Print a sample of dates containing '15' or '16'
sample_15 = df[df['issue_d'].astype(str).str.contains('15', na=False)]['issue_d'].head(5).tolist()
sample_16 = df[df['issue_d'].astype(str).str.contains('16', na=False)]['issue_d'].head(5).tolist()

print(f"Sample 2015 dates: {sample_15}")
print(f"Sample 2016 dates: {sample_16}")

# Show top 10 trailing characters to see year distributions
print("\nUnique endings of issue_d:")
print(df['issue_d'].str[-4:].value_counts().head(10))

# See if there are mixed formats (e.g. length of strings)
print("\nLengths of issue_d strings:")
print(df['issue_d'].str.len().value_counts())
