# Getting started

Install Python 3.
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

Keep the checkout after building.
The executable reads `categories.json` from the checkout's build-time location.
Moving the executable does not move that path.

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
| `curseforge:<numeric-id>` | `curseforge:238222` |

A slug is the short name in a project's URL.
Use ordinary digits for CurseForge IDs.
Full website URLs and CurseForge slugs are not accepted reference formats.

Put one reference on each line to use `--file`:

```sh
printf '%s\n' 'modrinth:sodium' 'modrinth:fabric-api' > refs.txt
python3 python/modhopper.py --file refs.txt
./rust/target/release/modhopper --file refs.txt
```

Both versions trim whitespace and skip empty lines.
They do not support comments in this file.
Repeated references produce repeated classifications.
Use a single file to keep the same order in both versions.
Mixing files and positional references has [different ordering rules](python-versus-rust.md#behavioral-differences).

| Option | Meaning |
| --- | --- |
| `--file <path>` | Read references from a text file. |
| `--cache <path>` | Use this JSON cache file. The default is `metadata-cache.json` in the current directory. |
| `--refresh` | Start with an empty cache and fetch project information again. See [cache replacement](questions-and-state.md#refresh-and-offline-reruns). |
| `-h`, `--help` | Print usage and exit. |

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
    "reason": "Jev chose tools with 97% probability; runner-up visuals at 3%.",
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
Both versions use status `2` for command syntax errors.
Some file and setup errors [differ](python-versus-rust.md#error-handling).
