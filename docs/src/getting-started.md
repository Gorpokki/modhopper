# Getting started

Install Python 3.8 or newer.
For the Rust version, also install [Rust and Cargo](https://www.rust-lang.org/tools/install).
Cargo is Rust's build and package tool.
The [comparison](python-versus-rust.md) lists the versions used for validation.

Clone the repository, then run all commands from its root:

```sh
git clone https://github.com/gorpokki/modhopper.git
cd modhopper
```

Set up your [Jev key](jev.md) before a live run.
Modrinth needs no key.
CurseForge references also need a [CurseForge key](curseforge.md) when fetching project information.

## Run Python

No Python packages need to be installed.

```sh
python3 python/modhopper.py modrinth:sodium
```

## Build and run Rust

Build an optimized executable:

```sh
cargo build --release --locked --manifest-path rust/Cargo.toml
./rust/target/release/modhopper modrinth:sodium
```

The executable includes `categories.json` from build time.
You can move it without the checkout.
Rebuild it after changing the categories.

For a development run, Cargo can build and start the program in one command:

```sh
cargo run -q --locked --manifest-path rust/Cargo.toml -- modrinth:sodium
```

The `--` separates Cargo options from Modhopper options.
Cargo uses a development build here, rather than the optimized build above.

## References and files

A reference identifies a project and its source:

| Format | Example |
| --- | --- |
| `modrinth:<slug-or-id>` | `modrinth:sodium` or `modrinth:AANobbMI` |
| `curseforge:<numeric-id>` | `curseforge:32274` |

A slug is the short name in a project's URL.
Modrinth identifiers accept ASCII letters, digits, and `` !@$()`.+_- ``.
ASCII is the basic character set used for these English letters and symbols.
Use a project ID if a slug contains a comma, double quote, or single quote.
Put a reference in single quotes if it contains shell symbols such as `$` or backticks.
CurseForge IDs accept only ASCII digits.
Full website URLs and CurseForge slugs are not accepted reference formats.

Put one reference on each line to use `--file`:

```sh
printf '%s\n' 'modrinth:sodium' 'modrinth:fabric-api' > refs.txt
python3 python/modhopper.py --file refs.txt
./rust/target/release/modhopper --file refs.txt
```

Both versions read UTF-8 text and split it on newline characters.
UTF-8 is the text encoding used for their input files, cache, requests, and output.
They trim spaces, tabs, and carriage returns at each line's ends, then skip empty lines.
Both Unix and Windows line endings work.
They do not support comments in this file.
Repeated references produce repeated classifications.
Both process all positional references first, then each `--file` in option order.
You can repeat `--file` and mix options with positional references.
Files without valid UTF-8 and non-UTF-8 command-line arguments cause a setup error.

| Option | Meaning |
| --- | --- |
| `--file <path>` | Read references from a text file. Repeat to read more files. |
| `--cache <path>` | Use this JSON cache file. The default is `metadata-cache.json` in the current directory. |
| `--refresh` | Fetch the requested references again while preserving other cached projects. See [refresh details](questions-and-state.md#refresh-and-offline-reruns). |
| `-h`, `--help` | Print usage and exit. |

`--file=refs.txt` and `--cache=metadata-cache.json` also work.
`--` ends option parsing.
Long-option abbreviations and `--refresh=true` are not accepted.
A bare `-` or a negative number is read as a reference, then fails reference validation.

## Read the output

Standard output, the command's normal output stream, contains one JSON array.
Each successful reference adds one object.
Progress and errors go to standard error, a separate stream.
To save results:

```sh
python3 python/modhopper.py modrinth:sodium > results.json
```

This is the Sodium result from a run against the recorded responses in `fixtures/`.
Live probabilities can differ.

```json
[
  {
    "categories": [
      "optimization"
    ],
    "category": "tools",
    "name": "Sodium",
    "reason": "Jev chose tools with 95% probability; runner-up visuals at 5%.",
    "reference": "modrinth:sodium",
    "source": "modrinth"
  }
]
```

`categories` contains the source website's labels.
`category` is Jev's choice from `categories.json`.
`reason` reports that choice and the next highest probability.
It is a sentence assembled by Modhopper, not an explanation written by Jev.

A run exits with status `0` when all references succeed.
It exits with status `1` when any project fails, while keeping successful projects in the array.
Check the exit status before treating the saved array as complete.
Both versions use status `2` for unusable arguments, input files, or a cache that cannot be read as a JSON object.
A closed output pipe exits with status `1` without a traceback or panic.
See [error handling](python-versus-rust.md#error-handling) for HTTP retries and validation.
