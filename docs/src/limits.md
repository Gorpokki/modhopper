# Limits and roadmap

Modhopper is a small proof of concept.
These are current gaps, not scheduled features.

- **Incomplete evidence.** CurseForge's full description is not fetched. Modrinth descriptions are limited to 2,000 characters in Jev requests. Promotional text and markup are kept.
- **One label per project.** The question chooses a single category, even for a mod with several purposes. `other` is a possible choice, not an automatic low-confidence fallback.
- **No correctness guarantee.** The tool uses the website's text. It does not inspect mod behavior, files, compatibility, or dependencies.
- **No confidence filter.** The tool ignores Jev's separate confidence value. The displayed reason reports probabilities, not supporting evidence.
- **Changing live results.** `jev-latest` can refer to a newer model over time. Normal runs do not save resolved model versions or past answers. The fixture recorder does save complete Jev responses.
- **Manual cache refresh.** Saved evidence has no expiry, and concurrent cache writers have no lock. A complete offline classification requires the fixture server.
- **Bounded retries.** Projects run one at a time. Only HTTP `429` and `503` are retried, with at most three attempts. Response size is not capped, and timeout behavior [differs between implementations](python-versus-rust.md).
- **Limited check coverage.** The offline check covers 165 saved projects. It does not establish live accuracy or cover every error path. Its CurseForge response is hand-written.
- **Separate category updates.** Editing `categories.json` changes the next Python run. Rust needs a rebuild to include those changes.

There is no release schedule in this repository.
Use these gaps to judge whether the current tool fits your use case.
