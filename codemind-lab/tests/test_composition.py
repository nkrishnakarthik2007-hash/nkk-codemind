import codemind_lab.backends as backend_module
from codemind_lab.config import LabConfig
from gama.backends import ModelBackend
from gama.models import ModelTier


class StubBackend(ModelBackend):
    available = True

    def __init__(self, name):
        self.name = name
        self.calls = []

    def complete(self, prompt, tier, **kwargs):
        self.calls.append((prompt, tier, kwargs))
        return f"{self.name}:{prompt}"


def test_router_dispatches_to_task_specific_backend(monkeypatch):
    coding = StubBackend("coding")
    general = StubBackend("general")
    monkeypatch.setattr(
        backend_module,
        "build_backends",
        lambda config: ({"coding": coding, "general": general}, object()),
    )

    router = backend_module.build_router(LabConfig(models=()), {"code_implementation": "coding"})
    assert router.complete("write code", ModelTier.SMALL, task_type="code_implementation") == (
        "coding:write code"
    )
    assert router.complete("explain", ModelTier.SMALL, task_type="explanation") == (
        "general:explain"
    )


def test_sequential_ensemble_runs_candidates_and_aggregator(monkeypatch):
    first = StubBackend("first")
    second = StubBackend("second")
    monkeypatch.setattr(
        backend_module,
        "build_backends",
        lambda config: ({"first": first, "second": second}, object()),
    )

    ensemble = backend_module.build_sequential_ensemble(
        LabConfig(models=(), max_ensemble_members=2), ["first", "second"]
    )
    result = ensemble.complete("solve", ModelTier.SMALL)

    assert result
    assert len(first.calls) == 1
    # The final member is both a candidate and the configured synthesizer.
    assert len(second.calls) == 2
