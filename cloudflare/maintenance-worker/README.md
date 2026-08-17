# Maintenance-page fallback Worker

A Cloudflare Worker that intercepts requests before they reach the origin
(via a Worker Route) and returns a static "Under Maintenance" page if the
origin fetch throws or returns a 5xx. Runs at Cloudflare's edge, independent
of the fleet's Cloudflare Tunnel — so it covers both failure modes a
Traefik-level fallback can't:

- the origin container is down but `docker-prod-01` (and the shared
  `cloudflared-tunnel`, per `stacks/cloudflared/`) is still up
- `docker-prod-01` itself is down, taking every `*.kazuki.uk` route with it,
  since all hostnames currently share one named tunnel

## Scope

Fleet-wide as of 2026-08-13 (`*.kazuki.uk/*` in `wrangler.toml`'s `routes`),
widened from a `stackdoc.kazuki.uk`-only pilot after live validation.

**Before deploying this scope**, confirm in the Cloudflare dashboard that
`ts.kazuki.uk` and its children (`komodo.ts.kazuki.uk`, `forgejo.ts.kazuki.uk`,
`coolify.ts.kazuki.uk`, `dockhand.ts.kazuki.uk`) are DNS-only (grey-cloud),
not proxied. Worker Routes only fire on traffic that passes through
Cloudflare's proxy, but the `*.kazuki.uk/*` pattern itself can match any
subdomain depth — if any `ts.kazuki.uk` record is ever switched to proxied,
this Worker would start wrapping tailnet-scoped admin UIs in the maintenance
fallback too, which is not the intent (those aren't the "public-facing"
services this was built for).

## Deploying

Requires a Cloudflare API token with `Workers Scripts:Edit` and
`Workers Routes:Edit` permissions on the `kazuki.uk` zone — an operator
credential (per CLAUDE.md's operator/executor split), not something to run
with a token pasted into a chat session.

```bash
cd cloudflare/maintenance-worker
wrangler login          # or: export CLOUDFLARE_API_TOKEN=...
wrangler deploy
```

This creates the Worker and attaches the Route in one step (`routes` is
declared in `wrangler.toml`, not set up separately in the dashboard).

## Testing

Simulate origin-down without touching the real container:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://stackdoc.kazuki.uk/
```

To confirm the fallback actually fires (not just a healthy passthrough),
stop the real origin path temporarily (e.g. `docker stop` the relevant
container on `coolify-prod-01`, or block the tunnel) and re-curl — expect a
`503` with the maintenance HTML body, not Cloudflare's own default error
page. Restore the origin afterward and re-verify a normal `200`.

**Also verify the negative case**: trigger a request that causes Stackdoc's
own backend to throw (an app-level bug, not an outage) and confirm you get
Stackdoc's real `500` response back, not the maintenance page. The Worker
only treats `502`/`503`/`504` (proxy/connectivity-layer signals) and
network-level fetch failures as "unreachable" — a plain `500` means the app
itself handled the request and should be shown as-is, per `worker.js`'s
`UNREACHABLE_STATUSES` comment.

## Post-widen verification

After redeploying with the fleet-wide route, spot-check beyond just
`stackdoc.kazuki.uk`:

- A couple of other public hostnames (e.g. `status.kazuki.uk`) still return
  their normal `200`, unaffected by the Worker.
- The ACME HTTP-01 challenge path continues to pass through untouched —
  Coolify tenants rely on a path-scoped Cloudflare Tunnel ingress rule for
  `/.well-known/acme-challenge/*` (see `handbook/docs/architecture/coolify.md`);
  the Worker doesn't change tunnel routing, but confirm a cert renewal still
  works cleanly rather than assuming it from first principles.
- `ts.kazuki.uk` admin UIs are unaffected (see the Scope section above).
