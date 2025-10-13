from dataclasses import dataclass
from typing import Literal, Any

from pydantic import BaseModel, Field


class FactCheckClaim(BaseModel):
    claim: str = Field(description="The exact text of the claim being verified")
    verdict: Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"] = Field(
        description="The verdict on the claim"
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Confidence level in the verdict"
    )
    explanation: str = Field(description="Brief explanation of the assessment")
    context_needed: str | None = Field(
        default=None, description="Any important context or nuance"
    )


class FactCheckResponse(BaseModel):
    claims_analyzed: list[FactCheckClaim] = Field(description="List of analyzed claims")
    overall_assessment: str = Field(description="Summary of the fact-check results")
    requires_current_data: bool = Field(
        description="Whether claims require real-time verification"
    )
    needs_web_search: bool = Field(
        description="Whether web search would improve accuracy"
    )


@dataclass
class StreamEventResult:
    text_delta: str = ""
    tool_id: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
