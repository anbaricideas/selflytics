"""Visualization generation with matplotlib."""

import uuid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend (server-safe)
import matplotlib.pyplot as plt


class VizGenerator:
    """Generate charts from fitness data."""

    def __init__(self, cache_dir: str = "spike/cache"):
        """Initialize visualization generator with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_line_chart(
        self, data: list[tuple], title: str, x_label: str, y_label: str
    ) -> str:
        """
        Generate line chart and return visualization ID.

        Args:
            data: List of (x, y) tuples
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label

        Returns:
            Visualization ID (filename without extension)
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract x, y values
        x_vals = [item[0] for item in data]
        y_vals = [item[1] for item in data]

        # Plot line
        ax.plot(x_vals, y_vals, marker="o", linewidth=2, markersize=6)

        # Styling
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.grid(True, alpha=0.3)

        # Rotate x-axis labels if dates
        plt.xticks(rotation=45, ha="right")

        # Tight layout
        plt.tight_layout()

        # Save to file
        viz_id = str(uuid.uuid4())
        output_path = self.cache_dir / f"viz_{viz_id}.png"
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return viz_id
