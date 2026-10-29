# Artifact supplement for: UMB — A Unified Markov Binary Format for Probabilistic Model Checking

<!-- TODO: remove all TODOs before submission -->

- **Paper:** TACAS 2027 regular tool paper, submission 0983.
- **Badges claimed:** Available, Functional, Reusable.
- **Tested on:** amd64: Ubuntu 24.04, Docker 29.8.

## Availability

The artifact is permanently archived at [Zenodo](https://zenodo.org/records/23765898) and hosted on [GitHub](https://github.com/pmc-tools/umb-artifact).
It contains:

| File | Content |
| --- | --- |
| `umb-artifact-{amd64,arm64}.tar.gz` | the Docker image, one per architecture |
| `paper.pdf` | the submitted paper |
| `umb-artifact.zip` | the sources of the image |
| `README.md` | this file |
| `LICENSE` | license file; the tools in the image keep their own licenses (mcsta: `artifact/docker/Modest-License.txt` in `umb-artifact.zip`) |

The image is based on the [UMB Observatory](https://github.com/pmc-tools/umb-observatory) and contains Storm, PRISM, mcsta, umbi and Stormvogel (versions in [Building the image](#building-the-image)), plus the scripts and benchmarks to replicate the paper's claims.

`umb-artifact.zip` is only needed to build the image or to inspect the sources:

| Path | Content |
| --- | --- |
| `docker-bake.hcl`, `docker/` | how the image is built (tool versions in `docker-bake.hcl`) |
| `claims/<claim>/run.ipy` | one IPython script per claim of the paper; concatenated, they form the notebook `claims.ipynb` (in the image: `/artifact/claims/`) |
| `umb-benchmarking/` | the benchmarks of Sec. 6: models, scripts, and the logs of our runs ([github.com/tquatmann/umb-benchmarking](https://github.com/tquatmann/umb-benchmarking)) |

## Functionality

### Requirements

Docker on amd64 or arm64.
No network access is needed after loading the image.
Podman works as well: replace `docker` by `podman` in all commands.

Resources for the smoke test and the modes of the Sec. 6 benchmarks:

| Mode | CPU, RAM | Free disk (incl. the 10 GiB image) | Time |
| --- | --- | --- | --- |
| smoke test, replot | 1 core, 4 GiB | 10 GiB | 1 min |
| subset | 1 core, 32 GiB | 35 GiB | 5.5 h |
| full | 1 core, 32 GiB | 110 GiB | 2 weeks |
| subset, full with `--jobs N` | N cores, N × 32 GiB | as above | about 1/N of the above |

The figures do not include the downloaded image file `umb-artifact-<arch>.tar.gz` (2.8 GiB).

### Setup

Load the image for your architecture (`uname -m`: `x86_64` → amd64, `aarch64`/`arm64` → arm64):

```bash
docker load -i umb-artifact-amd64.tar.gz
```

Afterwards, you can delete `umb-artifact-amd64.tar.gz`.
Alternatively, build the image from source, see [Building the image](#building-the-image).

All commands below run in any directory.
The benchmarks of Sec. 6 write their results to `./results/<mode>/`, so create that directory first:

```bash
mkdir -p results
```

### Smoke test (1 minute)

```bash
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact ipython /artifact/claims/4-sec6-benchmarks/run.ipy smoke
```

This runs the benchmarks of Sec. 6 on one model (`consensus.4-4`) with all tools and formats.
It prints the generated command lines, then one line per run, first the 16 exports, then the 23 imports, each ending in `... done (<time>)`.
Its last line is `Done: results/smoke/`; `results/smoke/experiments/csv/` then contains no `TO`, `MO` or `ERR` entries.

### Replicating empirical claims

The claims can be replicated in two ways, with the same scripts and the same expected outputs:

- **Shell:** each claim below has a `docker run` command, which runs the claim's IPython script `claims/<claim>/run.ipy`.
- **Notebook:** all claims are in one notebook, `claims.ipynb`, which consists of the same scripts, one section per claim, with each step as a cell.
  The options of the shell commands are variables in the first code cell of its section (`MODE`, `JOBS`, `TIMEOUT`).
  Start the Jupyter server of the image:

  ```bash
  docker run --rm -p 127.0.0.1:8000:8000 -e JUPYTER_TOKEN=umb -v "$PWD/results:/artifact/results" umb-artifact
  ```

  Then open http://localhost:8000/notebooks/claims.ipynb?token=umb in a browser.
  To stop the server, press Ctrl-C in the terminal where you started it (or choose File → Shut Down in the browser).

We recommend the notebook for all claims except the `full` run of Sec. 6.1–6.3 (2 weeks), which is better run from the shell: stopping the Jupyter server or restarting the kernel aborts a running benchmark, which then has to start over.

Each claim below gives the claim, the estimated evaluation time, the shell command, and what to look for in the output, which is the same in both modes.
Absolute times depend on the machine (paper: Intel Xeon 8468, 4 cores, 32 GiB).

#### Sec. 2, Ex. 1: building a model with umbi

- **Claim:** the snippet of Ex. 1 encodes a small MDP (Fig. 2, right) with umbi, extends it with observations to a POMDP and then with players to a POSG, and writes it to a UMB file.
- **Estimated evaluation time:** 1 minute

```bash
docker run --rm -t umb-artifact ipython /artifact/claims/1-sec2-ex1-umbi/run.ipy
```

The output has one line per step (`MDP: 4 states, …`, `POMDP: 2 observations, …`, `POSG: 2 players ['p0', 'p1'], …`), then the files of `out.umb` and its `index.json`, with `"#states": 4`, `"#observations": 2` and `"#players": 2`.

#### Sec. 4, Fig. 4: textual view of a UMB file

- **Claim:** PRISM prints the UMB file of the example MDP in textual form as in Fig. 4.
- **Estimated evaluation time:** 1 minute

```bash
docker run --rm -t umb-artifact ipython /artifact/claims/2-fig4-textual-umb/run.ipy
```

After PRISM's log, the output is Fig. 4, except for the creation date and the state valuations, which PRISM prints decoded (`[(0,false),(1,false),(2,false),(2,true)]`) rather than bit-packed.

#### Sec. 5: bitcoin-attack

- **Claim:** Storm builds, minimises and exports the bitcoin-attack MA to UMB in under 3 s (11475 states, 7551 after minimisation); mcsta checks the time-bounded reachability property on it in 13 s; Storm with Unif+ gives no result within 2 minutes.
- **Estimated evaluation time:** 3 minutes

```bash
docker run --rm -t umb-artifact ipython /artifact/claims/3-sec5-bitcoin-attack/run.ipy
```

The output shows three steps, each followed by its `Wall time`:

1. Storm builds, minimises and exports the model in under 3 s.
   Its state counts, 11375 and 7403 after minimisation, are slightly smaller than in the paper: the paper's Storm command is obsolete, as it makes Storm also check the properties itself (step 3), so the export uses a command that skips checking.
2. mcsta checks the property in 13 s and prints `Probability: 0.15435216442756577`.
3. Storm with Unif+ (the paper's command, without the export) builds 11475 states, 7551 after minimisation, as in the paper, and is stopped after 2 minutes: `no result (time limit)`.

#### Sec. 6.1–6.3, Figs. 5–6: import and export times, file sizes, total times

- **Claim:** each tool loads UMB faster than the other formats (sometimes by orders of magnitude) and writes it about an order of magnitude faster than its textual formats; compression shrinks UMB files about 7× (GZip) and 23× (XZ); and UMB reduces the total model checking time for almost all models, sometimes by orders of magnitude (Figs. 5–6 and the numbers of Sec. 6.1–6.3).
- **Estimated evaluation time:** 1 minute (`replot`), 5.5 hours (`subset`) or 2 weeks (`full`)

```bash
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact ipython /artifact/claims/4-sec6-benchmarks/run.ipy replot    # 1 min
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact ipython /artifact/claims/4-sec6-benchmarks/run.ipy subset    # 5.5 h
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact ipython /artifact/claims/4-sec6-benchmarks/run.ipy full      # 2 weeks
```

Each mode prints the numbers of Sec. 6.1–6.3 in the order of the paper, and writes them to `paper_numbers.txt`, and Figs. 5–6 to `plots.pdf` (also as `plots-1.png` and `plots-2.png`), in `results/replot/`, `results/subset/plots/` or `results/full/plots/`.

- `replot` recomputes them from the logs of our runs; the result is identical to the paper.
- `subset` runs 20 of the 36 models (1800 s limit, 1 repetition), `full` all 36 models as in the paper (7200 s limit, 5 repetitions).
  The subset leaves out the largest models, so its factors are smaller than the paper's (e.g., Storm loads UMB 31× instead of 40× faster than JANI), but it replicates the claim: UMB is loaded and written faster than the other formats, compresses about 7× (GZip) and 22× (XZ), and reduces the total model checking time; the plots look qualitatively the same as in the paper.
  Logs and an HTML overview of all measurements are in `results/<mode>/experiments/` (`html/index.html`).
- With less than 32 GiB of RAM, more runs fail with out-of-memory (`MO`).
- With `--jobs N` (e.g. `run.ipy -- subset --jobs 4`), N benchmarks run at a time, needing N times the RAM; the measured times are then less accurate.

**BCG results need CADP.**
The BCG file sizes (Fig. 5, mcsta, right) and the comparison of UMB with BCG in Sec. 6.2 are obtained with `bcg_io` of CADP, which is proprietary and not in the image.
`replot` reproduces them from our measurements; `subset` and `full` leave them out (no BCG lines in Fig. 5, `n/a` in `paper_numbers.txt`), unless you supply your own CADP (the paper used 2025-l; free for academic users: https://cadp.inria.fr/registration/).
To do so, start a shell in the container with `/path/to/your/cadp` replaced by your CADP directory on the host (the one containing `bin.<arch>/bcg_io`):

```bash
docker run --rm -it --hostname umb-artifact -v "/path/to/your/cadp:/opt/cadp" -e CADP=/opt/cadp -v "$PWD/results:/artifact/results" umb-artifact bash
```

CADP needs a license for the container, which this command names `umb-artifact` on every run.
Obtain a license for this machine name and install it in `/opt/cadp` as CADP's instructions describe.
Without a valid license, the `bcgio` runs fail, and their logs in `results/<mode>/experiments/logs/` show:

```
*007 protection violation:
     illicit attempt at using ``bcg_io 1.8'' on machine ``umb-artifact''
     no appropriate license
```

Once the license is in place, link `bcg_io` into the harness (replace `bin.x64` by your architecture directory if it differs) and run a mode (`smoke`, `subset` or `full`):

```bash
ln -s /opt/cadp/bin.x64/bcg_io /artifact/umb-benchmarking/bin/bcgio
ipython /artifact/claims/4-sec6-benchmarks/run.ipy smoke
```

The harness then also converts the exported `.aut` files to BCG, and the BCG sizes appear in `results/<mode>/experiments/` (as `bcgio`), and for `subset` and `full` also in `plots.pdf` and `paper_numbers.txt`.

#### Sec. 6.4: explicit encodings in the PRISM language

- **Claim:** PRISM builds random models with 10k and 100k states, generated with umbi, from UMB and from an explicit encoding in the PRISM language: from UMB, both take about a second; from the PRISM language, the 10k model takes seconds, while the 100k model hits the time limit of 1 hour.
- **Estimated evaluation time:** 1 hour with the paper's time limit, or 11 minutes with a time limit of 10 minutes, which suffices to show the difference

```bash
docker run --rm -t umb-artifact ipython /artifact/claims/5-sec6.4-flat-prism/run.ipy                     # 1 h limit, as in the paper
docker run --rm -t umb-artifact ipython /artifact/claims/5-sec6.4-flat-prism/run.ipy -- --timeout 600    # 10 min limit
```

For each model, the output shows its size (`Model size`, `File sizes`) and the `Wall time` of PRISM building it from the `.umb` and from the `.prism` file: about a second for both `.umb` files and seconds for the 10k `.prism` file, while for the 100k `.prism` file PRISM hits the limit (`no result (time limit)`).

## Reusability

### Using UMB

The UMB Observatory's getting-started notebook, which the image contains, shows how to use UMB in Storm, PRISM, mcsta, umbi (including its API) and Stormvogel.
It creates a model with umbi, inspects the file, draws it with Stormvogel, checks it with the three tools, and tests the tools against each other with `umbtest`.
To run its cells, change them and try your own models, start the Jupyter server of the image:

```bash
docker run --rm -p 127.0.0.1:8000:8000 -e JUPYTER_TOKEN=umb umb-artifact
```

Then open http://localhost:8000/notebooks/getting_started.ipynb?token=umb in a browser; stop the server with Ctrl-C.

A read-only version of the notebook is online at https://pmc-tools.github.io/umb-observatory/; it follows the latest tool versions, while the one in the image matches the tool versions of the paper.
More umbi examples: [github.com/pmc-tools/umbi/tree/main/examples](https://github.com/pmc-tools/umbi/tree/main/examples).

### Benchmarking further models

To compare the formats and tools as in Sec. 6 on your own models, put each model in a directory `<name>/` with `model.prism`, `model.jani` and `property.props` (`<name>` must not contain `_`).
Start a shell with the directory mounted among the benchmarks, here for a model `mymodel`:

```bash
docker run --rm -it -v "$PWD/mymodel:/artifact/umb-benchmarking/models/mymodel:ro" -v "$PWD/results:/artifact/results" umb-artifact bash
```

In the container, replace the models of the `subset` mode by yours (for several models: `MODELS=(a b c)`) and run it:

```bash
sed -i '/^MODELS=(/,/^)/c\MODELS=(mymodel)' /artifact/umb-benchmarking/subset.sh
ipython /artifact/claims/4-sec6-benchmarks/run.ipy subset
```

The results are in `results/subset/` as above.
The harness is documented in `umb-benchmarking/scripts/README.md`.

### Building the image

Instead of loading the image, you can build it from source in the folder unpacked from `umb-artifact.zip` (about 30 minutes on a 12-core machine):

```bash
docker buildx bake
```

This builds the [UMB Observatory](https://github.com/pmc-tools/umb-observatory) (Storm, PRISM, mcsta and umbi in one image) with the tool versions of the paper (see `docker-bake.hcl`), then the artifact image on top of it (`docker/Dockerfile`).
The build downloads the tools' sources, so it needs internet access.

| Tool | Version |
| --- | --- |
| UMB Observatory | commit [`5dc44c9`](https://github.com/pmc-tools/umb-observatory/commit/5dc44c954b7714ba08184346ba0ab28d1905385c) (2026-10-16) |
| Storm | [1.14.0](https://github.com/stormchecker/storm/releases/tag/1.14.0) + 68 commits (commit [`2c6a7c2`](https://github.com/stormchecker/storm/commit/2c6a7c2e96f7d64179d8193f27cea88f2cd19362)) |
| PRISM | [4.11](https://github.com/prismmodelchecker/prism/releases/tag/v4.11) + 1 commit (commit [`f118f0b`](https://github.com/prismmodelchecker/prism/commit/f118f0b2706d0deed1f57b4110fbeb01e4142366)) |
| mcsta | [v3.1.315](https://www.modestchecker.net/downloads/); the paper used v3.1.311, which is no longer available ([changelog](https://www.modestchecker.net/downloads/changelog.html): the only change is a new, optional algorithm) |
| umbi | [0.2.15](https://pypi.org/project/umbi/0.2.15/) |
| Stormvogel | [0.13](https://pypi.org/project/stormvogel/0.13/) |
