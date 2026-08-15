# Network failures

Use this guide when execution evidence indicates that an import could not
connect to a source or complete a request.

## Gather context

- Inspect relevant execution evidence, such as logs or monitoring signals, for
  request failures.
- Identify the affected request, URL or host, client library, and failure
  stage.
- Inspect the requesting code for timeout, streaming, retry, and exception
  handling behavior.
- Determine whether the failure stopped execution or was caught and skipped.

## Timeout

### Confirm or reject

- Confirm a timeout only from request-related evidence or a client exception.
- Determine the client's timeout semantics before classifying the failure.
- For Python `requests`, distinguish connection timeout from read timeout. A
  read timeout measures inactivity between received bytes, not the duration of
  the complete download.
- Distinguish these timeout stages:

  | Stage | Evidence |
  |---|---|
  | Connection | The client did not establish the connection before its connection timeout. |
  | First byte | The connection succeeded, but no response bytes arrived before the read timeout. |
  | Interrupted transfer | Some response data arrived, followed by enough inactivity to trigger the read timeout. |
  | Total operation | An outer deadline expired while the request or transfer was still running. |
  | Browser automation | A browser request failed; do not treat navigation, page-load, or element-wait timeouts alone as network evidence. |

### Check efficiently

- Start with source reachability and a lightweight request to the exact
  resource.
- Try `HEAD` when the source supports it. Otherwise use a Range request or a
  bounded streaming request and stop after enough data arrives to establish
  progress.
- Preserve request parameters, redirects, and ordinary headers required by the
  import. A successful request to a different resource does not establish that
  the import's resource is available.
- Record the response status, redirects, time to first byte, and whether data
  continues arriving.
- Treat a successful current check as supporting evidence only. It does not
  refute a transient or execution-environment-specific failure.

### Mitigation when confirmed

- Do not recommend increasing a timeout solely because a timeout occurred.
- Recommend increasing the applicable timeout only when evidence shows useful
  progress and that the current limit is the constraint.
- If no response data arrives, investigate the source and request before
  increasing the timeout. Use bounded retries with backoff only when the
  failure appears transient.
- If a transfer begins and then stalls, consider a larger read timeout only
  when a longer check shows that progress resumes. Consider bounded retry or
  resumable download behavior for interrupted transfers.
- If an outer deadline expires during steady progress, adjust that deadline
  using the expected size and observed transfer behavior.
- If the import catches the timeout and skips a required input, recommend
  failing the operation or enforcing an explicit completeness check. Do not
  treat a partial result as a successful download.

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
