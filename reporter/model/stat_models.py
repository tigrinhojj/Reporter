import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StatIssue(BaseModel):
    id: int
    title: str
    labels: List[str] = Field(default_factory=list)
    created_at: datetime.datetime
    closed_at: Optional[datetime.datetime]
    sent_for_approval_at: Optional[datetime.datetime]
    removed_sent_for_approval_at: Optional[datetime.datetime]
    milestone_title: Optional[str]
    is_consulting: bool
    in_backlog: bool
    to_dd: bool
    on_dev: bool
    on_approval: bool
    on_analytics: bool
    release: Optional[str]
