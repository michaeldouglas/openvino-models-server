from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from local_llm.config import ModelDefinition, Settings


@dataclass(frozen=True)
class ModelManifest:
    alias: str
    servable_name: str
    source: str = "configured-runtime"
    revision: str = "unknown"
    precision: str = "unknown"
    license: str = "unknown"
    devices: tuple[str, ...] = ("GPU", "CPU")
    path: Path | None = None

    @classmethod
    def from_definition(cls, definition: ModelDefinition) -> ModelManifest:
        return cls(alias=definition.alias, servable_name=definition.servable_name)


def configured_manifests(settings: Settings) -> tuple[ModelManifest, ...]:
    return tuple(ModelManifest.from_definition(item) for item in settings.model_definitions())
