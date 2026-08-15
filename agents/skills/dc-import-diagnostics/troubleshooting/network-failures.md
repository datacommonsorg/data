# Network failures

Use this guide when execution evidence indicates that an import could not
connect to a source or complete a request.

## Choose a hypothesis

| Evidence | Investigate |
|---|---|
| Request or client timeout | [Timeout](#timeout) |
| TLS handshake or certificate failure | [TLS or SSL failure](#tls-or-ssl-failure) |
| Another network failure | [No matching hypothesis](#when-no-hypothesis-matches) |

## Gather context

- Inspect relevant execution evidence, such as logs or monitoring signals, for
  request failures.
- Identify the affected request, URL or host, client library, and failure
  stage.
- Inspect the requesting code for timeout, streaming, retry, and exception
  handling behavior.
- Determine whether the failure stopped execution or was caught and skipped.

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

## TLS or SSL failure

### Confirm or reject

- Confirm the failure from TLS handshake or certificate-validation evidence.
- Treat certificate expiry, hostname mismatch, an incomplete or untrusted
  certificate chain, protocol incompatibility, and handshake failure as
  distinct possible causes.
- Treat a generic timeout as insufficient unless evidence places it in the TLS
  handshake stage.

### Investigate and mitigate

- Check the certificate hostname, validity period, chain, and runtime trust
  store as applicable.
- Check whether redirects, proxies, or browser-like client behavior change the
  hostname or TLS path.
- Correct the source certificate, request URL, trust configuration, protocol,
  or proxy behavior supported by the evidence.
- Do not recommend disabling certificate verification as a general fix.

## When no hypothesis matches

- Report the network failure as unclassified.
- Return to the parent troubleshooting fallback.
- State which evidence is unavailable and do not force a timeout or TLS
  diagnosis.
