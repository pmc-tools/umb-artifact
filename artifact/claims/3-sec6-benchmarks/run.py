# Sec. 6.1-6.3, Figs. 5-6: the benchmarks of umb-benchmarking/. Results go to /artifact/results/<mode>/.
#   python run.py smoke    benchmarks on one small model                                       (~1 min)
#   python run.py replot   Figs. 5-6 and the numbers of Sec. 6.1-6.3 from the logs of our runs  (~1 min)
#   python run.py subset   benchmarks on 20 of the 36 models, 1800 s limit, 1 repetition      (~5.5 h)
#   python run.py full     benchmarks on all 36 models, 7200 s limit, 5 repetitions           (~2 weeks)
#   --jobs N               with smoke, subset or full: N runs at a time instead of one (needs N times the RAM)
import argparse
import os
import re
import shutil
import subprocess

BENCH = "/artifact/umb-benchmarking"
RESULTS = "/artifact/results"


def run(*cmd, cwd=None, **kwargs):
    """Prints the command, then runs it."""
    print("$ " + (f"cd {cwd} && " if cwd else "") + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True, **kwargs)


def plots(csv, out):
    """The numbers of Sec. 6.1-6.3 and Figs. 5-6 from the csv files."""
    if os.path.abspath(csv) != os.path.abspath(f"{out}/csv"):
        shutil.copytree(csv, f"{out}/csv", dirs_exist_ok=True)
    with open(f"{out}/paper_numbers.txt", "w") as f:
        run("python3", f"{BENCH}/scripts/paper_numbers.py", "csv", f"{BENCH}/models", cwd=out, stdout=f)
    print(open(f"{out}/paper_numbers.txt").read())
    run("python3", f"{BENCH}/scripts/create_tex.py", "csv", cwd=out)
    for _ in range(2):  # twice for the legends
        run("pdflatex", "-interaction=batchmode", "plots.tex", cwd=out, stdout=subprocess.DEVNULL)
    print(f"Plots: {out}/plots.pdf, numbers: {out}/paper_numbers.txt")


def replot(out):
    """The csv files from the logs of our runs, then the plots."""
    os.makedirs(f"{out}/csv", exist_ok=True)
    run("tar", "-xzf", f"{BENCH}/experiments-paper/logs-paper.tar.gz", cwd=out, stderr=subprocess.DEVNULL)
    run("python3", f"{BENCH}/scripts/create_csv.py", "../logs", f"{BENCH}/models", cwd=f"{out}/csv",
        stdout=subprocess.DEVNULL)
    plots(f"{out}/csv", out)


def bench(script, out, jobs=1):
    """Runs a script of the harness and copies its results (not the exported models).
    With jobs > 1, runs a copy of the script in which xargs runs that many invocations at a time
    (the harness's run.py runs a single invocation of a json file by its index)."""
    if jobs > 1:
        sh = open(f"{BENCH}/{script}.sh").read()
        parallel = (r"""python3 -c "import json; print(*range(len(json.load(open('\1')))))" """
                    rf"| xargs -n 1 -P {jobs} python3 ../scripts/run.py \1")
        sh = re.sub(r"python3 \.\./scripts/run\.py (\S+) all", parallel, sh)
        with open(f"{BENCH}/{script}-jobs.sh", "w") as f:
            f.write(sh)
        os.chmod(f"{BENCH}/{script}-jobs.sh", 0o755)
        run("grep", "xargs", f"{BENCH}/{script}-jobs.sh")
        run(f"{BENCH}/{script}-jobs.sh", stdin=subprocess.DEVNULL)
    else:
        run(f"{BENCH}/{script}.sh", stdin=subprocess.DEVNULL)
    exp = f"{BENCH}/experiments-{script}"
    for name in os.listdir(exp):
        if name != "models":
            src, dst = os.path.join(exp, name), os.path.join(out, "experiments", name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy(src, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["smoke", "replot", "subset", "full"])
    parser.add_argument("--jobs", type=int, default=1, help="runs at a time (smoke, subset, full)")
    args = parser.parse_args()
    mode = args.mode
    out = f"{RESULTS}/{mode}"
    try:
        if mode == "smoke":
            os.makedirs(f"{out}/experiments", exist_ok=True)
            bench("smoketest", out, args.jobs)
        elif mode == "replot":
            replot(out)
        elif mode in ("subset", "full"):
            os.makedirs(f"{out}/experiments", exist_ok=True)
            bench("subset" if mode == "subset" else "all", out, args.jobs)
            plots(f"{out}/experiments/csv", f"{out}/plots")
        print(f"Done: results/{mode}/")
    finally:
        # The container runs as root; give the results to the owner of the mounted results directory.
        if os.path.exists(RESULTS):
            st = os.stat(RESULTS)
            subprocess.run(["chown", "-R", f"{st.st_uid}:{st.st_gid}", RESULTS], check=True)


if __name__ == "__main__":
    main()
