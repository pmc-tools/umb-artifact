# Artifact image for "UMB: A Unified Markov Binary Format for Probabilistic Model Checking" (TACAS 2027).
#
# Built on the UMB Observatory image (Storm, PRISM, Modest, umbi, Jupyter), built from its sources with the
# tool versions of the paper (see docker-bake.hcl). Adds the benchmarking harness (umb-benchmarking/), the scripts
# for the claims, and LaTeX for recreating the plots.
#
#   docker buildx bake

ARG OBSERVATORY_IMAGE=umb-observatory:tacas27
FROM $OBSERVATORY_IMAGE

# LaTeX for the plots of the paper (pgfplots, pgfplotstable, caption, etoolbox, geometry), pdftoppm to show them in
# the notebook
RUN apt-get update -qq \
 && apt-get install -yqq --no-install-recommends \
    poppler-utils texlive-latex-base texlive-latex-recommended texlive-pictures texlive-fonts-recommended cm-super \
 && rm -rf /var/lib/apt/lists/*

# So that the tools can be called as storm, prism and modest
ENV PATH="/opt/prism/prism/bin:/opt/Modest:$PATH"

# The observatory installs the latest stormvogel; pin the version of the README (and keep umbi's pin)
RUN python3 -m pip install --no-cache-dir stormvogel==0.13 umbi==0.2.15

# Modest's license, amended by its author to permit redistribution as part of this artifact
COPY docker/Modest-License.txt /opt/Modest/License.txt

WORKDIR /artifact
COPY umb-benchmarking umb-benchmarking
COPY claims claims

# All claims as one notebook, next to the observatory's getting_started.ipynb: the IPython scripts claims/*/run.ipy
# are in jupytext's percent format, i.e. notebook cells that also run with ipython
RUN cat claims/[1-5]-*/run.ipy > /opt/umb/claims.py \
 && jupytext --to ipynb --set-kernel python3 /opt/umb/claims.py \
 && rm /opt/umb/claims.py

# The harness expects the tools as links in umb-benchmarking/bin (see umb-benchmarking/scripts/README.md).
# CADP's bcg_io cannot be shipped, so there is no bin/bcgio.
RUN mkdir -p umb-benchmarking/bin \
 && ln -s /opt/Modest/modest         umb-benchmarking/bin/modest \
 && ln -s /opt/prism/prism/bin/prism umb-benchmarking/bin/prism \
 && ln -s "$(command -v storm)"      umb-benchmarking/bin/storm

# ipython run.ipy: no escape sequences for the window title, and Python's output in order with the tools' output
# also without a terminal
ENV PYTHONUNBUFFERED=1
RUN mkdir -p /root/.ipython/profile_default \
 && echo "c.TerminalInteractiveShell.term_title = False" > /root/.ipython/profile_default/ipython_config.py

# The default command is the observatory's: a Jupyter server on port 8000 with getting_started.ipynb.
WORKDIR /opt/umb
