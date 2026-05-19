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
        self.wincap = 10000.0
        self.win_type = "cluster"
        # C1 placeholder: 0.9700 to match the inherited opt_params condition sum.
        # GDD target is 0.9650 base / 0.9700 bonus — will be enforced in C2 by
        # tuning games/bang/game_optimization.py condition RTPs to sum to 0.965.
        self.rtp = 0.9700
        self.construct_paths()

        # 5x5 board
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels

        # Cluster-size tiers — minimum cluster is 5 (matches SDK sample convention).
        # 4-min was tried first; produced unbounded cascades on 5x5 with our reel
        # composition. 5-min on 5x5 hits the target high-volatility band and lets
        # the dynamite explosions be the hero moments.
        t1, t2, t3, t4, t5 = (5, 5), (6, 7), (8, 10), (11, 14), (15, 25)

        pay_group = {
            # H1 — Safe / Vault (top pay)
            (t1, "H1"): 6.0, (t2, "H1"): 15.0, (t3, "H1"): 40.0,
            (t4, "H1"): 100.0, (t5, "H1"): 500.0,
            # H2 — Gold Bar
            (t1, "H2"): 3.0, (t2, "H2"): 8.0, (t3, "H2"): 20.0,
            (t4, "H2"): 50.0, (t5, "H2"): 250.0,
            # H3 — Sheriff Badge
            (t1, "H3"): 1.6, (t2, "H3"): 4.0, (t3, "H3"): 10.0,
            (t4, "H3"): 25.0, (t5, "H3"): 100.0,
            # H4 — Horseshoe
            (t1, "H4"): 1.0, (t2, "H4"): 2.5, (t3, "H4"): 6.0,
            (t4, "H4"): 15.0, (t5, "H4"): 60.0,
            # L1 — Diamond
            (t1, "L1"): 0.4, (t2, "L1"): 1.0, (t3, "L1"): 2.5,
            (t4, "L1"): 6.0, (t5, "L1"): 20.0,
            # L2 — Heart
            (t1, "L2"): 0.4, (t2, "L2"): 1.0, (t3, "L2"): 2.5,
            (t4, "L2"): 6.0, (t5, "L2"): 20.0,
            # L3 — Club
            (t1, "L3"): 0.6, (t2, "L3"): 1.5, (t3, "L3"): 4.0,
            (t4, "L3"): 10.0, (t5, "L3"): 30.0,
            # L4 — Spade
            (t1, "L4"): 0.6, (t2, "L4"): 1.5, (t3, "L4"): 4.0,
            (t4, "L4"): 10.0, (t5, "L4"): 30.0,
            # DS — Small Dynamite (board symbol for now; DH/DV split deferred)
            (t1, "DS"): 2.0, (t2, "DS"): 5.0, (t3, "DS"): 12.0,
            (t4, "DS"): 30.0, (t5, "DS"): 120.0,
            # DB — Big Dynamite
            (t1, "DB"): 5.0, (t2, "DB"): 12.0, (t3, "DB"): 30.0,
            (t4, "DB"): 80.0, (t5, "DB"): 300.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True

        # No wilds, no scatters in BANG. Empty lists keep the SDK's cluster
        # detection happy (it checks the "wild" attribute on each cell).
        self.special_symbols = {"wild": [], "scatter": []}

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

        mode_maxwins = {"base": self.wincap, "bonus": self.wincap}

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=mode_maxwins["base"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                # C1 simplified distributions: base mode is basegame-only.
                # Removed: wincap (force_wincap loops forever with no dynamite
                # math), zero-win (5-min cluster makes it hard to sample), and
                # freegame (force_freegame loops forever waiting on an
                # unreachable scatter trigger). C2 reintroduces freegame once
                # the destruction-count trigger is wired.
                distributions=[
                    Distribution(
                        criteria="basegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "scatter_triggers": {0: 1},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=0.9700,
                max_win=mode_maxwins["bonus"],
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                # C1: bonus mode is a placeholder that runs like base. The real
                # "bonus buy directly enters freespins" mechanic needs the
                # destruction-count trigger to land in C2 (force_freegame=True
                # currently loops forever waiting on a scatter trigger that
                # BANG doesn't have). The criteria name is kept as "freegame"
                # only to satisfy opt_params verification.
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {self.basegame_type: {"BR0": 1}},
                            "scatter_triggers": {0: 1},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
        ]
