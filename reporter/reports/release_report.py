import os
from pathlib import Path
from typing import List, Optional

import markdown
import mdformat

from reporter.utils.label_map import (
    get_label_summary,
    get_label_summary_html,
)
from reporter.model.report_models import Release, Project
from string import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Релиз $release_name</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; background: #1e3a8a; min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: #f59e0b; color: white; padding: 40px; text-align: center; }
        .header h1 { font-size: 2.5rem; font-weight: 300; margin-bottom: 10px; }
        .header .date { font-size: 1.2rem; opacity: 0.9; }
        .content { padding: 40px; }
        h2 { color: #1e3a8a; font-size: 1.8rem; margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid #1e3a8a; position: relative; }
        h2::after { content: ''; position: absolute; bottom: -3px; left: 0; width: 50px; height: 3px; background: #f59e0b; }
        h3 { color: #1e3a8a; font-size: 1.4rem; font-weight: bold; margin: 25px 0 15px 0; padding: 10px 15px; background: #f8f9fa; border-left: 4px solid #1e3a8a; border-radius: 0 5px 5px 0; }
        ul { list-style: none; margin: 15px 0; }
        li { padding: 12px 20px; margin: 8px 0; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #1e3a8a; transition: all 0.3s ease; position: relative; }
        li:hover { transform: translateX(5px); box-shadow: 0 5px 15px rgba(30, 58, 138, 0.2); background: #fef3c7; }
        a { color: #1e3a8a; text-decoration: none; font-weight: 500; }
        a:hover { color: #f59e0b; text-decoration: underline; }
        .issue-id { font-weight: bold; color: #1e3a8a; }
        .labels { display: inline-block; background: #f59e0b; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 500; margin-left: 8px; }
        .stats { background: linear-gradient(135deg, #1e3a8a 0%, #f59e0b 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }
        .stats h4 { margin-bottom: 10px; font-size: 1.2rem; }
        .stats .numbers { font-size: 2rem; font-weight: bold; }
        @media (max-width: 768px) { .container { margin: 10px; border-radius: 10px; } .header { padding: 20px; } .header h1 { font-size: 2rem; } .content { padding: 20px; } h2 { font-size: 1.5rem; } h3 { font-size: 1.2rem; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Релиз $release_name</h1>
            <div class="date">$release_date_str</div>
        </div>
        <div class="content">$html_content</div>
    </div>
</body>
</html>"""


def get_project_description(
    project: Project,
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
        description.append("### Закрытые")

        for issue in project.issues:
            if not issue.closed:
                continue
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    if with_open and has_open:
        description.append("")
        description.append("### Открытые")

        for issue in project.issues:
            if issue.closed:
                continue
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    if with_odd and has_odd:
        description.append("")
        description.append("### Неразмеченные")

        for issue in project.odd_issues:
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    return description if len(description) > 1 else []


def get_project_description_html(
    project: Project,
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
        description.append("### Закрытые")

        for issue in project.issues:
            if not issue.closed:
                continue
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary_html(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    if with_open and has_open:
        description.append("")
        description.append("### Открытые")

        for issue in project.issues:
            if issue.closed:
                continue
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary_html(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    if with_odd and has_odd:
        description.append("")
        description.append("### Неразмеченные")

        for issue in project.odd_issues:
            if dev_only and issue.no_dev:
                continue
            summary = get_label_summary_html(issue)
            description.append(
                f" * [#{issue.iid}]({issue.link}){summary} {issue.title}"
            )

    return description if len(description) > 1 else []


def generate_release_report(
    release: Release,
    name: str,
    base_folder: Optional[Path] = None,
    render_html: bool = False,
    with_open: bool = False,
    dev_only: bool = False,
    with_odd: bool = False,
    with_support: bool = False,
) -> None:
    base_folder = base_folder if base_folder else Path(os.path.abspath(os.getcwd()))
    release_date_str = (
        f" ({release.info.scheduled.strftime('%d.%m.%Y')})"
        if release.info.scheduled is not None
        else ""
    )
    content: List[str] = []

    for project in release.projects:
        content.extend(
            get_project_description(
                project,
                with_open=with_open,
                dev_only=dev_only,
                with_odd=with_odd,
                with_support=with_support,
            )
        )

    rendered = "\n".join(content)

    with open(base_folder.joinpath(f"{name}.md"), "w", encoding="utf-8") as f:
        formatted = mdformat.text(rendered, extensions={"tables"})
        f.write(formatted)

    if render_html:
        html_content_list: List[str] = []
        for project in release.projects:
            html_content_list.extend(
                get_project_description_html(
                    project,
                    with_open=with_open,
                    dev_only=dev_only,
                    with_odd=with_odd,
                    with_support=with_support,
                )
            )

        html_rendered = "\n".join(html_content_list)
        html_content = markdown.markdown(
            html_rendered, extensions=["tables"], output_format="html5"
        )

        with open(base_folder.joinpath(f"{name}.html"), "w", encoding="utf-8") as f:
            f.write(
                Template(HTML_TEMPLATE).substitute(
                    release_name=release.info.name,
                    release_date_str=release_date_str,
                    html_content=html_content,
                )
            )
