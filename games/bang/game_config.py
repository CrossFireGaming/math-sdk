"""BANG game configuration — CrossFire Gaming.

5x5 cluster + tumble, Wild-West dynamite theme.
See ../../crossfire-bang/docs/GDD.md for the full spec.

C1 scaffold notes:
- Symbol set in place, paytable per GDD §3.
- Big/Small Dynamite area-effect resolution NOT YET implemented (C2 task).
  At this stage DS / DB pay as ordinary cluster symbols.
- DH/DV variants not yet split — board uses 'DS' as the single Small-Dynamite ID.
- Bonus trigger is destruction-based, not scatter-based — placeholder
  scatter-trigger config left in so the SDK boilerplate doesn't crash;
  scatter is unreachable on the BANG reels so it never fires in base mode.
  Bonus mode entry happens via force_freegame in the 'bonus' BetMode.
"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Singleton BANG game configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "bang"
        self.provider_number = 0
        self.working_name = "BANG"
        self.wincap = 50000.0
        self.win_type = "cluster"
        # Long-term target is Tome of Hades's 97.70% RTP. Kept at 0.97
        # here to match the inherited opt_params sum; opt_params will be
        # rebalanced to 0.977 when we're in the right band naturally.
        self.rtp = 0.9700
        self.construct_paths()

        # 5x5 board
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels

        # 4-min cluster + 6 tiers to match Tome of Hades structure:
        # 4-5 / 6-7 / 8-11 / 12-15 / 16-19 / 20-25 (full-board on 5x5 is 25).
        # The "20-25" top tier is where the big wins land.
        t1, t2, t3, t4, t5, t6 = (4, 5), (6, 7), (8, 11), (12, 15), (16, 19), (20, 25)

        # Paytable: Tome of Hades shape (tiny small-cluster pays, big top
        # tier), scaled up so base RTP lands in target band given how
        # often 4-cluster wins fire with wilds + 4-min cluster.
        pay_group = {
            # H1 — Safe / Vault (top pay)
            (t1, "H1"): 2.11, (t2, "H1"): 5.05, (t3, "H1"): 12.64,
            (t4, "H1"): 33.7, (t5, "H1"): 105.3, (t6, "H1"): 421.2,
            # H2 — Gold Bar
            (t1, "H2"): 1.47, (t2, "H2"): 3.16, (t3, "H2"): 7.58,
            (t4, "H2"): 21.06, (t5, "H2"): 54.76, (t6, "H2"): 252.72,
            # H3 — Sheriff Badge
            (t1, "H3"): 0.84, (t2, "H3"): 2.11, (t3, "H3"): 5.05,
            (t4, "H3"): 12.64, (t5, "H3"): 33.7, (t6, "H3"): 126.36,
            # H4 — Horseshoe
            (t1, "H4"): 0.59, (t2, "H4"): 1.47, (t3, "H4"): 3.37,
            (t4, "H4"): 7.58, (t5, "H4"): 21.06, (t6, "H4"): 75.82,
            # L1 — Diamond
            (t1, "L1"): 0.3, (t2, "L1"): 0.63, (t3, "L1"): 1.47,
            (t4, "L1"): 3.37, (t5, "L1"): 8.42, (t6, "L1"): 29.48,
            # L2 — Heart
            (t1, "L2"): 0.3, (t2, "L2"): 0.63, (t3, "L2"): 1.47,
            (t4, "L2"): 3.37, (t5, "L2"): 8.42, (t6, "L2"): 29.48,
            # L3 — Club
            (t1, "L3"): 0.34, (t2, "L3"): 0.76, (t3, "L3"): 1.89,
            (t4, "L3"): 5.05, (t5, "L3"): 12.64, (t6, "L3"): 46.33,
            # L4 — Spade
            (t1, "L4"): 0.34, (t2, "L4"): 0.76, (t3, "L4"): 1.89,
            (t4, "L4"): 5.05, (t5, "L4"): 12.64, (t6, "L4"): 46.33,
            # DS — wild, unreachable as cluster start (kept for safety)
            (t1, "DS"): 0.84, (t2, "DS"): 2.11, (t3, "DS"): 5.05,
            (t4, "DS"): 12.64, (t5, "DS"): 33.7, (t6, "DS"): 126.36,
            # DB — wild, unreachable
            (t1, "DB"): 1.47, (t2, "DB"): 3.16, (t3, "DB"): 7.58,
            (t4, "DB"): 21.06, (t5, "DB"): 54.76, (t6, "DB"): 252.72,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True

        # Dynamites are wilds — they substitute for any cluster symbol AND
        # still trigger their area-effect destruction when in a winning
        # cluster (see evaluate_clusters_with_dynamite for the per-cell
        # detection). DB forcing on feature spins happens via custom
        # placement in game_executables.draw_board (the SDK's
        # force_special_board only works with Symbol-slot attributes
        # like "wild" or "scatter").
        self.special_symbols = {
            "wild": ["DS", "DB"],
            "scatter": [],
        }

        # Placeholder scatter triggers — unreachable on BANG reels (no 'S' symbol).
        # Bonus entry happens via force_freegame in the bonus BetMode below.
        # C2 will replace this with a destruction-count trigger.
        self.freespin_triggers = {
            self.basegame_type: {99: 10},
            self.freegame_type: {99: 5},
        }
        self.anticipation_triggers = {
            self.basegame_type: 98,
            self.freegame_type: 98,
        }

        # BANG doesn't use the cluster sample's grid-position-multiplier mechanic
        # (replaced in C2 by collected TNT-crate multipliers). Set to 1 to keep
        # the inherited evaluate_clusters_with_grid math harmless: cluster
        # payouts get multiplied by max(sum_of_grid_mults, 1) == 1.
        self.maximum_board_mult = 1

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        mode_maxwins = {"base": self.wincap, "feature": self.wincap}

        # Shared reel_weights pattern — every distribution needs both
        # basegame and freegame entries because organic bonus triggers
        # (destruction count >= 50) can flip gametype mid-spin.
        _shared_reel_weights = {
            self.basegame_type: {"BR0": 1},
            self.freegame_type: {"FR0": 1},
        }

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=mode_maxwins["base"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="0",
                        quota=0.7,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": _shared_reel_weights,
                            "scatter_triggers": {0: 1},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=0.3,
                        conditions={
                            "reel_weights": _shared_reel_weights,
                            "scatter_triggers": {0: 1},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            # FEATURE SPIN (replaces bonus buy per design pivot):
            # A single spin that costs more than a regular bet, lands 5-25
            # Big Dynamites on the board, and has a *chance* of triggering
            # the free-spins round via the destruction count crossing 50.
            # No guaranteed free spins — the player paid for the bombs,
            # not for free spins directly. Tome-of-Madness-style.
            BetMode(
                name="feature",
                cost=20.0,
                rtp=self.rtp,
                max_win=mode_maxwins["feature"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="feature",
                        quota=1.0,
                        conditions={
                            "reel_weights": _shared_reel_weights,
                            "scatter_triggers": {0: 1},
                            # Number of Big Dynamites forced onto the
                            # feature-spin board (sampled by weight).
                            # Tone-of-Madness style: paid feature where
                            # player gets a chance at bonus. Pulled bomb
                            # counts down from 5-25 to 3-15 — wilds make
                            # each bomb very impactful so we don't need many.
                            "big_bomb_triggers": {3: 50, 4: 25, 5: 15, 7: 6, 10: 3, 15: 1},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
        ]
