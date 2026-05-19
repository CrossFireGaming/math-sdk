from game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from game_events import update_grid_mult_event
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """BANG game-specific orchestration.

    Differences from the inherited cluster sample (0_0_cluster):
    - get_clusters_update_wins() calls evaluate_clusters_with_dynamite
      (BANG-specific, in game_calculations.py) instead of
      evaluate_clusters_with_grid. Grid-position multipliers are not
      used; cluster pays are flat (subject to global_multiplier).
    - A per-spin destruction counter (self.spin_destruction_count) is
      accumulated from each cluster-eval pass — this feeds the 50-cell
      bonus trigger (C2-B will hook into check_fs_condition).
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

    def reset_spin_destruction_count(self):
        """Reset the per-spin destruction counter at the start of a spin."""
        self.spin_destruction_count = 0

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
