from pcro.model_profiles import ModelRegistry


def test_model_profiles_do_not_pool_models():
    registry = ModelRegistry()
    for _ in range(10):
        registry.observe("gemma_4", "family", succeeded=True, latency_ms=100)
        registry.observe(
            "gpt_oss", "family", succeeded=False, latency_ms=400, failure_stage="parser_invalid"
        )
    gemma = registry.profile("gemma_4").family("family")
    gpt = registry.profile("gpt_oss").family("family")
    assert gemma.success.posterior_mean > gpt.success.posterior_mean
    assert gemma.latency.mean_ms < gpt.latency.mean_ms
    assert gpt.parser_failures == 10
