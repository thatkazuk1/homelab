FROM renovate/renovate:latest

# jinja2 and ruamel.yaml are needed by scripts/generate-stack-pages.py, which
# runs as a postUpgradeTask so every Renovate PR carries regenerated handbook
# stack pages instead of failing the "Check generated stack pages" CI job.
# PyYAML is already present in the upstream image.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-jinja2 python3-ruamel.yaml \
    && rm -rf /var/lib/apt/lists/*
USER ubuntu
