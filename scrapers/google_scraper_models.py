from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, HttpUrl


NonEmptyStr = Annotated[str, StringConstraints(min_length=2, strip_whitespace=True)]

class GoogleJobPosting(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: NonEmptyStr
    company: NonEmptyStr
    location: NonEmptyStr
    link: HttpUrl
    date_posted: Optional[str] = Field(default=None, alias="datePosted")
    employment_type: Optional[str] = Field(default=None, alias="employmentType")
    description: NonEmptyStr


class GoogleScrapeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    query: str = ""
    jobs: List[GoogleJobPosting] = Field(default_factory=list)
    url: Optional[str] = None
    original_html_length: Optional[int] = Field(default=None, alias="originalHtmlLength")

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "GoogleScrapeResponse":
        return cls.model_validate(data)
