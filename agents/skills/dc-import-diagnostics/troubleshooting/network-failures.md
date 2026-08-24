# Network failures

Use this guide when execution evidence indicates that an import could not
connect to a source or complete a request.

## Common hypotheses

| Evidence | Investigate |
|---|---|
| Connection-level error | [Connection failure](#connection-failure) |
| Request or client timeout | [Timeout](#timeout) |
| Certificate-verification error | [TLS certificate verification failure](#tls-certificate-verification-failure) |

## Gather context

- Inspect relevant execution evidence, such as logs or monitoring signals, for
  request failures.
- Identify the affected request, URL or host, client library, and failure
  stage.
- Inspect the requesting code for timeout, streaming, retry, and exception
  handling behavior.
- Determine whether the failure stopped execution or was caught and skipped.
- When failures recur and exact historical jobs are known, compare their
  retained logs for recurring time windows, throttling, source availability,
  or cloud/IP blocking.
- Treat a recurring pattern as a clue unless direct evidence confirms its
  cause.

## Connection failure

Confirm the failure from a connection-level error, such as name-resolution
failure, connection refused, network unreachable, or connection reset.

### Investigate and mitigate

- Retry the connection a few times to determine whether the failure is
  transient. If it is, recommend bounded retries with backoff in the import
  code.
- If the connection fails consistently, check whether the configured source
  host or endpoint has moved or is no longer available.

#### Browser-only access

- Confirm that a browser succeeds while the normal client fails from the same
  machine and network.
- Try the exact request with a browser-impersonating client, such as Python
  `curl_cffi`.
- If browser impersonation still fails but the browser works, try browser
  automation as a possible workaround.

#### Cloud or runtime blocking

- Confirm that the same client and request work from a local machine but fail
  from the cloud or GCP runtime.
- If confirmed, investigate source-side cloud blocking or runtime network
  restrictions.
- Suggest local-network execution as a workaround and check whether the source
  offers another endpoint or can allow the cloud environment.

Investigate other connection causes supported by the available evidence.

## Timeout

### Confirm

- Confirm the timeout from request-related evidence or a client exception.
- Interpret it using the actual client library's timeout semantics. For Python
  `requests`, a read timeout measures inactivity between received bytes, not
  the duration of the complete download.
- Do not treat browser navigation, page-load, or element-wait timeouts as
  network timeouts without request-level evidence.

### Mitigate

- When practical, test the exact request using the current and a reasonable
  higher value for the applicable timeout.
- Recommend increasing the timeout only when the higher value completes the
  request or makes progress that the current value does not.
- If comparison is not practical, propose a bounded increase as an unverified
  experiment and use the next execution to confirm whether it helps.
- If the larger timeout makes no additional progress, investigate another
  cause.

## TLS certificate verification failure

### Confirm

- Confirm the failure from a certificate-verification error.
- If needed, repeat the exact request with certificate verification disabled
  as a diagnostic comparison.
- If that request succeeds, treat certificate verification as the blocker. It
  does not establish whether the server or client is responsible.

### Determine the cause and mitigate

| Evidence | Likely cause | Mitigation |
|---|---|---|
| The certificate is expired, does not match the hostname, or the server omits part of the required chain | Server or source configuration | Use the correct endpoint or have the source correct its certificate or served chain. |
| The served certificate is valid, or the URL works in a browser, but the import client cannot verify it | Client trust configuration is plausible | For Python `requests`, test an updated `certifi` or the appropriate CA bundle with verification enabled in the import runtime. |

- Confirm a client-side cause only when the exact request succeeds with
  verification enabled after changing the trust configuration.
- If no secure correction is confirmed, report the cause as unknown.
- If disabling verification was the only successful test, include it as a
  possible insecure workaround. Do not recommend it for ongoing use.

## Other network failures

Investigate other network causes supported by the available evidence. If no
cause can be established, report the failure as unclassified and return to the
parent troubleshooting fallback.
