# Python versus Rust

Both versions fetch the same evidence, ask the same question, and format the same valid answer.
Choose Python for the shortest setup.
Choose Rust if you want a compiled executable.
The shared check compares output, cache files, and the raw bytes of Jev requests.
Some build and failure details still differ.

## Dependencies, build, and installation

| | Python | Rust |
| --- | --- | --- |
| Entry point | `python/modhopper.py` | `rust/src/main.rs` |
| Dependencies | Python 3.8 or newer; standard library only | `ureq` 2 with its `json` feature; `serde_json` 1 |
| Preparation | Keep the checkout and a Python interpreter. No package installation. | Build with Cargo. `rust/Cargo.lock` records exact dependency versions; use `--locked`. |
| Run | `python3 python/modhopper.py modrinth:sodium` | `./rust/target/release/modhopper modrinth:sodium` |
| Category definitions | Reads `categories.json` beside the source tree at startup | Embeds `categories.json` at build time; rebuild after edits |
| Moving the program | Move the checkout, including `categories.json`. | The built executable can move without the checkout. |

Neither version has a packaged installer in this repository.
The Rust package uses the 2021 language edition.
Its manifest does not declare a minimum Rust version; the locked dependencies determine the build requirements.
CI uses stable Rust.
The [getting started commands](getting-started.md#build-and-run-rust) build the executable without installing it globally.

## One timing sample

Measured on 2026-09-28 using the implementation from commit `5d90c91`.
The machine was an Apple M4 Max with 48 GiB of memory and macOS 26.6.2.
The tools were Python 3.14.7, Rust 1.98.1, and Cargo 1.98.1.
Rust used `cargo build --release --locked --manifest-path rust/Cargo.toml`.

| Wall-clock elapsed time | Python | Rust |
| --- | ---: | ---: |
| Startup through `--help` exit | 57.16 ms | 297.59 ms |
| All 165 references, empty cache | 517.47 ms | 231.53 ms |
| Same references, populated cache | 201.45 ms | 130.39 ms |

Each cell is one measurement with no warm-up or averaging.
Startup was the first invocation of each command in this measurement session, including operating-system launch overhead.
It is not an estimate of steady-state startup cost.
Compilation time is excluded.

For the classification rows, a local `check.Fake` server served the recorded responses.
Both commands read `fixtures/refs.txt` and used separate temporary cache files.
Python's `time.perf_counter()` measured each `subprocess.run()` through exit, with output captured.
Every classification output matched `fixtures/expected.json` byte for byte.
No real storefront or Jev request was timed.
These numbers describe local processing, not live service latency or a general speed guarantee.

## Shared behavior

Both versions now process positional references before references from files.
Repeated `--file` options append files in option order.
Empty environment variables act as unset values.
Both require valid identifiers and the same evidence field types before calling Jev.
Both preserve unrelated cache entries during `--refresh` and update memory only after a successful save.
The [command guide](getting-started.md#references-and-files) and [answer parser](questions-and-state.md#parse-the-answer) describe the shared rules.

## Error handling

Both versions catch failures within each project, print an error, and continue with later projects.
They omit failed projects from the result array and return status `1` if any project failed.
A missing input file, unusable arguments, or a cache that cannot be read as a JSON object ends the run with status `2`.
A closed output pipe returns status `1` without a traceback or panic.
Operating-system error text can differ.

The following HTTP policy applies to storefront fetches and Jev requests:

| Response or failure | Behavior |
| --- | --- |
| HTTP `429` or `503` | Up to three attempts in total, with a wait before each retry. |
| `Retry-After` containing ASCII digits | Wait between 1 and 30 seconds. Zero becomes 1; values above 30 become 30. See the long-header exception below. |
| Missing, signed, date-formatted, or otherwise invalid `Retry-After` | Wait 1 second. |
| HTTP `500` or other non-retryable error | Fail the project after that attempt. |
| Redirect, such as HTTP `302` | Refuse to follow it and fail the project. No API key is forwarded to the redirect target. |
| Connection or timeout error | Fail the project without an application-level retry. |
| Invalid JSON response | Fail the project with a message naming the URL. |

Both configure a 60-second HTTP timeout, but its scope differs as described below.
HTTP response bodies must be UTF-8 JSON without a byte order mark, an optional encoding prefix that these parsers reject.
They reject `NaN`, infinity, numbers outside finite 64-bit floating-point range, invalid Unicode, and nesting at 128 levels or deeper.
These strict response rules are separate from cache-file parsing.
Neither version sets a response-size limit.

Malformed storefront fields fail before classification.
Malformed Jev answers also fail when the required choice or numeric probability object is missing.
A missing probability for an otherwise valid choice is allowed: both display zero percent.
Unknown probability labels do not become the runner-up.
Neither version requires the probabilities to sum to one.

## Remaining differences

| Condition | Python | Rust |
| --- | --- | --- |
| Category edit after installation | Reads the edited file at the next start. | Keeps the embedded definitions until rebuilt. |
| Missing or malformed category JSON | Reports a startup error with status `2`. | Needs no runtime category file. Invalid JSON embedded during a build causes a panic at startup. |
| HTTP timeout | 60 seconds per socket operation. A response that keeps trickling data can take longer overall. | 60 seconds for one request. Retries start new requests. |
| A long, zero-padded `Retry-After`, such as `00000000001` | Treats any all-digit header longer than ten characters as 30 seconds. | Parses this example as 1 second. |
| Nonstandard cache JSON, such as `{"unused": NaN}` | The standard JSON decoder accepts it; a run can preserve this unused entry. | Rejects the cache and exits with status `2`. |

These are current limits, not recommended inputs.
Use valid JSON cache files and ordinary retry headers for consistent behavior.
The strict HTTP parser does not make Python's cache and category decoders equally strict.

## What the check proves

`check.py` builds the Rust development executable and runs both versions twice on 165 references.
It compares all four output streams with `fixtures/expected.json`, both saved cache files, and the sets of raw Jev request bodies.

This protects the saved success cases and byte formatting.
It does not prove identical request order, timeout behavior, every malformed input, or live model choices.
The [offline check](offline-check.md) also runs in GitHub Actions on every push and pull request.
