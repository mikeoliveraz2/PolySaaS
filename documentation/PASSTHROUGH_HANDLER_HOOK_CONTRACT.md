# Passthrough Handler Hook Contract

This contract defines the boundary between the shared passthrough framework and endpoint-specific behavior.

## Rule

Shared middleware, URL routing, and forwarding must remain endpoint-agnostic.
If behavior depends on which app is being proxied, it belongs in the handler.

This is required for scale:
- bundled endpoints
- tenant-specific endpoints
- PolySniffer-generated handlers

Bundled application handlers are shared framework assets and may be reused across tenants.
Tenant isolation constraints apply to the endpoints and tenant-specific endpoint configuration,
not to the bundled handler classes themselves.

## Shared Layer Responsibilities

- Resolve the `PassThroughEndpoint`
- Load the handler
- Forward the request generically
- Invoke handler hooks
- Apply only endpoint-agnostic response plumbing

## Handler Hook Surface

Handlers may implement any of these hooks.

### Request normalization

- `try_rewrite_incoming_path(request, endpoint) -> bool`
  Rewrite native app paths into `/pt/admin/<trigger>/...`.

- `augment_outbound_headers(request, headers, target_url) -> None`
  Add or normalize upstream-facing headers.

- `filter_cookies_for_upstream(request, cookies) -> dict`
  Drop unrelated browser cookies before proxying upstream.

- `get_upstream_cookies(request) -> dict`
  Supply bootstrap or SSO cookies without overwriting browser-fresh cookies.

- `native_passthrough_prefixes() -> tuple[str, ...]`
  Declare native non-`/pt/` path prefixes owned by the handler, such as `/web`.

- `should_exempt_csrf_for_path(path_info) -> bool`
  Declare whether a non-`/pt/` path should bypass Django CSRF before handler rewrite.

- `upstream_url_for_subpath(endpoint_url, clean_path) -> str | None`
  Override how proxy subpaths map to upstream URLs.

### Display-shell preparation

- `try_root_display_shell_response(request, endpoint, url_trigger_segment) -> HttpResponse | None`
  Return a fully prepared shell response when the handler wants to own first-page rendering.

### Upstream transport policy

- `should_follow_upstream_redirects(request, target_url, upstream_path) -> bool`
  Decide whether the requests client should follow redirects internally.

- `postprocess_upstream_response(resp, request, **context) -> requests.Response`
  Normalize upstream responses before the shared forwarder handles redirect rewriting, body shaping, and final response assembly.

### Response shaping

- `rewrite_upstream_body(body, content_type, request, **context) -> bytes | None`
  Rewrite non-HTML upstream payloads such as JS, CSS, JSON, or binary-adjacent text.

- `process_html_response(html_str, request, endpoint_url=None, **context) -> str | tuple | HttpResponse`
  Rewrite HTML responses or return a fully-formed response.

- `should_forward_set_cookie_headers(request, upstream_content_type, upstream_path, response_kind) -> bool`
  Control endpoint-specific cookie forwarding policy.

## Migration Guidance

When shared code contains logic like:
- `if "odoo" in target_url`
- `if trigger == "nextcloud"`
- endpoint-specific URL patterns in generic middleware

that logic should be moved to one of the hooks above.

## PolySniffer Alignment

PolySniffer-generated handlers should target this hook surface.
That keeps generated endpoint behavior isolated from the shared passthrough core and avoids unmaintainable growth in middleware or URLconf.

For avoidance of doubt:
- Bundled handlers are shared and reusable.
- Tenant-specific endpoints may point at bundled handlers.
- Tenant-isolated behavior should live in endpoint data/config or tenant-scoped generated handlers, not in shared middleware.