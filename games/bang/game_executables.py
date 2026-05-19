from game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from src.calculations.statistics import get_random_outcome
from game_events import update_grid_mult_event
from src.events.events import update_freespin_event


# BANG bonus trigger: destroy this many cells in one spin's full cascade
# chain to trigger the free-spins round. See GDD §5.
DESTRUCTION_TRIGGER_THRESHOLD = 50
FREESPINS_AWARDED_ON_TRIGGER = 10
FREESPINS_AWARDED_ON_RETRIGGER = 5

# BANG bonus-round TNT-Crate multiplier collection (GDD §5).
# C2-C math-only implementation: each free spin has MULTIPLIER_SPAWN_PROB
# chance to "land" a TNT-Crate multiplier with value sampled from MULT_VALUES.
# Values accumulate into self.bonus_multiplier_sum across the round; at
# end_freespin the freegame total is multiplied by max(1, sum). The board
# representation (rendering M crates as a visible symbol) is deferred — only
# the math contribution lands in C2-C.
MULT_VALUES = {2: 35, 3: 25, 5: 18, 10: 12, 25: 6, 100: 3, 500: 1}
# C2-E tuning history (1k base / 200 bonus sims):
#   iter 0: 0.25 + paytable×1.0 → bonus RTP 56.86% (undershoot)
#   iter 1: 0.43 + paytable×1.0 → bonus RTP 106.88% (close)
#   iter 2: 0.39 + paytable×1.0, dropped wincap/freegame distros from base
#           → base RTP 28.20%, bonus 113.74%
#   iter 3: 0.39 + paytable×3.5 → base RTP 98.70% (+2.2%), bonus 396.43% (way over)
#   iter 4: 0.10 + paytable×3.5 → measuring
# Multiplier-spawn-prob and paytable scale are roughly orthogonal levers:
# base RTP scales with paytable, bonus RTP additionally scales with mult.
MULTIPLIER_SPAWN_PROB = 0.10


class GameExecutables(GameCalculations):
    """BANG game-specific orchestration.

    Differences from the inherited cluster sample (0_0_cluster):
    - get_clusters_update_wins() calls evaluate_clusters_with_dynamite
      (BANG-specific, in game_calculations.py) instead of
      evaluate_clusters_with_grid. Grid-position multipliers are not
      used; cluster pays are flat (subject to global_multiplier).
    - A per-spin destruction counter (self.spin_destruction_count) is
      accumulated from each cluster-eval pass.
    - check_fs_condition / check_freespin_entry / update_freespin_amount
      / update_fs_retrigger_amt are overridden to trigger free spins
      from destruction count instead of scatter count.
    """

    def reset_grid_mults(self):
        """Initialize per-cell multipliers (kept for SDK compatibility;
        not used by BANG's payout math)."""
        self.position_multipliers = [
            [0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)
        ]

    def update_grid_mults(self):
        """No-op for BANG — multipliers come from collected TNT-Crate
        symbols (C2-C), not grid-position activations. Kept as a stub so
        the inherited gamestate.run_freespin can still call it."""
        if self.win_data.get("totalWin", 0) > 0:
            update_grid_mult_event(self)

    def get_clusters_update_wins(self):
        """Find clusters, pay them, resolve dynamite area-effects, and
        increment the per-spin destruction counter."""
        clusters = Cluster.get_clusters(self.board, "wild")
        return_data = {"totalWin": 0, "wins": []}
        self.board, self.win_data = self.evaluate_clusters_with_dynamite(
            config=self.config,
            board=self.board,
            clusters=clusters,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )
        if not hasattr(self, "spin_destruction_count"):
            self.spin_destruction_count = 0
        self.spin_destruction_count += self.win_data.get("destructionCount", 0)

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}
        # Reset destruction counter so each free-spin can independently
        # re-trigger when it hits the threshold.
        self.spin_destruction_count = 0

        # BANG C2-C: roll for a TNT-Crate multiplier spawn this spin.
        # If hit, add its value to the running bonus_multiplier_sum;
        # applied to the freegame total in end_freespin.
        if get_random_outcome({0: 1 - MULTIPLIER_SPAWN_PROB, 1: MULTIPLIER_SPAWN_PROB}) == 1:
            value = get_random_outcome(MULT_VALUES)
            if not hasattr(self, "bonus_multiplier_sum"):
                self.bonus_multiplier_sum = 0
            self.bonus_multiplier_sum += value

    # ---- Destruction-count freespin trigger (replaces scatter-based) ----

    def check_fs_condition(self, scatter_key: str = "scatter") -> bool:
        """BANG: bonus triggers when ≥50 cells were destroyed in this spin's
        full cascade chain (GDD §5), OR when the current bet-mode distribution
        sets force_freegame (bonus buy path — the player paid for direct entry).
        Replaces the SDK's scatter-count check.
        """
        if self.repeat:
            return False
        if getattr(self, "spin_destruction_count", 0) >= DESTRUCTION_TRIGGER_THRESHOLD:
            return True
        if self.get_current_distribution_conditions().get("force_freegame"):
            return True
        return False

    def check_freespin_entry(self, scatter_key: str = "scatter") -> bool:
        """BANG: allow freespin entry when either the destruction-count
        threshold fired this spin OR the current bet-mode distribution sets
        force_freegame (used by bonus buy)."""
        if getattr(self, "spin_destruction_count", 0) >= DESTRUCTION_TRIGGER_THRESHOLD:
            return True
        if self.get_current_distribution_conditions().get("force_freegame"):
            return True
        self.repeat = True
        return False

    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        """BANG: trigger awards a flat 10 free spins (GDD §5). Doesn't scale
        with destruction count — the 50-cell threshold is binary."""
        self.tot_fs = FREESPINS_AWARDED_ON_TRIGGER

    def update_fs_retrigger_amt(self, scatter_key: str = "scatter") -> None:
        """BANG: hitting the 50-cell threshold during a free spin re-triggers
        +5 spins (GDD §5)."""
        if getattr(self, "spin_destruction_count", 0) >= DESTRUCTION_TRIGGER_THRESHOLD:
            self.tot_fs += FREESPINS_AWARDED_ON_RETRIGGER

    def end_freespin(self) -> None:
        """BANG: apply collected TNT-Crate multipliers to the freegame total
        before emitting the freespin-end event (GDD §5).

        freegame_total *= max(1, sum_of_collected_multipliers)

        max(1, ...) preserves the unmultiplied total when no multipliers
        landed during the round, matching Sweet Bonanza convention.
        """
        mult_sum = getattr(self, "bonus_multiplier_sum", 0)
        if mult_sum > 0 and self.win_manager.freegame_wins > 0:
            original = self.win_manager.freegame_wins
            multiplied = original * mult_sum
            delta = multiplied - original
            self.win_manager.freegame_wins = multiplied
            self.win_manager.running_bet_win += delta
            # Wincap is enforced in update_final_win via min(...); no need to
            # clamp here (and we want the books to reflect the raw multiplied
            # value so the frontend can render the actual collected total).
        super().end_freespin()
