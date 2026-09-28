# Setting up Jev

Jev is TypeSafe's System One model.
It answers questions with structured values, such as a choice from a list.
Modhopper uses TypeSafe's application programming interface (API), the web service that accepts these requests.
It sends one question per project and receives a category and probabilities.
See the [TypeSafe introduction](https://docs.typesafe.ai/introduction).

## Get and set a key

Sign in to the [TypeSafe console's API Keys page](https://console.typesafe.ai/keys) and create a key.
You need an account with API access.
Follow the console's current access instructions if you cannot create one.
The [official quick start](https://docs.typesafe.ai/introduction/quickstart) links to this page.

In a Bash or Zsh terminal, this command asks for the key without displaying it:

```sh
export TYPESAFE_API_KEY="$(python3 -c 'import getpass; print(getpass.getpass("TypeSafe API key: "))')"
```

The exported variable is available to commands started from that shell.
Modhopper sends it in the `Authorization` header with the `Bearer` scheme.
Neither version reads a `.env` file automatically.
Do not put keys in source files, saved output, or shell commands recorded in history.
Keep shell tracing disabled while setting or using keys.

## Choose the endpoint

An endpoint is the URL that receives a request.
`TYPESAFE_BASE_URL` defaults to `https://api.typesafe.ai`.
An empty value also uses that default.
Modhopper appends `/v1/systemone` and sends a JSON `POST` request there.
To use the public service explicitly:

```sh
export TYPESAFE_BASE_URL=https://api.typesafe.ai
```

Change this variable only when using a compatible proxy or gateway, a service that forwards requests to Jev.
Set it to that service's base URL, without a trailing slash or `/v1/systemone`.
The service must accept the [same request and response format](questions-and-state.md#the-request).
A chat API is not a drop-in replacement.

Only send your key to a service you trust.
Modhopper sends the configured key to the configured base URL.
If your gateway supplies its own key, omit the client key with `unset TYPESAFE_API_KEY`.
When the variable is absent or empty, both versions omit the authorization header.

## Check the setup

From the repository root, run:

```sh
python3 python/modhopper.py modrinth:sodium
```

A working setup prints a result with `category` and `reason`, then exits with status `0`.
The progress message `classifying modrinth:sodium` alone does not prove that Jev answered.
A cache hit still calls Jev, so repeating this command also tests the connection.

An HTTP `401` or `403` error indicates an authentication or access problem at the URL shown.
Check the key, the account's access, and the base URL.
A missing client key is not rejected locally; the public service rejects unauthenticated requests.
The [offline check](offline-check.md) can verify local code without a key, but cannot verify your TypeSafe account.
HTTP `429` and `503` receive up to three attempts.
Other HTTP errors, including `500` and redirects such as `302`, fail without a retry.
See the [request policy](python-versus-rust.md#error-handling).
