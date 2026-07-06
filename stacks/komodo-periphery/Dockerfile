ARG PERIPHERY_VERSION=2

FROM ghcr.io/moghtech/komodo-periphery:${PERIPHERY_VERSION}

USER root

# Versions pinned for reproducibility — bump explicitly
ARG SOPS_VERSION=3.13.1
ARG AGE_VERSION=1.3.1

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && curl -fsSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64" -o /usr/local/bin/sops \
  && chmod +x /usr/local/bin/sops \
  && curl -fsSL "https://github.com/FiloSottile/age/releases/download/v${AGE_VERSION}/age-v${AGE_VERSION}-linux-amd64.tar.gz" -o /tmp/age.tgz \
  && tar -xzf /tmp/age.tgz -C /tmp \
  && install /tmp/age/age /tmp/age/age-keygen /usr/local/bin/ \
  && rm -rf /tmp/age* \
  && apt-get clean && rm -rf /var/lib/apt/lists/* \
  && sops --version \
  && age --version

USER root
