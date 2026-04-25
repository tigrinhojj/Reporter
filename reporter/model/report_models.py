import datetime
from datetime import date
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field
from reporter.consts import RELEASE_INDICATOR


class ReleaseSchedule(BaseModel):
    name: str
    scheduled: Optional[date] = None
    raw: str

    @classmethod
    def from_string(cls, label: str) -> Optional["ReleaseSchedule"]:
        if label == "future":
            return ReleaseSchedule(raw=label, name=label, scheduled=None)
        try:
            raw_date, raw_version, *_ = label.split("→")
            parsed_date = None
            try:
                parsed_date = datetime.datetime.strptime(
                    raw_date.strip(), "%Y.%m.%d"
                ).date()
            except Exception:
                pass

            return ReleaseSchedule(
                raw=label, name=raw_version.strip(), scheduled=parsed_date
            )
        except Exception:
            return None


def segregate_release_labels(labels: List[str]) -> Tuple[List[str], List[str]]:
    return list(filter(lambda label: is_release_label(label), labels)), list(
        filter(lambda label: not is_release_label(label), labels)
    )


def is_release_label(label: str) -> bool:
    return RELEASE_INDICATOR in label or label == "future" or label == "tag-needed"


class ReleaseIssue(BaseModel):
    id: int
    iid: int
    title: str
    link: str
    labels: List[str] = Field(default_factory=list)
    release_infos: List[ReleaseSchedule] = Field(default_factory=list)
    closed: bool
    merge_requests_count: int

    def model_post_init(self, __context) -> None:
        release_labels, other = segregate_release_labels(self.labels)
        self.labels = other
        self.release_infos = [
            ri
            for ri in [ReleaseSchedule.from_string(label) for label in release_labels]
            if ri is not None
        ]

    @property
    def bug(self) -> bool:
        return "bug" in self.labels

    @property
    def feature(self) -> bool:
        return "feature" in self.labels

    @property
    def send_to_external(self) -> bool:
        return "send-to-external" in self.labels

    @property
    def waiting_for_approval(self) -> bool:
        return "for-approval" in self.labels

    @property
    def technicalsupport(self) -> bool:
        return "technicalsupport" in self.labels

    @property
    def has_mrs(self) -> bool:
        return self.merge_requests_count > 0

    @property
    def odd(self) -> bool:
        return len(self.release_infos) == 0

    @property
    def no_dev(self) -> bool:
        return self.merge_requests_count == 0


class Project(BaseModel):
    name: str
    link: str
    issues: List[ReleaseIssue] = Field(default_factory=list)
    odd_issues: List[ReleaseIssue] = Field(default_factory=list)
    release_info: ReleaseSchedule

    @property
    def has_release_related_changes(self) -> bool:
        return len(self.issues) + len(self.odd_issues) > 0


class Release(BaseModel):
    projects: List[Project] = Field(default_factory=list)
    info: ReleaseSchedule


class ReportType(str, Enum):
    release = "release"
    test = "test"
    all = "all"
