# Python versus Rust

Both versions fetch the same evidence, ask the same question, and format the same valid answer.
Choose Python for the shortest setup.
Choose Rust if you want a compiled executable.
The recorded examples produce identical JSON, but the implementations are not interchangeable for every input or failure.

## Dependencies, build, and installation

| | Python | Rust |
| --- | --- | --- |
| Entry point | `python/modhopper.py` | `rust/src/main.rs` |
| Dependencies | Python 3 standard library only | `ureq` 2 with its `json` feature; `serde_json` 1 |
| Preparation | Keep the checkout and a Python interpreter. No package installation. | Build with Cargo. `rust/Cargo.lock` records exact dependency versions; use `--locked`. |
| Run | `python3 python/modhopper.py modrinth:sodium` | `./rust/target/release/modhopper modrinth:sodium` |
| Category file | Resolved relative to the Python source file at runtime | Read at runtime from an absolute path set when Cargo builds the executable |

Neither version has a packaged installer in this repository.
The Rust executable is not self-contained: keep `categories.json` at its original build location, or rebuild after moving the checkout.
Python can move with the checkout.
The [getting started commands](getting-started.md#build-and-run-rust) build Rust without installing it globally.

## One timing sample

Measured on 2026-09-28 on an Apple M4 Max with 48 GiB of memory and macOS 26.6.2.
The tools were Python 3.14.7, Rust 1.98.1, and Cargo 1.98.1.
Rust used `cargo build --release --locked --manifest-path rust/Cargo.toml`.

| Wall-clock elapsed time | Python | Rust |
| --- | ---: | ---: |
| Startup through `--help` exit | 56.61 ms | 289.01 ms |
| All four references, empty cache | 65.29 ms | 6.03 ms |
| Same references, populated cache | 62.29 ms | 3.99 ms |

Each cell is one measurement with no warm-up or averaging.
Startup was the first invocation of each command in this measurement session, including operating-system launch overhead.
It is not an estimate of steady-state startup cost.
Compilation time is excluded.

For the two classification rows, a local `check.Fake` server served the recorded responses.
Both commands read `fixtures/refs.txt` and used separate temporary cache files.
Python's `time.perf_counter()` measured each `subprocess.run()` through exit, with output captured.
Every classification output matched `fixtures/expected.json` byte for byte.
No real storefront or Jev request was timed.
These numbers describe local processing, not live service latency or a general speed guarantee.

## Behavioral differences

These differences exist in the current code; the documentation does not change them.

| Input or condition | Python | Rust |
| --- | --- | --- |
| `--file fixtures/refs.txt modrinth:sodium` | Processes positional Sodium first, then the file. | Processes the file first, then positional Sodium. |
| Repeated `--file` options | Reads only the last file. | Appends every file where its option appears. |
| Empty `CURSEFORGE_API_KEY` on an uncached reference | Rejects it as missing before HTTP. | Sends the empty header; the service decides whether to reject it. |
| Empty `TYPESAFE_API_KEY` | Omits the authorization header. | Attempts to send the header with an empty bearer value. |
| Non-ASCII decimal digits in a CurseForge ID | Accepts them as decimal digits, but a resulting URL can fail in Python's HTTP code. | Rejects them as a bad reference; only ASCII digits pass. |
| Valid JSON cache that is not an object, such as `[]` | Loads the value; processing can fail when it tries to use it as a reference map. | Treats it as an empty cache and fetches evidence again. |
| Jev omits the chosen label from `probabilities`, but supplies another label | Fails when reading the chosen probability. | Reports `0%` for the choice and uses the other label as runner-up. |
| Jev supplies a nonnumeric probability | Arithmetic or sorting can fail. | Converts that probability to zero. |
| Missing storefront fields | Required dictionary lookups can fail. | Several missing fields become JSON `null` or empty arrays instead. |

Use one reference file, nonempty keys, ordinary numeric IDs, and unmodified caches for consistent normal runs.
Neither version performs complete validation of remote response fields.

## Error handling

Both versions catch failures within each project, print an error, and continue with later projects.
They leave failed projects out of the result array and return status `1` if any project failed.
Neither adds application-level retries or a backoff policy to wait between retries.

The Python HTTP call sets a 60-second timeout.
Rust sets no timeout in Modhopper itself.
The locked `ureq` 2.12.1 defaults to a 30-second connection timeout, with no read, write, or overall timeout.
Thus the same stalled response can keep Rust waiting after Python has failed.

Setup errors happen before the per-project handler.
A missing `--file` input causes a Python traceback with status `1`; Rust prints an error with status `2`.
Malformed category JSON or invalid cache JSON also aborts the entire run.
Python raises an exception; Rust uses `expect`, which ends the program with a panic message.
The error text is not byte-identical.

## What the check proves

`check.py` builds the Rust development executable and runs both versions twice.
It compares all four output streams with `fixtures/expected.json`.
It also compares the two saved cache files byte for byte.

This protects the recorded success cases and output formatting.
It does not prove identical argument parsing, timeouts, malformed-response behavior, or live model choices.
See [Offline check](offline-check.md) for the exact coverage and fixture procedure.
