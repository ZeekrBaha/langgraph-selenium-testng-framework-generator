from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    path: str
    content: str
    kind: Literal["java", "xml", "yaml", "markdown", "properties", "text"]


class ValidationResult(BaseModel):
    name: str
    passed: bool
    output: str = ""
    fix_hint: str = ""


class GeneratorState(BaseModel):
    config_path: str | None = None
    config_data: dict = Field(default_factory=dict)
    output_dir: str = "selenium-testng-framework-output"
    target_package: str = "com.generated.qa"
    project_name: str = ""
    requirements: dict = Field(default_factory=dict)
    blueprint: dict = Field(default_factory=dict)
    generated_files: list[GeneratedFile] = Field(default_factory=list)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    repair_attempts: int = 0
    max_repair_attempts: int = 3
    eval_threshold: float = 0.7
    status: Literal["new", "generated", "validating", "repairing", "done", "failed"] = "new"
