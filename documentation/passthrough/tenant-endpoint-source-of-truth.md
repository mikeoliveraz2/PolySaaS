# Tenant Passthrough Endpoint Source of Truth

## Invariant

Each tenant's `PassThroughEndpoint` row is the only source of truth for that
tenant's passthrough route and upstream target.

`PassThroughEndpoint` is tenant-owned data. It must be read from and written to
the active tenant schema only. The PostgreSQL `public` schema does not provide
passthrough defaults, fallback rows, inherited rows, or merge candidates.

## Canonical URL

The browser-facing admin route is derived without changing the stored record:

```text
endpoint_url = https://tenant-app.example.com:8443
starting_uri = /web

browser URL  = /pt/admin/tenant-app.example.com:8443/web
proxy target = https://tenant-app.example.com:8443
```

The transformation is:

1. Parse the exact host, including its port when present, from `endpoint_url`.
2. Prepend `/pt/admin/` to that host.
3. Append `starting_uri` for the initial UI link.
4. Preserve subsequent request subpaths and query parameters when forwarding.

The stored `endpoint_url` is never rewritten during this process.

## Identity Rules

- `endpoint_url` is unique within each tenant schema and is the only
  `PassThroughEndpoint` routing identity.
- `endpoint_url` supplies both the upstream target and browser route host.
- `starting_uri` supplies only the initial application path.
- `slug` is optional descriptive/application metadata. It is not a route key.
- The database primary key is not exposed as passthrough route identity.
- Proxy resolution requires an exact `endpoint_url` host match in the active
  tenant schema.

Integer primary keys remain valid for unrelated Django admin, PolySniffer,
capture, and session records. The defunct rule applies only to
`PassThroughEndpoint` browser links and proxy resolution.

Both browser surfaces are derived from the same endpoint string:

```text
/pt/admin/<endpoint host>/<upstream path>
/pt/dose/<endpoint host>/<upstream path>
```

## Tenant Isolation

The following behavior is prohibited:

- Querying `public.dose_passthroughendpoint` as a fallback.
- Merging public and tenant endpoint querysets.
- Copying endpoint rows from `public` into a tenant schema.
- Copying endpoint rows from one tenant into another tenant.
- Inventing an upstream URL from an unmatched browser route.
- Falling back from an endpoint host to a slug or record ID.

Shared authentication and tenant-registry data may still live in `public`.
That does not give `public` any role in `PassThroughEndpoint` ownership or
resolution.

## Provisioning

Each tenant app provisioner creates and maintains its own exact endpoint row in
that tenant's schema. Generic tenant creation, subscription bootstrap, and admin
bootstrap must not seed endpoint catalogs from another schema.

Admin saves require an active tenant. A request without an active tenant must
not write a passthrough endpoint into `public`.

## Failure Behavior

If the active tenant has no enabled endpoint whose stored host exactly matches
the `/pt/admin/<host>/` segment, the request returns `404`. It must not search
`public`, search another tenant, infer a scheme, or synthesize an upstream URL.

## Regression Check

`dose/tests/test_passthrough_endpoint_url.py` verifies that:

- Host and `starting_uri` produce canonical `/pt/admin/` and `/pt/dose/` URLs.
- Changing `slug` does not change the browser URL.
- Changing the database record ID does not change the browser URL.
- Building the browser URL does not mutate `endpoint_url`.
- Unsupported passthrough surface prefixes are rejected.
- `endpoint_url` is declared unique at the database model boundary.