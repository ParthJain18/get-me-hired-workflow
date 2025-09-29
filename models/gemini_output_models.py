from pydantic import BaseModel, Field
from typing import List


class RankedJob(BaseModel):
    id: str = Field(description="The job ID from the input.")
    rank: int = Field(description="The numerical rank of the job.")
    company: str = Field(description="The name of the company.")
    title: str = Field(description="The job title.")
    url: str = Field(description="The URL for the job posting.")
    match_reason: str = Field(
        description="A brief, one-sentence explanation of why this is a top match.")


class RankingResponse(BaseModel):
    ranked_jobs: List[RankedJob]


class ExperienceResponse(BaseModel):
    min_years: int
    max_years: int


class ResumeContentResponse(BaseModel):
    summary_bullets: List[str] = Field(
        description="2-3 bullet statements summarizing fit for the role.")
    keywords: List[str] = Field(
        description="6-8 keyword phrases to emphasize in the resume.")
    highlight_bullets: List[str] = Field(
        description="3 concise, achievement-oriented bullet points aligned to the job.")
