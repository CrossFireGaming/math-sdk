"""Main file for generating results for BANG."""

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    # C2-G final confidence pass — 1M base / 100k bonus.
    num_threads = 4
    rust_threads = 4
    batching_size = 10000
    compression = False
    profiling = False

    # 1M base + 100k feature for proper RTP convergence across "many
    # many spins" per Eddie. ~10 min wall-clock with 4 threads.
    num_sim_args = {
        "base": int(1e6),
        "feature": int(1e5),
    }

    # Optimization off during scaffolding — runs faster, and tuning the
    # placeholder reels with the optimizer would be wasted work.
    run_conditions = {
        "run_sims": True,
        "run_optimization": False,
        "run_analysis": True,
        # Format checks expect compressed books (.zst) which we don't produce
        # while compression=False. Re-enable for the first production run.
        "run_format_checks": False,
    }
    target_modes = ["base", "feature"]

    config = GameConfig()
    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
