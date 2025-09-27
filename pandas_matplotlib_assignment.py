#!/usr/bin/env python3
"""
Pandas + Matplotlib Assignment
- Load CSV or fallback to Iris dataset
- Explore (head, dtypes, missing)
- Clean missing values
- Basic analysis (.describe, groupby)
- Visualizations: line, bar, histogram, scatter
- Error handling for I/O and data issues

Usage:
    python pandas_matplotlib_assignment.py
    # You will be prompted for a CSV file path (press Enter for Iris)
"""

import sys
import os
import math
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Try to import sklearn for the Iris fallback; handle if not installed
def load_iris_fallback() -> pd.DataFrame:
    try:
        from sklearn.datasets import load_iris
    except Exception as e:
        raise RuntimeError(
            "Iris fallback requires scikit-learn. Install it with 'pip install scikit-learn' "
            "or provide a CSV file path when prompted."
        ) from e

    iris = load_iris(as_frame=True)
    df = iris.frame.copy()
    # Standardize column names
    df = df.rename(
        columns={
            "sepal length (cm)": "sepal_length",
            "sepal width (cm)": "sepal_width",
            "petal length (cm)": "petal_length",
            "petal width (cm)": "petal_width",
            "target": "species_id",
        }
    )
    # Add species names
    df["species"] = df["species_id"].map(dict(enumerate(iris.target_names)))
    # Add a synthetic time index for the line chart
    df["sample_id"] = np.arange(1, len(df) + 1)
    return df

def safe_read_csv(path: str) -> pd.DataFrame:
    try:
        # Try parse dates automatically for columns that look like dates
        return pd.read_csv(path, low_memory=False)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {path}") from e
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"No data: {path} is empty.") from e
    except pd.errors.ParserError as e:
        raise ValueError(f"Parse error while reading CSV: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error reading CSV: {e}") from e

def choose_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Heuristics to choose columns:
    - cat_col: first object/category column with 2-20 unique values
    - num1, num2: first two numeric columns
    - time_col: first datetime-like column if any (for line chart), else None
    """
    # Detect time-like columns by attempting to parse to datetime
    time_col = None
    for c in df.columns:
        s = pd.to_datetime(df[c], errors="coerce", infer_datetime_format=True)
        if s.notna().sum() > 0 and s.notna().sum() >= max(5, int(0.1 * len(s))):
            time_col = c
            break

    # Categorical column
    cat_col = None
    for c in df.select_dtypes(include=["object", "category"]).columns:
        nunique = df[c].nunique(dropna=True)
        if 2 <= nunique <= 20:
            cat_col = c
            break

    # Numeric columns
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num1 = num_cols[0] if len(num_cols) >= 1 else None
    num2 = num_cols[1] if len(num_cols) >= 2 else None

    return cat_col, num1, num2, time_col

def clean_missing(df: pd.DataFrame) -> pd.DataFrame:
    # Fill numeric NaNs with column median; categorical with mode; drop all-null columns
    cleaned = df.copy()
    # Drop columns that are entirely NaN
    all_null_cols = [c for c in cleaned.columns if cleaned[c].isna().all()]
    if all_null_cols:
        cleaned = cleaned.drop(columns=all_null_cols)

    num_cols = cleaned.select_dtypes(include=[np.number]).columns
    cat_cols = cleaned.select_dtypes(include=["object", "category"]).columns

    for c in num_cols:
        if cleaned[c].isna().any():
            cleaned[c] = cleaned[c].fillna(cleaned[c].median())

    for c in cat_cols:
        if cleaned[c].isna().any():
            mode_vals = cleaned[c].mode(dropna=True)
            if not mode_vals.empty:
                cleaned[c] = cleaned[c].fillna(mode_vals.iloc[0])
            else:
                cleaned[c] = cleaned[c].fillna("Unknown")

    return cleaned

def ensure_output_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)

def plot_line(df: pd.DataFrame, x_col: Optional[str], y_col: str, out_dir: Path) -> Optional[Path]:
    try:
        plt.figure()
        if x_col is not None:
            x = pd.to_datetime(df[x_col], errors="coerce") if "datetime" in str(df[x_col].dtype) else df[x_col]
            plt.plot(x, df[y_col])
            plt.xlabel(x_col)
        else:
            # Fallback to sample index
            x = np.arange(1, len(df) + 1)
            plt.plot(x, df[y_col])
            plt.xlabel("sample_index")
        plt.ylabel(y_col)
        plt.title(f"Line Chart: {y_col} over {x_col or 'sample_index'}")
        out_path = out_dir / "line_chart.png"
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path
    except Exception as e:
        print(f"[WARN] Could not create line chart: {e}")
        return None

def plot_bar(means: pd.Series, out_dir: Path, title: str, ylabel: str) -> Optional[Path]:
    try:
        plt.figure()
        plt.bar(means.index.astype(str), means.values)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel("Category")
        plt.xticks(rotation=45, ha="right")
        out_path = out_dir / "bar_chart.png"
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path
    except Exception as e:
        print(f"[WARN] Could not create bar chart: {e}")
        return None

def plot_hist(df: pd.DataFrame, col: str, out_dir: Path) -> Optional[Path]:
    try:
        plt.figure()
        plt.hist(df[col].dropna(), bins=20)
        plt.title(f"Histogram: {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        out_path = out_dir / "histogram.png"
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path
    except Exception as e:
        print(f"[WARN] Could not create histogram: {e}")
        return None

def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str, cat_col: Optional[str], out_dir: Path) -> Optional[Path]:
    try:
        plt.figure()
        if cat_col and df[cat_col].nunique() <= 10:
            for cat, sub in df.groupby(cat_col):
                plt.scatter(sub[x_col], sub[y_col], label=str(cat))
            plt.legend(title=cat_col)
        else:
            plt.scatter(df[x_col], df[y_col])
        plt.title(f"Scatter: {x_col} vs {y_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        out_path = out_dir / "scatter.png"
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path
    except Exception as e:
        print(f"[WARN] Could not create scatter plot: {e}")
        return None

def main():
    print("=== Pandas + Matplotlib Assignment ===")
    print("Tip: Press Enter to use the Iris dataset fallback.\n")
    csv_path = input("Enter path to a CSV file (or press Enter for Iris): ").strip()

    # Load data
    if csv_path:
        print(f"\nLoading CSV: {csv_path}")
        df_raw = safe_read_csv(csv_path)
        # If there's an obvious date column, try parse it for exploration (non-destructive)
        for c in df_raw.columns:
            if "date" in c.lower() or "time" in c.lower():
                try:
                    df_raw[c] = pd.to_datetime(df_raw[c], errors="coerce", infer_datetime_format=True)
                except Exception:
                    pass
        # Add sample_id for plotting fallback
        if "sample_id" not in df_raw.columns:
            df_raw["sample_id"] = np.arange(1, len(df_raw) + 1)
    else:
        print("No CSV provided. Using Iris dataset fallback.\n")
        df_raw = load_iris_fallback()

    # Explore
    print("\n--- Head ---")
    print(df_raw.head())

    print("\n--- DTypes ---")
    print(df_raw.dtypes)

    print("\n--- Missing values per column ---")
    print(df_raw.isnull().sum())

    # Clean
    df = clean_missing(df_raw)

    # Basic statistics
    print("\n--- Describe (numeric) ---")
    print(df.describe(include=[np.number]))

    # Choose columns for analysis/plots
    cat_col, num1, num2, time_col = choose_columns(df)

    # Grouping (if we have a categorical and at least one numeric)
    if cat_col and num1:
        group_means = df.groupby(cat_col, dropna=True)[num1].mean().sort_values(ascending=False)
        print(f"\n--- Group mean of '{num1}' by '{cat_col}' ---")
        print(group_means)
        # Simple finding
        top_cat = group_means.index[0]
        top_val = group_means.iloc[0]
        print(f"\nFinding: '{top_cat}' has the highest mean {num1} ({top_val:.3f}).")
    else:
        group_means = None
        print("\n[INFO] Could not compute group means (need a categorical column and a numeric column).")

    # Output directory for plots
    out_dir = Path("plots")
    ensure_output_dir(out_dir)

    # Visualizations (4)
    # 1) Line chart: use time_col if available; else sample_id over num1 (or first numeric)
    y_for_line = num1 or df.select_dtypes(include=[np.number]).columns[0]
    line_path = plot_line(df, time_col if time_col else ("sample_id" if "sample_id" in df.columns else None), y_for_line, out_dir)
    if line_path: print(f"Saved: {line_path}")

    # 2) Bar chart: group mean bar if available
    if group_means is not None and not group_means.empty:
        bar_path = plot_bar(group_means, out_dir, f"Mean {num1} by {cat_col}", ylabel=f"Mean {num1}")
        if bar_path: print(f"Saved: {bar_path}")
    else:
        print("[INFO] Skipping bar chart (no suitable categorical grouping).")

    # 3) Histogram: first numeric column
    hist_col = num1 or df.select_dtypes(include=[np.number]).columns[0]
    hist_path = plot_hist(df, hist_col, out_dir)
    if hist_path: print(f"Saved: {hist_path}")

    # 4) Scatter: need two numeric columns
    if num1 and num2:
        scatter_path = plot_scatter(df, num1, num2, cat_col, out_dir)
        if scatter_path: print(f"Saved: {scatter_path}")
    else:
        print("[INFO] Skipping scatter (need two numeric columns).")

    print("\nDone. Plots saved under ./plots")
    print("Remember to include code, outputs, and observations in your submission.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting gracefully.")
