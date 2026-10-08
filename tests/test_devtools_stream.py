from src.devtools_stream import ReleaseRequest, release_events


def test_rejected_release_does_not_emit_model_deltas():
    request = ReleaseRequest(service="web", commit="bad-feed", diagnostics="lint failed")
    events = list(release_events(request, ["should", "not", "stream"]))
    assert [(event.kind, event.text) for event in events] == [
        ("release.rejected", "web: commit needs review")
    ]


def test_completed_release_keeps_stream_order():
    request = ReleaseRequest(service="web", commit="abc123", diagnostics="tests passed")
    assert [event.kind for event in release_events(request, ["hi", "!"])] == [
        "release.started", "diagnostic", "model.delta", "model.delta", "release.completed"
    ]
