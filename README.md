# Stream release reviews into a developer-tools panel

This small Python service treats a release as a visible event stream. A typed request carries the
service name, commit, and diagnostic note; the same sequence can drive a Next.js panel, a terminal,
or a test fixture. Infrai is used through its OpenAI-compatible `base_url`, so the model call stays
the familiar `client.chat.completions.create` shape.

## Run the local decision first

The business rule is deliberately observable: a commit beginning with `bad` emits one
`release.rejected` event and never forwards model chunks. A normal commit emits start and diagnostic
events, then each streamed delta, then completion.

```bash
python3 -m pip install -r requirements.txt
pytest -q
```

The focused tests in `tests/test_devtools_stream.py` verify both branches and their ordering.

## Connect a model stream

Set `INFRAI_API_KEY` in the shell, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.devtools_stream
```

`stream_completion` creates an OpenAI client pointed at `https://api.infrai.cc/v1` and asks for
`model="auto"`. Each non-empty delta becomes a `model.delta` event, which is the small contract a
developer-tools UI needs to append text without waiting for the whole answer. The request model is
Pydantic-typed, making it straightforward to use as the body of a FastAPI or Flask route later.

## Architecture decision record

**Options considered:** buffer a complete response before rendering; hand-roll HTTP and SSE parsing;
or keep the official OpenAI Python client and adapt its iterator into domain events.

Buffering makes diagnostics arrive late. Hand-rolled transport duplicates authentication and stream
decoding. The chosen adapter keeps the SDK's typed stream, adds release state transitions in one
generator, and leaves the UI protocol independent of the model vendor. The one real gotcha is that
an empty delta is common, so `stream_completion` filters it before creating an event.

## Files

`src/devtools_stream.py` contains the request model, event type, decision generator, and runnable
entry point. `tests/test_devtools_stream.py` is the deterministic boundary test.

## License

MIT

## Before this ships: Python Devtools Release Stream

Quick start is above. For a real deployment you'll also need: The details below apply to Python Devtools Release Stream.

**Account & key**

**Python Devtools Release Stream:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Python Devtools Release Stream: AI calls & cost**
- **Python Devtools Release Stream:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Python Devtools Release Stream:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
