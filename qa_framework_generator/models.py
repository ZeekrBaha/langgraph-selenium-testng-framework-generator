from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class LocatorDef(BaseModel):
    name: str
    by: str
    value: str
    confidence: Literal["high", "medium", "low"] = "high"


class PageObjectOutput(BaseModel):
    class_name: str
    package_name: str
    elements: list[LocatorDef] = Field(default_factory=list)
    extra_methods: list[str] = Field(default_factory=list)

    def has_placeholder_locators(self) -> bool:
        return any(el.confidence == "low" for el in self.elements)


class TestStep(BaseModel):
    action: str
    target: str | None = None
    value: str | None = None


class TestCaseOutput(BaseModel):
    class_name: str
    package_name: str
    groups: list[str]
    steps: list[TestStep] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def groups_must_not_be_empty(self) -> "TestCaseOutput":
        if not self.groups:
            raise ValueError("groups must contain at least one TestNG group")
        return self


class RequirementsOutput(BaseModel):
    project_name: str
    package_name: str
    summary: str
    pages: list[dict[str, Any]] = Field(default_factory=list)
    flows: list[dict[str, Any]] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    browsers: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class BlueprintOutput(BaseModel):
    page_classes: list[str] = Field(default_factory=list)
    test_classes: list[str] = Field(default_factory=list)
    package_name: str
    test_groups: list[str] = Field(default_factory=list)
    maven_commands: list[str] = Field(default_factory=list)


class ReviewOutput(BaseModel):
    passed: bool
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
