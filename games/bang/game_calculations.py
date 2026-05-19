"""BANG game calculations — Big/Small Dynamite area-effect resolution.

Replaces the cluster sample's grid-multiplier mechanic with BANG's
dynamite-driven destruction:

- DS clusters (Small Dynamite, 5+ connected): each cluster member destroys
  its row AND column (plus pattern, up to 9 cells per member). DH/DV
  directional variants are deferred — see GDD §2.1.
- DB clusters (Big Dynamite, 5+ connected): each cluster member destroys
  a 3x3 area centered on itself, clipped to grid edges.

Destruction count is collected into return_data["destructionCount"] for
the 50-cell bonus trigger (wired in game_executables.py).
"""

from src.executables.executables import Executables
from src.calculations.cluster import Cluster
from src.config.config import Config


class GameCalculations(Executables):
    """BANG-specific cluster eval with dynamite area-effects."""

    def evaluate_clusters_with_dynamite(
        self,
        config: Config,
        board: list,
        clusters: dict,
        global_multiplier: int = 1,
        return_data: dict = {"totalWin": 0, "wins": []},
    ):
        """Pay clusters, then resolve dynamite area-effects before the tumble.

        Mutates `board` (sets .explode = True on destroyed cells) and
        appends to return_data. Returns (board, return_data) for caller chaining.
        """
        total_win = 0
        destruction_count = 0

        for sym in clusters:
            for cluster in clusters[sym]:
                size = len(cluster)
                if (size, sym) not in config.paytable:
                    continue

                sym_win = config.paytable[(size, sym)]
                symwin_mult = sym_win * global_multiplier
                total_win += symwin_mult

                json_positions = [{"reel": p[0], "row": p[1]} for p in cluster]
                central = Cluster.get_central_cluster_position(json_positions)
                return_data["wins"].append(
                    {
                        "symbol": sym,
                        "clusterSize": size,
                        "win": symwin_mult,
                        "positions": json_positions,
                        "meta": {
                            "globalMult": global_multiplier,
                            "clusterMult": 1,
                            "winWithoutMult": sym_win,
                            "overlay": {"reel": central[0], "row": central[1]},
                        },
                    }
                )

                # Standard cluster destruction
                for r, c in cluster:
                    if not board[r][c].explode:
                        board[r][c].explode = True
                        destruction_count += 1

                # Dynamite area-effects
                if sym == "DS":
                    # Plus pattern: each Small Dynamite destroys its row AND column.
                    # C2.x will split into DH = row only / DV = column only variants
                    # once the board cell type supports a directional attribute.
                    for r, c in cluster:
                        for rr_idx in range(len(board[r])):
                            if not board[r][rr_idx].explode:
                                board[r][rr_idx].explode = True
                                destruction_count += 1
                        for cc_idx in range(config.num_reels):
                            if not board[cc_idx][c].explode:
                                board[cc_idx][c].explode = True
                                destruction_count += 1
                elif sym == "DB":
                    # 3x3 area centered on each Big Dynamite, clipped to grid edges
                    for r, c in cluster:
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                rr, cc = r + dr, c + dc
                                if 0 <= rr < config.num_reels and 0 <= cc < len(board[rr]):
                                    if not board[rr][cc].explode:
                                        board[rr][cc].explode = True
                                        destruction_count += 1

        return_data["totalWin"] += total_win
        return_data["destructionCount"] = (
            return_data.get("destructionCount", 0) + destruction_count
        )

        return board, return_data
