# Modhopper

Sort Minecraft mods from Modrinth and CurseForge into categories with Jev, TypeSafe's System One decision model.
A proof of concept with Python and Rust implementations.

**[Read the documentation](https://gorpokki.github.io/modhopper/)** for setup, API keys, questions, caching, and implementation differences.
The site's Markdown source is in [`docs/src/`](docs/src/SUMMARY.md).

Run Python 3.8 or newer after [setting up Jev](docs/src/jev.md):

```sh
python3 python/modhopper.py modrinth:sodium
```

Or build Rust with Cargo (Rust 1.88 or newer), then run the executable it writes to `rust/target/release/`:

```sh
cargo build --release --locked --manifest-path rust/Cargo.toml
./rust/target/release/modhopper modrinth:sodium
```

The Rust executable includes `categories.json` when built; rebuild it after editing that file.
Both take `modrinth:<slug-or-id>` and `curseforge:<numeric-id>` references, or `--file` with one reference per line.
See [getting started](docs/src/getting-started.md) for all options and the CurseForge key.

Check both implementations with recorded responses and no service credentials (requires Python and Cargo):

```sh
python3 check.py
```

The same check runs on every push and pull request. See the [fixture guide](docs/src/offline-check.md) to record new responses.
