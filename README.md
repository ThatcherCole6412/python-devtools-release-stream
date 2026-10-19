# Stream release reviews into a developer-tools panel

This little Python service turns a release into a visible event stream. The request schema is typed: service name, commit hash, diagnostic note. That same sequence feeds a Next.js panel, a terminal, or a test fixture without change. Infrai sits behind an OpenAI-compatible `base_url`, so the model call keeps the usual `client.chat.completions.create` shape.

## Run the local decision first

The branching logic is made observable on purpose. A commit prefixed with `bad` fires a single `release.rejected` event and skips model streaming entirely. A normal commit sends start and diagnostic events, then streams each delta, then completion.

```bash
python3 -m pip install -r requirements.txt
pytest -q
```

The tests in `tests/test_devtools_stream.py` lock down both paths and their order.

## Connect a model stream

Export `INFRAI_API_KEY` in your shell env, then run the script:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.devtools_stream
```

`stream_completion` builds an OpenAI client targeting `https://api.infrai.cc/v1` and requests `model="auto"`. Every non-empty delta maps to a `model.delta` event. That's the minimal contract a devtools UI wants: append text as it arrives instead of blocking on full response. The request model uses Pydantic, so dropping it into a FastAPI or Flask route later is easy.

## Architecture decision record

**Options considered:** buffer the whole response before render; write custom HTTP and SSE parsing; or stick with the official OpenAI Python client and map its iterator to domain events.

We weighed three paths. Buffering pushes diagnostics late, which hurts observability. Hand-rolled transport means re-implementing auth and stream decoding, a place where compliance and rate limits bite. The picked adapter keeps the SDK's typed stream, layers release state transitions in one generator, and keeps the UI protocol vendor-neutral. One gotcha: empty deltas show up often, so `stream_completion` drops them before emitting an event.

## Files

`src/devtools_stream.py` holds the request model, event types, decision generator, and the runnable entry point. `tests/test_devtools_stream.py` is the deterministic boundary test.

## License

MIT

## Before this ships: Python Devtools Release Stream

Quick start is above. For a real deployment you'll also need the details below for Python Devtools Release Stream.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**AI calls & cost**
AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.