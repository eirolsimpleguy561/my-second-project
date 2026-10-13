import pandas as pd
import sys


def analyze_csv(filepath):
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"\n--- CSV Analysis: {filepath} ---")
    print(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")
    print(f"\nColumn Names: {list(df.columns)}")

    # Missing values
    missing = df.isnull().sum()
    print("\nMissing Values:")
    print(missing[missing > 0].to_string() if missing.any() else "  None found.")

    # Numeric stats
    numeric = df.select_dtypes(include='number')
    if not numeric.empty:
        print("\nNumeric Column Statistics:")
        print(numeric.describe().round(2).to_string())

    # Export summary
    summary_path = "summary_report.csv"
    if not numeric.empty:
        numeric.describe().round(2).to_csv(summary_path)
        print(f"\nSummary exported to '{summary_path}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath = input("Enter CSV file path: ").strip()
    else:
        filepath = sys.argv[1]
    analyze_csv(filepath)
