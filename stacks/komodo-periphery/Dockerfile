ARG PERIPHERY_VERSION=2

FROM ghcr.io/moghtech/komodo-periphery:${PERIPHERY_VERSION}

USER root

# Versions pinned for reproducibility — bump explicitly
ARG SOPS_VERSION=3.13.2
ARG AGE_VERSION=1.3.1

# Arch is derived from `uname -m` at build time (inside the target-platform layer),
# not from buildx's TARGETARCH build-arg — this Dockerfile previously hardcoded
# linux.amd64 unconditionally, which is why the arm64 image shipped an x86-64 sops
# binary. sops/age --version at the end fails the build loudly on a wrong-arch binary
# instead of surfacing as a deploy-time exec format error.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates file \
  && case "$(uname -m)" in \
       x86_64) ARCH=amd64 ;; \
       aarch64) ARCH=arm64 ;; \
       *) echo "Unsupported arch: $(uname -m)"; exit 1 ;; \
     esac \
  && echo "Building for architecture: ${ARCH}" \
  && curl -fsSL "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.${ARCH}" -o /usr/local/bin/sops \
  && chmod +x /usr/local/bin/sops \
  && curl -fsSL "https://github.com/FiloSottile/age/releases/download/v${AGE_VERSION}/age-v${AGE_VERSION}-linux-${ARCH}.tar.gz" -o /tmp/age.tgz \
  && tar -xzf /tmp/age.tgz -C /tmp \
  && install /tmp/age/age /tmp/age/age-keygen /usr/local/bin/ \
  && rm -rf /tmp/age* \
  && apt-get clean && rm -rf /var/lib/apt/lists/* \
  && sops --version \
  && age --version \
  && file /usr/local/bin/sops \
  && file /usr/local/bin/age

USER root
