"""Generate placeholder reel-strip CSVs for BANG.

These are scaffold values — meant to make `make run GAME=bang` produce
something. Real reel composition gets tuned via simulation runs against
RTP targets (see ../../crossfire-bang/docs/GDD.md §1 verification targets).

Usage:
    python3 gen_placeholder_reels.py

Output:
    reels/BR0.csv    (base reel)
    reels/FR0.csv    (free-spins reel)
    reels/WCAP.csv   (forced-max-win distribution)
"""

import csv
import os
import random


REEL_LEN = 250         # rows per CSV — matches the cluster sample density
NUM_REELS = 5          # columns per CSV
SEED = 20260519        # deterministic — change to reshuffle

REELS_DIR = os.path.join(os.path.dirname(__file__), "reels")


def make_reels(distribution: dict[str, int], label: str) -> list[list[str]]:
    """Generate a REEL_LEN x NUM_REELS grid with symbols sampled by weight."""
    rng = random.Random(f"{SEED}-{label}")
    population, weights = zip(*distribution.items())
    rows = []
    for _ in range(REEL_LEN):
        row = rng.choices(population, weights=weights, k=NUM_REELS)
        rows.append(row)
    return rows


def write_csv(path: str, rows: list[list[str]]) -> None:
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


def main() -> None:
    os.makedirs(REELS_DIR, exist_ok=True)

    # Base reel — dynamite density reduced since wilds substitute for any
    # symbol (so even rare DS/DB contribute to many clusters). Iter pre-wild
    # had DS 8%, DB 2%; iter wild starts at DS 3%, DB 0.5% — will tune.
    base_dist = {
        "L1": 18, "L2": 18, "L3": 18, "L4": 18,
        "H4": 9,  "H3": 7,  "H2": 5,  "H1": 3.5,
        "DS": 3,  "DB": 0.5,
    }

    # Free-spins reel — slightly more dynamite than base; with wilds doing
    # the substitution work, density doesn't need to be huge.
    free_dist = {
        "L1": 15, "L2": 15, "L3": 15, "L4": 15,
        "H4": 10, "H3": 8, "H2": 6, "H1": 4,
        "DS": 6, "DB": 1,
    }

    # Forced-max-win reel — heavy on Big Dyn + high pays to make chain-detonation
    # spins reach the 10,000x cap when the wincap distribution selects it.
    wcap_dist = {
        "DB": 30, "DS": 25,
        "H1": 15, "H2": 10, "H3": 8,  "H4": 5,
        "L1": 2,  "L2": 2,  "L3": 2,  "L4": 1,
    }

    for label, dist in (("BR0", base_dist), ("FR0", free_dist), ("WCAP", wcap_dist)):
        path = os.path.join(REELS_DIR, f"{label}.csv")
        write_csv(path, make_reels(dist, label))
        print(f"wrote {path} ({REEL_LEN} rows x {NUM_REELS} cols)")


if __name__ == "__main__":
    main()
