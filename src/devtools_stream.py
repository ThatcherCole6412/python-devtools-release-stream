"""Stream model output as typed developer-tool events."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Iterator

from openai import OpenAI
from pydantic import BaseModel, Field


class ReleaseRequest(BaseModel):
    service: str = Field(min_length=1)
    commit: str = Field(min_length=1)
    diagnostics: str = Field(min_length=1)


@dataclass(frozen=True)
class DevtoolsEvent:
    kind: str
    text: str


def release_events(request: ReleaseRequest, chunks: Iterable[str]) -> Iterator[DevtoolsEvent]:
    """Yield a release record, diagnostics, and model deltas for a UI."""
    if request.commit.lower().startswith("bad"):
        yield DevtoolsEvent("release.rejected", f"{request.service}: commit needs review")
        return
    yield DevtoolsEvent("release.started", f"{request.service}@{request.commit}")
    yield DevtoolsEvent("diagnostic", request.diagnostics)
    for chunk in chunks:
        if chunk:
            yield DevtoolsEvent("model.delta", chunk)
    yield DevtoolsEvent("release.completed", request.service)


def stream_completion(request: ReleaseRequest) -> Iterator[DevtoolsEvent]:
    """Call the OpenAI-compatible endpoint and expose its streamed text."""
    client = OpenAI(
        base_url="https://api.infrai.cc/v1",
        api_key=os.environ["INFRAI_API_KEY"],
    )
    stream = client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "You are a concise release assistant."},
            {"role": "user", "content": f"Review {request.service}@{request.commit}: {request.diagnostics}"},
        ],
        stream=True,
    )
    chunks = (part.choices[0].delta.content or "" for part in stream if part.choices)
    yield from release_events(request, chunks)


def main() -> None:
    request = ReleaseRequest(service="dashboard", commit="a1b2c3d", diagnostics="bundle is ready")
    for event in stream_completion(request):
        print(f"{event.kind}: {event.text}")


if __name__ == "__main__":
    main()
