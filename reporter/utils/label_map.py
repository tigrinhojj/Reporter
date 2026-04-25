from enum import Enum
from typing import Dict

from pydantic import BaseModel

from reporter.model.report_models import ReleaseIssue


class LabelType(str, Enum):
    bug = "bug"
    feature = "feature"
    consultation = "consultation"
    working = "working"
    not_working = "not_working"
    partialy_working = "partialy_working"
    dknw = "dknw"
    send_to_external = "send_to_external"
    for_approval = "for_approval"


class LabelMapping(BaseModel):
    label_type: LabelType
    display_text: str
    html_class: str = ""


label_map: Dict[LabelType, str] = {
    LabelType.bug: "bug",
    LabelType.feature: "feat",
    LabelType.consultation: "consult",
    LabelType.working: "✅",
    LabelType.not_working: "❌",
    LabelType.partialy_working: "🃏",
    LabelType.dknw: "🤷",
    LabelType.send_to_external: "ext",
    LabelType.for_approval: "apprv",
}


def get_label_summary(issue: ReleaseIssue) -> str:
    labels = []

    if issue.bug:
        labels.append(label_map[LabelType.bug])

    if issue.feature:
        labels.append(label_map[LabelType.feature])

    if issue.waiting_for_approval:
        labels.append(label_map[LabelType.for_approval])

    if issue.send_to_external:
        labels.append(label_map[LabelType.send_to_external])

    if issue.closed and issue.technicalsupport and not issue.has_mrs:
        labels.append(label_map[LabelType.consultation])

    valid_labels = [label for label in labels if label]
    return f"[{','.join(valid_labels)}]" if valid_labels else ""


def get_label_summary_html(issue: ReleaseIssue) -> str:
    labels = []

    if issue.bug:
        labels.append("bug")

    if issue.feature:
        labels.append("feat")

    if issue.waiting_for_approval:
        labels.append("apprv")

    if issue.send_to_external:
        labels.append("ext")

    if issue.closed and issue.technicalsupport and not issue.has_mrs:
        labels.append("consult")

    valid_labels = [label for label in labels if label]
    if valid_labels:
        labels_html = ",".join(valid_labels)
        return f'<span class="labels">[{labels_html}]</span>'
    return ""
