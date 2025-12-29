import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# ============================================================================
# Configuration and Setup
# ============================================================================

def find_latest_run() -> Path:
    """Find the most recent benchmark run directory."""
    # Get the script directory and construct absolute path
    script_dir = Path(__file__).parent
    runs_dir = script_dir.parent / "results" / "runs"
    if not runs_dir.exists():
        print(f"Error: results/runs directory not found at {runs_dir}")
        sys.exit(1)

    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        print("Error: No run directories found")
        sys.exit(1)

    return run_dirs[-1]


def load_benchmark_data(run_dir: Path) -> pd.DataFrame:
    """Load and combine network and file benchmark data."""
    net_csv = run_dir / "net-raw.csv"
    file_disk_csv = run_dir / "file-disk-raw.csv"
    file_memory_csv = run_dir / "file-memory-raw.csv"
    
    # For backwards compatibility, also check for old file-raw.csv
    file_csv = run_dir / "file-raw.csv"

    dfs = []
    
    if net_csv.exists():
        df_net = pd.read_csv(net_csv)
        dfs.append(df_net)

    if file_disk_csv.exists():
        df_disk = pd.read_csv(file_disk_csv)
        dfs.append(df_disk)

    if file_memory_csv.exists():
        df_mem = pd.read_csv(file_memory_csv)
        dfs.append(df_mem)

    # Backwards compatibility
    if file_csv.exists() and not file_disk_csv.exists() and not file_memory_csv.exists():
        df_file = pd.read_csv(file_csv)
        dfs.append(df_file)

    if not dfs:
        print(f"Error: No CSV files found in {run_dir}")
        sys.exit(1)

    df = pd.concat(dfs, ignore_index=True)
    #rename net to HTTP/TCP for clarity
    df["method"] = df["method"].replace("net", "network - HTTP/TCP")

    return df


# ============================================================================
# Data Aggregation
# ============================================================================

def compute_latency_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute latency percentiles (p50, p90, p95, p99) by method and size.

    Returns:
        DataFrame with columns: method, size_bytes, p50, p90, p95, p99
    """
    percentiles = (
        df.groupby(["method", "size_bytes"])["elapsed_ms"]
        .quantile([0.5, 0.9, 0.95, 0.99])
        .unstack(level=-1)
        .reset_index()
        .rename(columns={0.5: "p50", 0.9: "p90", 0.95: "p95", 0.99: "p99"})
    )
    return percentiles


def compute_throughput_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute throughput mean and standard deviation by method and size.

    Returns:
        DataFrame with columns: method, size_bytes, mean, std
    """
    thr_stats = (
        df.groupby(["method", "size_bytes"])["throughput_mib_s"]
        .agg(["mean", "std"])
        .reset_index()
    )
    return thr_stats


def compute_transfer_time_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transfer time mean and std deviation by method and size for comparison.

    Returns:
        DataFrame with columns: method, size_bytes, mean, std
    """
    transfer_stats = (
        df.groupby(["method", "size_bytes"])["elapsed_ms"]
        .agg(["mean", "std"])
        .reset_index()
    )
    return transfer_stats


# ============================================================================
# Utility Functions
# ============================================================================

def format_bytes(bytes_val: int) -> str:
    """Format byte size as human-readable string (e.g., 1KiB, 1MiB)."""
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.0f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TiB"


# ============================================================================
# Plotting Functions
# ============================================================================

def plot_latency_percentiles(percentiles: pd.DataFrame, output_dir: Path) -> None:
    import matplotlib.colors as mcolors

    def lighten(color: str, amount: float) -> tuple:
        """Lighten a color by blending it with white.
        amount in [0, 1]: 0 = original, 1 = white.
        """
        r, g, b = mcolors.to_rgb(color)
        return (1 - amount) * r + amount * 1.0, (1 - amount) * g + amount * 1.0, (1 - amount) * b + amount * 1.0

    # Choose distinct base colors for each method
    base_colors = {
        "file-disk": "#1f77b4",   # blue
        "file-memory": "#d62728", # red
        "net": "#2ca02c",        # green
    }

    # Percentile-specific style: darker for p50, lighter for p95/p99
    pct_styles = {
        "p50": {"lighten": 0.0, "linestyle": "-",  "marker": "o", "label": "p50 (median)"},
        "p95": {"lighten": 0.35, "linestyle": "--", "marker": "s", "label": "p95"},
        "p99": {"lighten": 0.6, "linestyle": ":",  "marker": "^", "label": "p99"},
    }

    plt.figure(figsize=(10, 6))

    # Ensure consistent plotting order by method
    for method, sub in percentiles.groupby("method"):
        sub = sub.sort_values("size_bytes")
        base = base_colors.get(method, None)
        if base is None:
            # fall back to current rc cycle color
            base = plt.gca()._get_lines.get_next_color()

        for pct_key in ["p50", "p95", "p99"]:
            style = pct_styles[pct_key]
            color = lighten(base, style["lighten"]) if style["lighten"] > 0 else base
            plt.plot(
                sub["size_bytes"],
                sub[pct_key],
                marker=style["marker"],
                linestyle=style["linestyle"],
                linewidth=2 if pct_key == "p50" else 1.7,
                markersize=6,
                color=color,
                label=f"{method} {style['label']}",
            )

    # Get unique sizes and format as human-readable labels
    unique_sizes = sorted(percentiles["size_bytes"].unique())
    size_labels = [format_bytes(size) for size in unique_sizes]

    plt.xscale("log", base=2)
    plt.xticks(unique_sizes, size_labels)
    plt.xlabel("Data Size", fontsize=11)
    plt.ylabel("Latency (ms)", fontsize=11)
    plt.title("Latency Percentiles vs Payload Size (n=20)\n(color per method, shade per percentile)", fontsize=13, fontweight="bold")
    plt.grid(True, which="both", linestyle=":", alpha=0.4)
    plt.legend(loc="best", fontsize=10)
    plt.tight_layout()

    output_path = output_dir / "latency_percentiles.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def plot_throughput(thr_stats: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(10, 6))

    for method, sub in thr_stats.groupby("method"):
        sub = sub.sort_values("size_bytes")
        plt.errorbar(
            sub["size_bytes"],
            sub["mean"],
            yerr=sub["std"],
            marker="o",
            capsize=4,
            linewidth=2,
            markersize=7,
            label=method,
        )

    # Get unique sizes and format as human-readable labels
    unique_sizes = sorted(thr_stats["size_bytes"].unique())
    size_labels = [format_bytes(size) for size in unique_sizes]

    plt.xscale("log", base=2)
    plt.xticks(unique_sizes, size_labels)
    plt.xlabel("Data Size", fontsize=11)
    plt.ylabel("Throughput (MiB/s)", fontsize=11)
    plt.title("Throughput vs Payload Size (mean ± 1σ, n=20)", fontsize=13, fontweight="bold")
    plt.grid(True, which="both", linestyle=":", alpha=0.4)
    plt.legend(loc="best", fontsize=10)
    plt.tight_layout()

    output_path = output_dir / "throughput.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path.name}")
    plt.close()


def plot_transfer_time_comparison(transfer_stats: pd.DataFrame, output_dir: Path) -> None:
    # Pivot data for grouped bar chart
    pivot_mean = transfer_stats.pivot(
        index="size_bytes", columns="method", values="mean"
    )
    pivot_std = transfer_stats.pivot(
        index="size_bytes", columns="method", values="std"
    )

    fig, ax = plt.subplots(figsize=(11, 6))

    x = np.arange(len(pivot_mean.index))
    width = 0.25  # Narrower bars for 3 methods

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # blue, orange, green
    for i, method in enumerate(pivot_mean.columns):
        offset = (i - len(pivot_mean.columns) / 2 + 0.5) * width

        # Calculate asymmetric error bars to prevent going below 0
        means = pivot_mean[method].values
        stds = pivot_std[method].values
        yerr_lower = np.minimum(means, stds)  # Don't go below 0
        yerr_upper = stds

        ax.bar(
            x + offset,
            means,
            width,
            yerr=[yerr_lower, yerr_upper],
            label=method,
            color=colors[i],
            alpha=0.8,
            capsize=3,
            error_kw={'linewidth': 1.5, 'alpha': 0.7}
        )

    # Format x-axis with human-readable sizes
    size_labels = [format_bytes(size) for size in pivot_mean.index]
    ax.set_xlabel("Data Size", fontsize=11)
    ax.set_ylabel("Latency (ms)", fontsize=11)
    ax.set_title("Latency Comparison: Network vs File I/O\n(Mean ± 1σ, n=20 per size)",
                 fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(size_labels)
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)

    plt.tight_layout()

    output_path = output_dir / "latency_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved: {output_path.name}")
    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    run_dir = find_latest_run()
    print(f"📊 Using latest run: {run_dir.name}\n")

    df = load_benchmark_data(run_dir)

    output_dir = run_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Computing aggregations...")
    percentiles = compute_latency_percentiles(df)
    thr_stats = compute_throughput_stats(df)
    transfer_stats = compute_transfer_time_stats(df)

    print("Generating plots...\n")
    plot_latency_percentiles(percentiles, output_dir)
    plot_throughput(thr_stats, output_dir)
    plot_transfer_time_comparison(transfer_stats, output_dir)

    print(f"\n✅ All plots saved to: {output_dir}")


if __name__ == "__main__":
    main()

