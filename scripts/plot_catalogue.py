#!/usr/bin/env python3
"""Plot the exact component-count matrix of a completed finite catalogue."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    index = json.loads(args.index.read_bytes())
    if index.get("complete") is not True:
        raise ValueError("Only a complete finite catalogue may be plotted")
    labels = index["discriminants"]
    position = {d: i for i, d in enumerate(labels)}
    counts = np.full((len(labels), len(labels)), np.nan)
    for row in index["pairs"]:
        i, j = position[row["d1"]], position[row["d2"]]
        counts[i, j] = counts[j, i] = row["component_count"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, ax = plt.subplots(figsize=(10, 9), dpi=180)
    fig.patch.set_facecolor("#fbfbf7")
    cmap = plt.get_cmap("cividis").copy()
    cmap.set_bad("#e5e7eb")
    image = ax.imshow(counts, origin="lower", interpolation="nearest", cmap=cmap,
                      vmin=0, vmax=np.nanmax(counts), aspect="equal")
    last = len(labels) - 1
    ticks = sorted(set([0, *range(20, max(1, last - 10), 20), last]))
    ax.set_xticks(ticks, [str(labels[i]) for i in ticks])
    ax.set_yticks(ticks, [str(labels[i]) for i in ticks])
    ax.set_xlabel(r"Valid discriminant $d_1$ (ordered labels)", labelpad=10)
    ax.set_ylabel(r"Valid discriminant $d_2$ (ordered labels)", labelpad=10)
    ax.set_title(r"Irreducible components of $\mathcal{C}_{d_1}\cap\mathcal{C}_{d_2}$",
                 loc="left", fontsize=18, pad=36, color="#15333c")
    ax.text(0, 1.025, f"Complete finite catalogue: {index['pair_count']:,} unordered pairs; "
            f"{len(labels)} valid labels through {index['max_discriminant']}",
            transform=ax.transAxes, fontsize=10, color="#52626a")
    bar = fig.colorbar(image, ax=ax, shrink=.82, pad=.035)
    bar.set_label("Number of irreducible components", labelpad=12)
    for spine in ax.spines.values():
        spine.set_color("#bac3c6")
    fig.text(.105, .042,
             "Each cell is one pair of distinct valid labels. Counts are repeated symmetrically; the diagonal is excluded.\n"
             "Exact lattice enumeration. Component counts do not decide rationality.",
             fontsize=9, color="#52626a", linespacing=1.6)
    fig.subplots_adjust(left=.105, right=.94, top=.87, bottom=.13)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
