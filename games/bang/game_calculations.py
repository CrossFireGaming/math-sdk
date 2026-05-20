"""BANG game calculations — Big/Small Dynamite area-effect resolution.

Dynamites (DS, DB) are wilds — they substitute for any cluster symbol so
a cluster of "4 H1 + 1 DS" pays as a 5-H1 cluster. Each dynamite cell in
any winning cluster STILL triggers its area-effect destruction:

- DS in a winning cluster: destroys its row AND column (plus pattern).
- DB in a winning cluster: destroys a 3x3 area centered on it, clipped
  to grid edges.

The detection is per-cell (board[r][c].name) — not per-cluster-symbol —
because dynamites now ride along inside non-dynamite clusters.

Pure-dynamite clusters (5+ adjacent DS/DB with no non-wild neighbours)
don't form under the standard SDK cluster algorithm (wilds aren't valid
cluster starts). That's intended: those dynamites stay on the board
sticky-style until a non-wild cluster forms around them.

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

                # Per-cell processing: mark cluster cells exploded AND
                # trigger dynamite area-effects based on the actual cell
                # symbol (which may be DS/DB acting as a wild inside a
                # non-dynamite cluster).
                for r, c in cluster:
                    if not board[r][c].explode:
                        board[r][c].explode = True
                        destruction_count += 1

                    actual = board[r][c].name
                    if actual == "DS":
                        # Small Dynamite — destroys its row (5 cells max).
                        # Eddie's design: DS is the Tome-of-Madness "books"
                        # equivalent (small wild that detonates). DB is
                        # the bigger 3x3 bomb. DS must be SMALLER than DB.
                        for cc_idx in range(config.num_reels):
                            if not board[cc_idx][c].explode:
                                board[cc_idx][c].explode = True
                                destruction_count += 1
                    elif actual == "DB":
                        # Big Dynamite — 3x3 area centered, clipped to grid.
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
