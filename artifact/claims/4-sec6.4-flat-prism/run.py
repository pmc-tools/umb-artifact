# Sec. 6.4: random stochastic games generated with umbi. Plain PRISM does not support games, so each game is turned
# into an MDP with the same states, choices and branches, written as UMB and encoded explicitly in the PRISM language
# (one command per choice, as in umbi's examples/misc/ats_smg_to_prism.py), for 10k and 100k states.
# PRISM then builds the model from both files:
#   prism -ex -importmodel game-<n>.umb
#   prism -ex game-<n>.prism
#   python run.py                 time limit of one hour per PRISM call, as in the paper  (~1 h)
#   python run.py --timeout 60    time limit of one minute                                (~2 min)
import argparse
import os
import subprocess
import time

import umbi
from umbi.ats.examples.random_game import random_game


def write_flat_prism(mdp, path):
    with open(path, "w") as f:
        f.write(f"mdp\n\nmodule main\n\tstate: [0..{mdp.num_states - 1}];\n\n")
        for state in range(mdp.num_states):
            for choice in mdp.get_state_choices(state):
                action = mdp.choice_action_to_name[mdp.choice_to_choice_action[choice]]
                branches = " + ".join(
                    f"{mdp.branch_to_probability[b]} : (state'={mdp.branch_to_target[b]})"
                    for b in mdp.get_choice_branches(choice)
                )
                f.write(f"\t[{action}] state={state} -> {branches};\n")
        init = " | ".join(f"state={s}" for s in mdp.initial_states)
        f.write(f"endmodule\n\ninit {init} endinit\n")


def run_prism(timeout, *cmd):
    """Runs a PRISM command with a time limit (s) and prints the command, the model type and the time.
    (PRISM's own output is not shown: it lists every action of the model.)"""
    print("$ " + " ".join(cmd), flush=True)
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"timeout after {time.time() - start:.1f} s")
        return
    if result.returncode != 0:
        print(f"error:\n{result.stdout[-2000:]}")
        return
    model_type = [line for line in result.stdout.splitlines() if line.startswith("Type:")][0].split()[1]
    print(f"built {model_type} after {time.time() - start:.1f} s", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=3600, help="time limit per PRISM call in seconds")
    timeout = parser.parse_args().timeout
    os.makedirs("/tmp/flat-prism", exist_ok=True)
    os.chdir("/tmp/flat-prism")

    for n in (10000, 100000):
        print(f"######## {n} states")
        game = random_game(n, seed=0)
        game.num_players = 1  # SMG -> MDP: a single player owns all states
        game.state_to_player = [0] * n
        game.player_to_name = None  # PRISM rejects player names in non-game models
        umb, flat = f"game-{n}.umb", f"game-{n}.prism"
        umbi.ats.write(game, umb)
        write_flat_prism(game, flat)
        print(f"{game.num_states} states, {game.num_choices} choices, {game.num_branches} branches")
        print(f"{umb}: {os.path.getsize(umb) / 2**20:.1f} MiB, {flat}: {os.path.getsize(flat) / 2**20:.1f} MiB")
        run_prism(timeout, "prism", "-ex", "-importmodel", umb)
        run_prism(timeout, "prism", "-ex", flat)


if __name__ == "__main__":
    main()
