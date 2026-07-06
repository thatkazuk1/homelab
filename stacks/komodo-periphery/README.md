# Custom Komodo Periphery image

Adds `sops` + `age` to the official `ghcr.io/moghtech/komodo-periphery` image so
Komodo Stacks can use `compose_cmd_wrapper = "sops exec-env ..."` for at-deploy-time
secret decryption.

## Build

```bash
docker build \
  --build-arg PERIPHERY_VERSION=2 \
  --build-arg SOPS_VERSION=3.13.1 \
  --build-arg AGE_VERSION=1.3.1 \
  -t komodo-periphery-sops:2 \
  .
```

## Upstream version tracking

Bump `PERIPHERY_VERSION` when the official Periphery releases. Rebuild and redeploy.

## Sprint 3 follow-up

Push to Forgejo's container registry once that registry is configured, so other
hosts can pull rather than each building locally.
