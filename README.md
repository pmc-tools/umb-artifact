# Artifact supplement for: UMB — A Unified Markov Binary Format for Probabilistic Model Checking

<!-- TODO: remove all TODOs before submission -->

Artifact supplement for the TACAS 2027 regular tool submission paper: *UMB: A Unified Markov Binary Format for Probabilistic Model Checking*.

- **Submission number**: 0983
- **Badges claimed:** Available, Functional, Reusable.
- **Tested on:** amd64: Ubuntu 24.04, Docker 29.8; arm64: TODO.

## Availability

The artifact is permanently archived at [Zenodo](TODO link) (DOI: TODO) and hosted on [GitHub](TODO link).
It contains:

| File | Content |
| --- | --- |
| `umb-artifact-{amd64,arm64}.tar.gz` | the Docker image, one per architecture |
| `paper.pdf` | the submitted paper |
| `umb-artifact.zip` | the artifact's repository, from which the image can be built (see below) |
| `README.md` | this file |
| `LICENSE` | license file; the tools in the image keep their own licenses |

The image contains everything needed to replicate the empirical claims.
It is based on the [UMB Observatory](https://github.com/pmc-tools/umb-observatory) and contains Storm 1.14.0+, PRISM 4.11+, mcsta v3.1.315 and umbi 0.2.15 (exact versions in [Building the image](#building-the-image)), plus the scripts and benchmarks needed to replicate the paper's results.

The repository `umb-artifact.zip` is only needed to build the image or to inspect the sources.
It contains:

| Path | Content |
| --- | --- |
| `docker-bake.hcl`, `docker/` | how the image is built (tool versions in `docker-bake.hcl`) |
| `claims/<claim>/run.py` | one script per claim of the paper (also in the image, at `/artifact/claims/`) |
| `umb-benchmarking/` | the benchmarks of Sec. 6: models, scripts, and the logs of our runs ([github.com/tquatmann/umb-benchmarking](https://github.com/tquatmann/umb-benchmarking)) |

## Functionality

### Requirements

Docker on amd64 or arm64.
No network access is needed after loading the image.
Podman works as well: replace `docker` by `podman` in all commands.

The resources needed for the smoke test and for each mode of the benchmarks of Sec. 6 (see below):

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
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact python /artifact/claims/3-sec6-benchmarks/run.py smoke
```

This runs the benchmarks of Sec. 6 on one model (`consensus.4-4`) with all tools and formats.
It prints the generated command lines, then one line per run, first the 16 exports, then the 23 imports, each ending in `... done (<time>)`.
Its last line is `Done: results/smoke/`; `results/smoke/experiments/csv/` then contains no `TO`, `MO` or `ERR` entries.
The claim of [Fig. 4](#sec-4-fig-4-textual-view-of-a-umb-file) also takes only a moment to check.

### Replicating empirical claims

#### Sec. 4, Fig. 4: textual view of a UMB file

```bash
docker run --rm -t umb-artifact python /artifact/claims/1-fig4-textual-umb/run.py
```

umbi writes the example MDP to `mdp.umb`, and PRISM prints the contents of the file (`prism -ex -importmodel mdp.umb -exportmodel mdp.umbt:format=umb,text`).
The output is Fig. 4, except for the creation date and the state valuations, which PRISM prints decoded (`[(0,false),(1,false),(2,false),(2,true)]`) rather than bit-packed.

#### Sec. 5: bitcoin-attack

Storm builds, minimises and exports the bitcoin-attack MA to UMB in under 3 s (11475 states, 7551 after minimisation); mcsta checks the time-bounded reachability property on it in 13 s; Storm with Unif+ gives no result within 2 minutes.
TODO

#### Sec. 6.1–6.3, Figs. 5–6: import and export times, file sizes, total times

```bash
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact python /artifact/claims/3-sec6-benchmarks/run.py replot    # 1 min
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact python /artifact/claims/3-sec6-benchmarks/run.py subset    # 5.5 h
docker run --rm -t -v "$PWD/results:/artifact/results" umb-artifact python /artifact/claims/3-sec6-benchmarks/run.py full      # 2 weeks
```

Each mode writes `plots.pdf` (Figs. 5–6) and `paper_numbers.txt` (the numbers of Sec. 6.1–6.3, in the order of the paper) to `results/replot/`, `results/subset/plots/` or `results/full/plots/`.

- `replot` recomputes them from the logs of our runs (`umb-benchmarking/experiments-paper/logs-paper.tar.gz`); the result is identical to the paper.
- `subset` runs 20 of the 36 models (1800 s limit, 1 repetition), `full` all 36 models as in the paper (7200 s limit, 5 repetitions, one run after the other).
  Logs and an HTML overview of all measurements: `results/<mode>/experiments/` (`html/index.html`).
  For the subset, the numbers differ from the paper, but the factors between formats and tools should be similar.
- `--jobs N` (e.g. `run.py subset --jobs 4`) runs N benchmark runs at a time; the measured times are then less accurate.
- Absolute times depend on the machine (paper: Intel Xeon 8468, 4 cores, 32 GiB).
  With less than 32 GiB of RAM, more runs fail with out-of-memory (`MO`).
- The BCG file sizes (Fig. 5, mcsta, right) need CADP's `bcg_io`, which is proprietary.
  `replot` uses our measured BCG sizes; `subset` and `full` leave the BCG lines out, unless you supply CADP as below.

**With your own CADP** (the paper used CADP 2025-l).
Start a shell in the container with your CADP installation mounted:

```bash
docker run --rm -it -v "$CADP:/opt/cadp:ro" -e CADP=/opt/cadp -v "$PWD/results:/artifact/results" umb-artifact bash
```

In the container, link `bcg_io` into the harness, enable its BCG step, and run a mode (`smoke`, `subset` or `full`):

```bash
ln -s /opt/cadp/bin.x64/bcg_io /artifact/umb-benchmarking/bin/bcgio    # bin.x64 on amd64
sed -i 's|^# python3 ../scripts/aut_to_bcg.py|python3 ../scripts/aut_to_bcg.py|' /artifact/umb-benchmarking/*.sh
python /artifact/claims/3-sec6-benchmarks/run.py smoke
```

The BCG sizes then appear in `results/<mode>/` as for `replot`.

#### Sec. 6.4: explicit encodings in the PRISM language

```bash
docker run --rm -t umb-artifact python /artifact/claims/4-sec6.4-flat-prism/run.py    # 1 h
```

This uses a time limit of 1 h per PRISM call, as in the paper.
`--timeout` sets a different limit in seconds; with a limit of 60 s, the script takes about 2 min:

```bash
docker run --rm -t umb-artifact python /artifact/claims/4-sec6.4-flat-prism/run.py --timeout 60
```

umbi generates random models with 10k and 100k states and writes each both as UMB and as a flat PRISM-language file (one command per choice).
PRISM builds the model from both (`prism -ex -importmodel game-<n>.umb`, `prism -ex game-<n>.prism`) and the script prints the time of each.
From the UMB file, both models take about a second; from the PRISM file, the 10k model takes seconds, while the 100k model hits the time limit.

#### Sec. 2, Ex. 1: building a model with umbi

umbi builds the example MDP from Python and writes it to a UMB file: section "Creating a model with umbi" of the UMB Observatory's getting-started notebook (see [Using UMB](#using-umb) for how to run it).

## Reusability

This section documents how the tools use UMB, how to benchmark further models, and how to build the image.

### Using UMB

The usage of UMB in Storm, PRISM, mcsta and umbi, including the API of umbi, is documented in the UMB Observatory's getting-started notebook, online at https://pmc-tools.github.io/umb-observatory/.
It creates a model with umbi, inspects the file (`index.json` and the binary files), checks the model with the three tools, and tests the tools against each other with `umbtest`.
More umbi examples: [github.com/pmc-tools/umbi/tree/main/examples](https://github.com/pmc-tools/umbi/tree/main/examples).

The image contains the notebook for the tool versions of the paper (the online one follows the latest versions).
To run it offline, start the image:

```bash
docker run --rm -p 127.0.0.1:8000:8000 -e JUPYTER_TOKEN=umb umb-artifact
```

and open http://localhost:8000/notebooks/getting_started.ipynb?token=umb.

### Benchmarking further models

To compare the formats and tools as in Sec. 6 on your own models, put each model in a directory `<name>/` with `model.prism`, `model.jani` and `property.props` (`<name>` must not contain `_`).
Start a shell with the directory mounted among the benchmarks, here for a model `mymodel`:

```bash
docker run --rm -it -v "$PWD/mymodel:/artifact/umb-benchmarking/models/mymodel:ro" -v "$PWD/results:/artifact/results" umb-artifact bash
```

In the container, replace the models of the `subset` mode by yours (for several models: `MODELS=(a b c)`) and run it:

```bash
sed -i '/^MODELS=(/,/^)/c\MODELS=(mymodel)' /artifact/umb-benchmarking/subset.sh
python /artifact/claims/3-sec6-benchmarks/run.py subset
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
