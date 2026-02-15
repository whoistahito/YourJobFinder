from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GoogleJobPosting(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    link: str = Field(min_length=1)
    date_posted: Optional[str] = Field(default=None, alias="datePosted")
    employment_type: Optional[str] = Field(default=None, alias="employmentType")
    description: Optional[str] = None


class GoogleScrapeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    query: str = ""
    jobs: List[GoogleJobPosting] = Field(default_factory=list)
    url: Optional[str] = None
    original_html_length: Optional[int] = Field(default=None, alias="originalHtmlLength")

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "GoogleScrapeResponse":
        return cls.model_validate(data)
