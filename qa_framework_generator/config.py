from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
import yaml


class EnvConfig(BaseModel):
    base_url: str


class ElementDef(BaseModel):
    name: str
    by: Literal["css", "xpath", "id", "name", "class", "tag", "link_text", "partial_link_text"]
    value: str


class PageDef(BaseModel):
    name: str
    path: str = "/"
    elements: list[ElementDef] = Field(default_factory=list)


class FlowDef(BaseModel):
    name: str
    groups: list[str] = Field(default_factory=lambda: ["smoke"])
    steps: list[dict] = Field(default_factory=list)


class ParallelConfig(BaseModel):
    enabled: bool = True
    thread_count: int = 3


class FrameworkConfig(BaseModel):
    project_name: str
    package_name: str = "com.generated.qa"
    output_dir: str = "selenium-testng-framework-output"
    environments: dict[str, EnvConfig] = Field(
        default_factory=lambda: {
            "dev": EnvConfig(base_url="http://localhost"),
            "qa": EnvConfig(base_url="http://localhost"),
        }
    )
    browsers: list[str] = Field(default_factory=lambda: ["chrome"])
    headless_default: bool = True
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    pages: list[PageDef] = Field(default_factory=list)
    flows: list[FlowDef] = Field(default_factory=list)


def load_config(path: str) -> FrameworkConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return FrameworkConfig(**data)
