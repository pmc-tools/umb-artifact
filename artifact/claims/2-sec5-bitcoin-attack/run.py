# Sec. 5, use case (2): Storm builds, minimises and exports the bitcoin-attack MA to UMB, and mcsta checks the
# time-bounded reachability property on it with the switch-step algorithm.
# Claims: Storm takes < 3 s (11475 states, 7551 after minimisation); mcsta takes 13 s; Storm with Unif+ gives
# no result within 2 minutes.
#   storm --jani ba.jani -const MALICIOUS=40,CD=50 --prop "((m_len >= 50) & (m_diff > 0))" \
#       -e dd-to-sparse --bisimulation --exportbuild ba.umb
#   python umb_reorder.py ba.umb ba-reordered.umb
#   modest mcsta ba-reordered.umb ba.properties.txt --time-bounded-alg SwitchStep
#   storm --jani ba.jani -const MALICIOUS=40,CD=50 --janiproperty -e dd-to-sparse --bisimulation    (time limit 2 min)
#   python run.py
# Model, property and umb_reorder.py by Arnd Hartmanns. mcsta currently requires the initial state to be state 0,
# while Storm puts it at an arbitrary index: umb_reorder.py moves it to index 0 (a temporary workaround).
# Expected result: Probability: 0.15435216442756577
import os
import shutil
import subprocess
import sys
import time

CLAIM = os.path.dirname(os.path.abspath(__file__))


def run(*cmd, timeout=None):
    """Runs a command, showing the command, its output and its wall-clock time.
    (Not attached to the terminal: mcsta's progress display crashes in a container terminal.)"""
    print("$ " + " ".join(cmd), flush=True)
    start = time.time()
    try:
        result = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        output = e.output.decode() if isinstance(e.output, bytes) else e.output or ""
        print(output, end="")
        print(f"\nno result after {time.time() - start:.1f} s (time limit)\n", flush=True)
        return
    print(result.stdout, end="")
    result.check_returncode()
    print(f"took {time.time() - start:.1f} s\n", flush=True)


def main():
    os.makedirs("/tmp/bitcoin-attack", exist_ok=True)
    os.chdir("/tmp/bitcoin-attack")
    for f in ("ba.jani", "ba.properties.txt"):
        shutil.copy(os.path.join(CLAIM, f), f)

    # The paper's command (--janiproperty instead of --prop) is obsolete: with it, Storm also checks the model's
    # properties itself, using Unif+ for the time-bounded one, which takes far longer than the export (see the last
    # step). --prop only gives Storm the target states, so it builds and exports the model without checking it;
    # the model is then slightly smaller than in the paper (11375 states, 7403 after minimisation).
    run("storm", "--jani", "ba.jani", "-const", "MALICIOUS=40,CD=50", "--prop", "((m_len >= 50) & (m_diff > 0))",
        "-e", "dd-to-sparse", "--bisimulation", "--exportbuild", "ba.umb")
    run(sys.executable, os.path.join(CLAIM, "umb_reorder.py"), "ba.umb", "ba-reordered.umb")
    run("modest", "mcsta", "ba-reordered.umb", "ba.properties.txt", "--time-bounded-alg", "SwitchStep")

    # Storm checks the properties itself (the paper's command, without the export); Unif+ is Storm's default for
    # time-bounded reachability on MAs
    run("storm", "--jani", "ba.jani", "-const", "MALICIOUS=40,CD=50", "--janiproperty", "-e", "dd-to-sparse",
        "--bisimulation", timeout=120)


if __name__ == "__main__":
    main()
