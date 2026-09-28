# Modhopper

Sort Minecraft mods from Modrinth and CurseForge into categories with Jev, TypeSafe's System One decision model.
A proof of concept with Python and Rust implementations.

**[Read the documentation](https://gorpokki.github.io/modhopper/)** for setup, API keys, questions, caching, and implementation differences.
The site's Markdown source is in [`docs/src/`](docs/src/SUMMARY.md).

Run Python after [setting up Jev](docs/src/jev.md):

```sh
python3 python/modhopper.py modrinth:sodium
```

Check both implementations with recorded responses and no service credentials (requires Python and Cargo):

```sh
python3 check.py
```
