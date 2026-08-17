const MAINTENANCE_HTML = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Under Maintenance</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0e0e10;
    color: #eee;
    text-align: center;
    margin: 0;
    padding: 20vh 1rem 0;
  }
  h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
  p { color: #999; }
</style>
</head>
<body>
  <h1>Under Maintenance</h1>
  <p>This service is temporarily unavailable. Please check back shortly.</p>
</body>
</html>`;

// Proxy/connectivity-layer signals only (Traefik or Cloudflare couldn't reach
// the app at all) — NOT a plain 500, which means the app itself handled the
// request and its own code threw. A 500 is a real, debuggable app error and
// must pass through unmodified rather than being masked as "maintenance".
const UNREACHABLE_STATUSES = new Set([502, 503, 504]);

export default {
  async fetch(request) {
    try {
      const response = await fetch(request);
      if (UNREACHABLE_STATUSES.has(response.status)) {
        throw new Error(`origin returned ${response.status}`);
      }
      return response;
    } catch (err) {
      return new Response(MAINTENANCE_HTML, {
        status: 503,
        headers: {
          "content-type": "text/html;charset=UTF-8",
          "retry-after": "120",
        },
      });
    }
  },
};
