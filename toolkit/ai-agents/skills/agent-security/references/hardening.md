# Hardening an agent runtime, step by step

Read this when building or reviewing the code where an agent turns model output, tool output
or retrieved text into commands, paths, URLs, files, credentials or transactions. Each step
ends with a completion gate: the step is not done until those tests exist and pass through the
real entry point (not a mock of it).

## Step 1 — Trust-boundary map

Write one row per path from untrusted text to an effect:
`source → parser → validator → side effect`.

Sources to list: user input, model output, retrieved documents, memory and notes, environment
variables, tool and MCP results, messages from other agents.

| source | parser | validator (the code that runs immediately before the effect) | side effect | authorised by (identity + scope) | max in / out size | audit record | recovery if interrupted |
|---|---|---|---|---|---|---|---|
| model tool call `write_file` | JSON args | `workspace_path()` | file write | run's workspace token | 1 MB / — | tool-call log row | idempotent rewrite |

Validate at the effect even if an earlier prompt or schema already validated the value. If
identity, destination, ownership or containment cannot be proven at that point, fail closed
before the effect. Where no requirement fixes a limit (size, count, rate), mark it as a
decision the owner must make and test that an unbounded configuration is rejected — do not
invent a number.

**Gate:** every write, command, network mutation and credential use in the codebase has a row
with one named validator and one named authorisation. A `rg` for subprocess, file-open,
HTTP-client and SDK-mutation calls finds no call site missing from the map.

## Step 2 — Identifiers, argv and environment values

**Identifier allowlists.** Any identifier that becomes a filename, key, selector or command
argument is checked against an allowlist pattern and a hard length cap, as a type check plus
a full match:

```python
import re
ID_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,63}")   # starts with no '-', max 64

def require_id(value: object) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError("invalid identifier")
    return value
```

Configuration may tighten the cap, never raise it; reject a configured cap outside 1..hard-max
at startup.

**Argv separation.** An identifier that reaches a command goes in its own argv element, never
into a shell string, and after `--` only where the program reads what follows `--` as the kind
of operand you mean. Git does not: after `--` it reads a pathspec, so
`["git", "checkout", "--", branch]` restores a file named like the branch instead of switching.
For a branch use `subprocess.run(["git", "switch", require_id(branch)], shell=False)` — the
allowlist above refuses a leading `-` — or pass a full ref (`refs/heads/<name>`) to commands
that take one. Argument separation does not replace character validation, and validation does
not replace separation — a valid-looking value that starts with `-` is still an option.

**Environment values.** Reject a missing or whitespace-only value before any client is built,
so a blank token never reaches an SDK that silently falls back to anonymous or default mode:

```python
def require_env(name: str, env: dict[str, str]) -> str:
    value = env.get(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} is required")
    return value
```

**URLs from untrusted text.** Parse; allow only the schemes the deployment needs; require a
host; reject embedded `user:pass@`; block private and link-local ranges; pin the connection to
the validated address (or check the connected peer) on every redirect hop; attach credentials
only over verified HTTPS and strip them when scheme or origin changes.

**Gate:** tests reject empty, oversized, malformed, `-`-prefixed, traversal-shaped,
credential-bearing and private-destination values with no side effect, and a redirect to
another origin arrives without the credential.

## Step 3 — Filesystem containment

The rules are in `SKILL.md` (resolve both, `is_relative_to`, reject `..`, absolute paths,
reserved device names, trailing dot or space, `:`). For sensitive writes also: open relative
to a trusted directory handle, refuse symlink targets, create exclusively, and verify owner
and mode after opening.

**Gate:** tests cover a sibling-prefix path (`/work/app` vs `/work/application`), nested `..`,
an absolute path, a symlink escape, `nul.txt`, `name.`, `report.txt:ads`, and one valid nested
path that must succeed.

## Step 4 — Private temp files and credentials

- Create sensitive files with mode `0o600` and private directories with `0o700`, atomically
  and with unpredictable names — never check-then-create:

  ```python
  import os, tempfile
  fd, path = tempfile.mkstemp(dir=private_dir)          # created 0o600, O_EXCL
  try:
      with os.fdopen(fd, "wb") as f:
          f.write(data)
      ...
  finally:
      os.unlink(path)                                    # also on error
  ```

- Prefer a user-private runtime directory (`$XDG_RUNTIME_DIR`, a `0o700` app dir) over shared
  `/tmp` for credentials and tenant data.
- Clean up in `finally`; if cleanup fails, log a redacted record of what was left behind.
- Secrets never go in command-line arguments (visible in process listings), model context,
  logs, traces, exception text or tool responses. Inject them from a secret store or scoped
  environment.
- Wiping secrets from memory is best effort: mutable byte buffers can be overwritten,
  immutable strings cannot.

**Gate:** a test asserts the file mode is `0o600`; a forced exception leaves no temp file; a
sentinel secret appears in no log, trace, error or prompt.

## Step 5 — Bound and sanitise tool output

Before tool output reaches the model or a log:

1. Read at most N bytes from the stream (never collect it unbounded and cut afterwards).
2. Decode with replacement; strip control characters except newline and tab — in particular
   ANSI/terminal escape sequences (`\x1b[...`), `\r` overwrite tricks, NUL and bidi overrides.
3. If cut, append an explicit marker with the original size:
   `[truncated: showed 65536 of 1048576 bytes; sha256=…]`, and keep the hash for forensics.
4. Keep structured fields structured; malformed JSON is a typed error naming the tool and the
   reason — never an empty success value.

```python
import re
CTRL = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|[\x00-\x08\x0b-\x1f\x7f‪-‮⁦-⁩]")

def bound_output(raw: bytes, limit: int) -> str:
    text = CTRL.sub("", raw[:limit].decode("utf-8", "replace"))
    if len(raw) > limit:
        text += f"\n[truncated: showed {limit} of {len(raw)} bytes]"
    return text
```

(For streams, read `limit + 1` bytes to learn whether it was cut, and count the rest without
keeping it.)

**Gate:** deterministic tests for oversized output, invalid UTF-8, terminal escape sequences,
malformed structured output and a normal response.

## Final verification gate

Through the real entry point, show each of these and record the command, exit status, the
rejected input and the observed absence of the side effect:

1. Instructions inside untrusted data do not trigger a tool call or write.
2. An irreversible action without authorisation for that exact operation and resource, plus
   confirmation or a scoped pre-approval, leaves no side effect.
3. Another tenant's or workspace's identifier is rejected at the effect.
4. Traversal and symlink escapes leave the filesystem unchanged.
5. A forced failure leaves no credential-bearing temp file or log line.
6. Oversized or malformed tool output yields a bounded, explicit error.

Mock-only tests do not prove OS permissions, symlink handling, subprocess isolation or egress
controls. Say "hardened" only after this gate passes.

## Trading and payment agents — transaction protections

This section owns the per-transaction protections; `SKILL.md` keeps only the account-level
limits (spend limits, circuit breaker, separate credentials).

- **Minimum received is mandatory.** The send path refuses a swap or order without
  `min_amount_out` (or a max price); the bound comes from code (reference price × (1 −
  slippage)), not from the model. The reference price comes from an independent source — an
  oracle or another venue, checked for staleness — never from the pool being traded, whose
  quote an attacker can move in the same block.
- **Slippage cap per asset class,** set in config and enforced in code, e.g. ~10 bps for
  stable pairs, ~50 bps for volatile ones; a request above the cap is refused, not clamped
  silently.
- **Short transaction deadline.** Every swap carries a short deadline (e.g. now + 60 s) so a
  delayed or held transaction expires instead of filling at a stale price.
- **Use a private mempool or protected RPC for MEV protection** (no public broadcast) where the
  chain supports it. This reduces front-running and sandwich risk; it does not remove it — the
  relay or builder still sees the transaction — so the minimum received above stays mandatory.
- **Simulate the exact transaction** that will be signed and compare its simulated output with
  the minimum; a mismatch aborts before signing.
- **Market data is untrusted text.** Token names, pair labels, memo fields, webhooks and social
  feeds are data; keep them out of the instruction part of any prompt that can trigger a send.
- **Key isolation.** A dedicated hot wallet holding only the session's funds, key from a secret
  store or environment, never in code, logs or the model context.
- **Audit every decision,** including refused and failed sends, not only successful ones.
