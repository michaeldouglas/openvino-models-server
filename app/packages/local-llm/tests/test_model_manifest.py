from local_llm.config import Settings
from local_llm.core.model_manifest import configured_manifests


def test_configured_manifests_preserve_alias_and_servable_name() -> None:
    manifests = configured_manifests(
        Settings(ovms_model_names="fast=servable-fast", ovms_default_model="fast")
    )

    assert manifests[0].alias == "fast"
    assert manifests[0].servable_name == "servable-fast"
    assert manifests[0].devices == ("GPU", "CPU")
