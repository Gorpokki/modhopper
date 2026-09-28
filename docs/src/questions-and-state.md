# Questions and state

Here, **request state** means the evidence sent to Jev for one project.
**Saved state** means the storefront cache kept between runs.
They are separate: Modhopper saves evidence, then asks Jev again on every run.

## The request

Both versions send `POST /v1/systemone` to `TYPESAFE_BASE_URL`.
They set `Content-Type: application/json`.
They send one project per request, in sequence.
There is no conversation history or batch of projects in a request.

```mermaid
flowchart TD
    accTitle: One Jev request and response
    accDescr: The request contains a model, project state, and one Choice question. Modhopper reads the response's choice and probabilities to produce category and reason.
    subgraph Request["Request body"]
        Model["model: jev-latest"]
        State["state<br/>name · summary · description<br/>storefront_categories"]
        Question["questions.category<br/>type: choice<br/>instructions · criteria"]
    end
    Request -->|POST /v1/systemone| Jev["Jev"]
    Jev --> Response
    subgraph Response["Response body"]
        Answer["answers.category<br/>type · choice · probabilities · confidence"]
        Metadata["model · usage"]
    end
    Answer -->|choice| Category["Output category"]
    Answer -->|probabilities| Reason["Format reason with the choice and runner-up"]
```

The category definitions become `criteria`.
Modhopper reads `choice` and `probabilities`; it ignores the other response fields shown.

This is the request body for the recorded CurseForge project `curseforge:238222`.
JSON object key order and spacing can differ between implementations; the fields and values match.
The `criteria` object below is included directly from `categories.json` when this book builds.

```json
{
  "model": "jev-latest",
  "state": {
    "name": "Just Enough Items (JEI)",
    "summary": "JEI is an item and recipe viewing mod for Minecraft, built from the ground up for stability and performance.",
    "description": "",
    "storefront_categories": ["Map and Information", "Utility & QoL"]
  },
  "questions": {
    "category": {
      "type": "choice",
      "instructions": "Which category fits this Minecraft mod best? Judge from `name`, `summary`, `description`, and `storefront_categories`.",
      "criteria":
{{#include ../../categories.json}}
    }
  }
}
```

| Field | Meaning and purpose |
| --- | --- |
| `model` | `jev-latest` asks for TypeSafe's current model under that alias. The code fixes this value; there is no model option. |
| `state.name` | The project's name supplies its identity. |
| `state.summary` | The short storefront description supplies a concise statement of purpose. |
| `state.description` | The first 2,000 characters of the long description add context while limiting its size. CurseForge sends an empty string. |
| `state.storefront_categories` | The source website's labels supply another signal. These are evidence, not the allowed answers. |
| `questions.category` | `category` names the question so the code can find its answer. |
| `type` | `choice` requests one label from a defined set. |
| `instructions` | The fixed question asks for the best fit using the four evidence fields. |
| `criteria` | The full category object defines the allowed labels and what each means. |

The description limit counts characters, not bytes or words.
The code does not remove Markdown or HTML, and does not limit the other fields.
It does not send the project reference, source name, download counts, versions, or dependencies as separate fields.
Those details can still appear inside the source's text.

This structure separates project facts from category definitions.
A single Choice question fits the output: one category per project.
The probability table supports the short result sentence without a second question.

## Change the categories

Edit `categories.json` at the repository root.
Each JSON object key is an output label.
Its string value explains that label to Jev.
Both versions read this file when they start, even when all evidence is cached.

Add or rename a key to change the possible answers.
Edit its description to change the classification rule.
Keep valid JSON and at least two choices: the result formatter requires a runner-up.
The code does not validate the whole category file before sending it.

You do not need to refresh the evidence cache after a category edit.
Update the recorded answers and expected output in the [offline check](offline-check.md#add-a-fixture) to match any new labels.
The check does not ask the real model to reconsider saved answers.

## Parse the answer

Both versions read `answers.category` from the response.
They use `choice` as the output `category` and reject a choice absent from `categories.json`.
They then read `probabilities`, which maps labels to numbers.

To find the runner-up, they sort by probability from highest to lowest.
Equal probabilities sort by label in alphabetical order.
The first label other than `choice` becomes the runner-up.
The output follows `choice`, even if another label has a higher probability.

For each displayed percentage, the code multiplies the probability by 100, adds 0.5, and converts to an integer.
Thus the recorded `0.995` becomes `100%`.
The `reason` is the fixed sentence shown in the [output example](getting-started.md#read-the-output).
It does not explain which words led to the decision.

The code ignores the response's `confidence`, resolved `model`, and `usage` fields.
It applies no minimum probability or confidence threshold.
Malformed answers can produce [different results or errors](python-versus-rust.md#behavioral-differences).

## The cache

By default, `metadata-cache.json` is a JSON object in the directory where you run the command.
`--cache <path>` selects a different file.
Its parent directory must already exist.

Each key is the exact input reference, such as `modrinth:sodium`.
Each value contains `name`, `summary`, `description`, and `categories` from the storefront fetch.
The cache keeps the full fetched Modrinth description; only the Jev request truncates it.
Two references for the same project, such as a slug and an ID, create separate entries.

The cache never holds API keys, request headers, Jev answers, probabilities, reasons, or category definitions.
There are no timestamps or expiry rules.
The tool does not detect changes on the source website.
Both implementations can read the same valid cache file.
Do not run simultaneous writers against it: there is no file lock.

After each new fetch, the tool saves the cache before calling Jev.
Evidence survives a later classification failure.
It writes a sibling file with `.tmp` appended to the cache filename, then renames it over the cache.
This avoids replacing the cache with a partly written JSON file.

## Refresh and offline reruns

```sh
python3 python/modhopper.py --cache metadata-cache.json --refresh modrinth:sodium
```

`--refresh` starts with an empty in-memory cache for the entire run.
The first successful fetch replaces the saved cache.
Old entries that are not fetched in this run are then gone.
If every fetch fails, no replacement is written.
Repeated references within the run still reuse the newly fetched evidence.
Use a different `--cache` path if you need to preserve the old file.

A normal rerun can work while the storefronts are unavailable, if every reference is already cached.
It still calls Jev for every reference.
The cache alone does not support a fully offline classification run.
Use [the fixture server](offline-check.md) for a fully offline check of request handling and output.
