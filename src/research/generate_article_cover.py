"""Generate cover image for LinkedIn article on Synthetic Dividends.

Creates a 1200x644 professional bar chart showing empirical volatility alpha
results across three assets with different volatility profiles.

Usage:
    python -m src.research.generate_article_cover

Output:
    docs/articles/synthetic-dividend-article/cover-image.png (1200x644)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def generate_cover_image(output_path: str = None):
    """Generate LinkedIn article cover image (1200x644).

    Args:
        output_path: Optional custom output path. Defaults to article directory.
    """
    if output_path is None:
        output_path = "docs/articles/synthetic-dividend-article/cover-image.png"

    # LinkedIn Featured Image dimensions
    width_px = 1200
    height_px = 644
    dpi = 100

    fig, ax = plt.subplots(figsize=(width_px/dpi, height_px/dpi), dpi=dpi)

    # Data from article empirical results
    assets = ['GLD\n(Gold)', 'NVDA\n(NVIDIA)', 'PLTR\n(Palantir)']
    volatility = [16, 52, 68]
    alpha_pct = [1.4, 77, 198]

    # Color scheme: professional blues/greens with gradient
    colors = ['#5C7A99', '#3B7EA1', '#2A9D8F']

    # Create bars
    bars = ax.bar(assets, alpha_pct, color=colors, edgecolor='white', linewidth=2)

    # Add value labels on top of bars
    for i, (bar, val) in enumerate(zip(bars, alpha_pct)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{val}%',
                ha='center', va='bottom', fontsize=28, fontweight='bold',
                color=colors[i])

    # Add volatility labels below asset names
    for i, (bar, vol) in enumerate(zip(bars, volatility)):
        ax.text(bar.get_x() + bar.get_width()/2., -18,
                f'{vol}% volatility',
                ha='center', va='top', fontsize=14, color='#555555',
                style='italic')

    # Styling
    ax.set_ylabel('Excess Returns vs Buy-and-Hold (%)', fontsize=18, fontweight='600')
    ax.set_ylim(-25, max(alpha_pct) * 1.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.tick_params(axis='both', which='major', labelsize=14, colors='#555555')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.8)
    ax.set_axisbelow(True)

    # Title and subtitle
    fig.suptitle('Volatility Harvesting: Empirical Results',
                 fontsize=32, fontweight='bold', y=0.98, color='#1a1a1a')
    ax.set_title('3-Year Backtests Using Synthetic Dividend Algorithm (SD6/SD8/SD16)',
                 fontsize=16, pad=20, color='#555555', style='italic')

    # Add subtle footer
    fig.text(0.99, 0.02, 'No derivatives • No market timing • Systematic rebalancing only',
             ha='right', va='bottom', fontsize=11, color='#888888', style='italic')

    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    print(f"[OK] Cover image saved to: {output_path}")
    print(f"     Dimensions: {width_px}x{height_px} pixels")

    plt.close()


def main():
    """Generate cover image for article."""
    print("Generating LinkedIn article cover image...")
    print("=" * 60)
    generate_cover_image()
    print("=" * 60)
    print("\nTo use in LinkedIn article:")
    print("1. Upload as Featured Image (1200x644)")
    print("2. Image shows empirical results: 1.4%, 77%, 198% excess returns")
    print("3. Supports 'results-first' hook in article")


if __name__ == "__main__":
    main()
