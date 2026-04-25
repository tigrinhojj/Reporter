import os
from pathlib import Path
from typing import Optional, List

import mdformat

from reporter.utils.label_map import (
    get_label_summary,
    label_map,
    LabelType,
)
from reporter.model.report_models import Release, Project


def get_project_description(
    project: Project,
    testers: List[str],
    with_open: bool = False,
    dev_only: bool = False,
    with_odd: bool = False,
    with_support: bool = False,
) -> List[str]:
    has_open = any(filter(lambda i: not i.closed, project.issues))
    has_closed = any(filter(lambda i: i.closed, project.issues))
    has_odd = any(project.odd_issues)

    if not has_odd and not has_closed and not has_open:
        return []

    if not with_support and project.name == "iskra-support":
        return []

    description = [
        f"## Проект {project.name}",
    ]

    if has_closed:
        description.append("")
        description.append("## Закрытые")

        description.append("")
        description.append(f"| Задачи | {'|'.join(testers)} |")
        description.append(f"|-------| {'|'.join([':-------:' for _ in testers])} |")

        for issue in project.issues:
            if not issue.closed:
                continue

            if dev_only and issue.no_dev:
                continue

            summary = get_label_summary(issue)
            description.append(
                f"|[#{issue.iid}]({issue.link}){summary}| {'|'.join([label_map[LabelType.dknw] for _ in testers])} |"
            )

    if with_open and has_open:
        description.append("")
        description.append("## Открытые")
        description.append("")
        description.append(f"| Задачи | {'|'.join(testers)} |")
        description.append(f"|-------| {'|'.join([':-------:' for _ in testers])} |")

        for issue in project.issues:
            if issue.closed:
                continue
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary(issue)
            description.append(
                f"|[#{issue.iid}]({issue.link}){summary}| {'|'.join([label_map[LabelType.dknw] for _ in testers])} |"
            )

    if with_odd and has_odd:
        description.append("")
        description.append("## Неразмеченные")
        description.append("")
        description.append(f"| Задачи | {'|'.join(testers)} |")
        description.append(f"|-------| {'|'.join([':-------:' for _ in testers])} |")

        for issue in project.odd_issues:
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary(issue)
            description.append(
                f"|[#{issue.iid}]({issue.link}){summary}| {'|'.join([label_map[LabelType.dknw] for _ in testers])} |"
            )

    return description if len(description) > 1 else []


def generate_test_report(
    release: Release,
    name: str,
    testers: List[str],
    base_folder: Optional[Path] = None,
    with_open: bool = False,
    dev_only: bool = False,
    with_odd: bool = False,
    with_support: bool = False,
) -> None:
    base_folder = base_folder if base_folder else Path(os.path.abspath(os.getcwd()))

    date_str = (
        f" ({release.info.scheduled.strftime('%d.%m.%Y')})"
        if release.info.scheduled is not None
        else ""
    )

    content: List[str] = [
        f"# Тестирование релиза {release.info.name}{date_str}",
        "",
        f" * {label_map[LabelType.working]} — работает",
        f" * {label_map[LabelType.not_working]} — не работает",
        f" * {label_map[LabelType.partialy_working]} — работает частично",
    ]

    for project in release.projects:
        content.extend(
            get_project_description(
                project, testers, with_open, dev_only, with_odd, with_support
            )
        )

    rendered = "\n".join(content)

    with open(base_folder.joinpath(f"{name}.md"), "w", encoding="utf-8") as f:
        formatted = mdformat.text(rendered, extensions={"tables"})
        f.write(formatted)
