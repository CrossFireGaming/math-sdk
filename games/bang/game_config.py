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

        # C2-E iter 3: paytable scaled 3.5x from the original GDD draft.
        # iter 2 (original draft) measured base RTP at 28.20% across 1000 sims;
        # target is 96.5%, so multiplied uniformly by 3.4 (rounded to 3.5 for
        # cleaner numbers). C2-F (proper optimizer-driven tuning) will
        # rebalance properly — this is the placeholder until then.
        pay_group = {
            # H1 — Safe / Vault (top pay)
            (t1, "H1"): 21.0, (t2, "H1"): 52.5, (t3, "H1"): 140.0,
            (t4, "H1"): 350.0, (t5, "H1"): 1750.0,
            # H2 — Gold Bar
            (t1, "H2"): 10.5, (t2, "H2"): 28.0, (t3, "H2"): 70.0,
            (t4, "H2"): 175.0, (t5, "H2"): 875.0,
            # H3 — Sheriff Badge
            (t1, "H3"): 5.6, (t2, "H3"): 14.0, (t3, "H3"): 35.0,
            (t4, "H3"): 87.5, (t5, "H3"): 350.0,
            # H4 — Horseshoe
            (t1, "H4"): 3.5, (t2, "H4"): 8.75, (t3, "H4"): 21.0,
            (t4, "H4"): 52.5, (t5, "H4"): 210.0,
            # L1 — Diamond
            (t1, "L1"): 1.4, (t2, "L1"): 3.5, (t3, "L1"): 8.75,
            (t4, "L1"): 21.0, (t5, "L1"): 70.0,
            # L2 — Heart
            (t1, "L2"): 1.4, (t2, "L2"): 3.5, (t3, "L2"): 8.75,
            (t4, "L2"): 21.0, (t5, "L2"): 70.0,
            # L3 — Club
            (t1, "L3"): 2.1, (t2, "L3"): 5.25, (t3, "L3"): 14.0,
            (t4, "L3"): 35.0, (t5, "L3"): 105.0,
            # L4 — Spade
            (t1, "L4"): 2.1, (t2, "L4"): 5.25, (t3, "L4"): 14.0,
            (t4, "L4"): 35.0, (t5, "L4"): 105.0,
            # DS — Small Dynamite
            (t1, "DS"): 7.0, (t2, "DS"): 17.5, (t3, "DS"): 42.0,
            (t4, "DS"): 105.0, (t5, "DS"): 420.0,
            # DB — Big Dynamite
            (t1, "DB"): 17.5, (t2, "DB"): 42.0, (t3, "DB"): 105.0,
            (t4, "DB"): 280.0, (t5, "DB"): 1050.0,
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
                            # 5 = most common, 25 = rarest big hit.
                            "big_bomb_triggers": {5: 40, 8: 30, 12: 15, 16: 8, 20: 5, 25: 2},
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
        ]
