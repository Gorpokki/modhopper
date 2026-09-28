# Modhopper

Sorts Minecraft mods from Modrinth and CurseForge into categories with Jev (TypeSafe System One). A proof of concept, in Python and in Rust; both give byte-identical output.

For each project it fetches the storefront name, summary, description, and categories, caches them, and asks Jev one Choice question: which entry of [`categories.json`](categories.json) fits best. The answer, the runner-up, and the storefront categories used as evidence go to stdout as JSON.

## Run

References are `modrinth:<slug-or-id>` or `curseforge:<numeric-id>`, on the command line or one per line in a file.

```sh
python3 python/modhopper.py modrinth:sodium curseforge:238222
cargo run -q --manifest-path rust/Cargo.toml -- --file refs.txt
```

Options: `--file <path>`, `--cache <path>` (default `metadata-cache.json`, storefront evidence only), `--refresh` (refetch). Progress and errors go to stderr; the exit code is non-zero if any project failed.

## Environment

| Variable | Purpose |
| --- | --- |
| `TYPESAFE_API_KEY` | Jev API key, sent as `Authorization: Bearer`. |
| `TYPESAFE_BASE_URL` | Jev endpoint base, default `https://api.typesafe.ai`. |
| `CURSEFORGE_API_KEY` | Required for any `curseforge:` reference, sent as `x-api-key`. Modrinth needs no key. |

`MODRINTH_BASE_URL` and `CURSEFORGE_BASE_URL` exist so the check below can point both implementations at fixtures.

## Check

```sh
python3 check.py
```

Builds the Rust binary, serves `fixtures/` as fake Modrinth, CurseForge, and Jev endpoints, runs both implementations against them twice (second run from cache), and asserts every output is byte-identical to `fixtures/expected.json`.
