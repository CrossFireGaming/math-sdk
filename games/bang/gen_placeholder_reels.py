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

    # Base reel — gems dominate, dynamites at scaffold-target rates
    # (Small Dyn ~8%, Big Dyn ~2% per GDD §11 #2 recommendation).
    base_dist = {
        "L1": 17, "L2": 17, "L3": 17, "L4": 17,
        "H4": 8,  "H3": 6,  "H2": 5,  "H1": 3,
        "DS": 8,  "DB": 2,
    }

    # Free-spins reel — high-pay-weighted to lift raw freegame wins so
    # the multiplier mechanism can land Eddie's distribution shape (50x
    # mode with tiered tails). Free spins feel meaningfully different
    # from base — more action, bigger pays, more dynamite cascades.
    free_dist = {
        "L1": 7, "L2": 7, "L3": 7, "L4": 7,
        "H4": 15, "H3": 12, "H2": 9, "H1": 6,
        "DS": 22, "DB": 8,
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
