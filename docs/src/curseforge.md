# CurseForge API key

CurseForge's project API requires a key.
It is separate from your TypeSafe key.

## Get and set a key

Start at the [CurseForge developer console](https://console.curseforge.com/).
CurseForge's [API documentation](https://docs.curseforge.com/rest-api/#authentication) identifies this console as the key source.
For third-party tools, follow the [API key application process](https://support.curseforge.com/support/solutions/articles/9000208346).
CurseForge reviews applications and contacts approved developers by email.
Use this project API key, not an upload API token.

In Bash or Zsh, enter the key without displaying it:

```sh
export CURSEFORGE_API_KEY="$(python3 -c 'import getpass; print(getpass.getpass("CurseForge API key: "))')"
python3 python/modhopper.py curseforge:238222
```

Set up the [Jev key](jev.md) too.
Keep shell tracing disabled and do not save either key in a file.

For a project fetch, Modhopper requests `https://api.curseforge.com/v1/mods/238222`.
It sends `CURSEFORGE_API_KEY` as the `x-api-key` header.
It reads the response's `data` object.

If the variable is absent, an uncached CurseForge reference fails before the request.
The error is `CURSEFORGE_API_KEY is not set; CurseForge references need it`.
The tool does not scrape the website, use an unofficial mirror, or guess a matching Modrinth project.
This keeps a failed authenticated lookup from becoming a classification of unrelated evidence.

A cached CurseForge project needs no storefront request, so it can run without this key.
It still needs Jev access.
`--refresh` requires the CurseForge key again.
An empty variable has [different behavior in the two versions](python-versus-rust.md#behavioral-differences); use a valid key or unset it.

## Evidence from each source

Evidence means the project information sent to Jev.

| Jev field | Modrinth project response | CurseForge `data` object |
| --- | --- | --- |
| `name` | `title` | `name` |
| `summary` | `description` | `summary` |
| `description` | `body`, or an empty string | Always an empty string |
| `storefront_categories` | `categories` followed by `additional_categories` | The `name` of each entry in `categories` |

Modrinth supplies its long description in the same project response.
CurseForge has a separate endpoint for its full HTML description.
Modhopper does not call that endpoint.
It uses only the summary and category names for additional context.
The two sources can therefore supply different amounts of evidence for the same mod.
