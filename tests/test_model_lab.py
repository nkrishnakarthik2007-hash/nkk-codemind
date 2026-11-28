from codemind.model_lab import CANDIDATES, TASKS, benchmark_models, save_benchmark_report

class FakeProvider:
    def generate(self, model, prompt, **kwargs):
        class Result:
            text = "ok"
            generated_tokens = 10
            prompt_tokens = 20
            total_duration_ns = 1_000_000_000
        return Result()

def test_candidates_are_unique_and_include_code_specialist():
    assert len({item.tag for item in CANDIDATES}) == len(CANDIDATES)
    assert any("code" in item.roles for item in CANDIDATES)

def test_benchmark_runs_all_tasks_sequentially():
    report = benchmark_models(FakeProvider(), ["a", "b"])
    assert len(report["results"]) == 2 * len(TASKS)
    assert all(row["tokens_per_second"] == 10 for row in report["results"])
    assert report["settings"]["mode"] == "sequential-unloaded"

def test_report_is_saved(tmp_path):
    path = tmp_path / "nested" / "report.json"
    save_benchmark_report(benchmark_models(FakeProvider(), ["a"]), path)
    assert '"schema_version": 1' in path.read_text(encoding="utf-8")
