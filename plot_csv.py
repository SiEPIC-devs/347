#!/usr/bin/env python3
"""
plot_csv.py — simple matplotlib CSV plotter.

Usage examples:
  python plot_csv.py data.csv
  python plot_csv.py data.csv --x Wavelength_nm --y Power_dBm
  python plot_csv.py data.csv --y col2 col3            # x = first column by default
  python plot_csv.py data.csv --delimiter ';' --save out.png
"""

import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt

def main():
    p = argparse.ArgumentParser(description="Plot CSV columns with matplotlib.")
    p.add_argument("csv", help="Path to CSV file")
    p.add_argument("--x", help="Column name to use as X axis (default: first column)")
    p.add_argument("--y", nargs="+", help="One or more column names to plot as Y (default: all numeric except X)")
    p.add_argument("--delimiter", default=",", help="CSV delimiter (default: ',')")
    p.add_argument("--no-header", action="store_true", help="Treat CSV as having no header row")
    p.add_argument("--save", help="Save figure to this path instead of showing it")
    p.add_argument("--title", default=None, help="Plot title")
    args = p.parse_args()

    # Read CSV (pandas is fast and handles types well)
    header = None if args.no_header else 0
    try:
        df = pd.read_csv(args.csv, sep=args.delimiter, header=header)
    except Exception as e:
        sys.exit(f"Failed to read CSV: {e}")

    # If no header: synthesize column names as C0, C1, ...
    if header is None:
        df.columns = [f"C{i}" for i in range(df.shape[1])]

    if df.empty:
        sys.exit("CSV is empty.")

    # Choose X column
    x_col = args.x if args.x else df.columns[0]
    if x_col not in df.columns:
        sys.exit(f"X column '{x_col}' not found. Available: {list(df.columns)}")

    # Choose Y columns
    if args.y:
        y_cols = args.y
        for c in y_cols:
            if c not in df.columns:
                sys.exit(f"Y column '{c}' not found. Available: {list(df.columns)}")
    else:
        # Default: plot all numeric columns except X
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        y_cols = [c for c in numeric_cols if c != x_col]
        if not y_cols:
            # If nothing numeric, try everything except X
            y_cols = [c for c in df.columns if c != x_col]

    if not y_cols:
        sys.exit("No Y columns selected to plot.")

    # Basic plot
    fig = plt.figure()  # one chart, no styles/colors specified
    for c in y_cols:
        plt.plot(df[x_col], df[c], label=c)

    plt.xlabel(x_col)
    plt.ylabel(", ".join(y_cols) if len(y_cols) == 1 else "values")
    if args.title:
        plt.title(args.title)
    if len(y_cols) > 1:
        plt.legend()
    plt.grid(True)

    if args.save:
        try:
            plt.savefig(args.save, bbox_inches="tight", dpi=150)
            print(f"Saved figure to {args.save}")
        except Exception as e:
            sys.exit(f"Failed to save figure: {e}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
