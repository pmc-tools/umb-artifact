# Artifact image for "UMB: A Unified Markov Binary Format for Probabilistic Model Checking" (TACAS 2027).
#
# Built on the UMB Observatory image (Storm, PRISM, Modest, umbi, Jupyter), built from its sources with the
# tool versions of the paper (see docker-bake.hcl). Adds the benchmarking harness (umb-benchmarking/), the scripts
# for the claims, and LaTeX for recreating the plots.
#
#   docker buildx bake

ARG OBSERVATORY_IMAGE=umb-observatory:tacas27
FROM $OBSERVATORY_IMAGE

# LaTeX for the plots of the paper (pgfplots, pgfplotstable, caption, etoolbox, geometry)
RUN apt-get update -qq \
 && apt-get install -yqq --no-install-recommends \
    texlive-latex-base texlive-latex-recommended texlive-pictures texlive-fonts-recommended cm-super \
 && rm -rf /var/lib/apt/lists/*

# So that the tools can be called as storm, prism and modest
ENV PATH="/opt/prism/prism/bin:/opt/Modest:$PATH"

WORKDIR /artifact
COPY umb-benchmarking umb-benchmarking
COPY claims claims

# The harness expects the tools as links in umb-benchmarking/bin (see umb-benchmarking/scripts/README.md).
# CADP's bcg_io cannot be shipped, so there is no bin/bcgio.
RUN mkdir -p umb-benchmarking/bin \
 && ln -s /opt/Modest/modest         umb-benchmarking/bin/modest \
 && ln -s /opt/prism/prism/bin/prism umb-benchmarking/bin/prism \
 && ln -s "$(command -v storm)"      umb-benchmarking/bin/storm

# The default command is the observatory's: a Jupyter server on port 8000 with getting_started.ipynb.
WORKDIR /opt/umb
