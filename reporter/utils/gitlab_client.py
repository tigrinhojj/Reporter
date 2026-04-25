from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
import gitlab
import typer
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import track
from dateutil import parser
from gitlab.v4.objects import Group, GroupLabel, Project as GitlabProject

from reporter.consts import (
    RELEASE_INTERVAL_IN_DAYS,
    APPROVAL_LABEL,
    BACKLOG_LABELS,
    DEV_LABEL,
    RELEASE_INDICATOR,
    CONSULTATION_LABEL,
    EXTERNAL_LABEL,
    ANALYTICS_LABEL,
)
from reporter.model.report_models import (
    ReleaseSchedule,
    is_release_label,
    ReleaseIssue,
    Release,
    Project,
)
from reporter.model.stat_models import StatIssue


def make_gitlab_client() -> gitlab.Gitlab:
    url = os.getenv("GITLAB_URL") or "https://gitlab.com"
    token = os.getenv("GITLAB_API_TOKEN")
    if not token:
        typer.secho(
            "Ошибка: не найден GITLAB_API_TOKEN", fg=typer.colors.RED, bold=True
        )
        typer.secho(
            "Установите токен: reporter config --token glpat-новый_токен",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        raise typer.Exit(1)
    client = gitlab.Gitlab(url, private_token=token, per_page=100)
    validate_gitlab_token(client)
    typer.secho(
        "Установлено соединение с GitLab ", fg=typer.colors.GREEN, bold=True, nl=False
    )
    typer.secho(f"{url}", fg=typer.colors.MAGENTA, bold=True)
    typer.echo()
    return client


def validate_gitlab_token(client: gitlab.Gitlab) -> None:
    try:
        client.auth()
    except gitlab.exceptions.GitlabAuthenticationError:
        typer.secho(
            "Ошибка: токен GitLab недействителен или истек",
            fg=typer.colors.RED,
            bold=True,
        )
        typer.secho(
            "Обновите токен: reporter config --token glpat-новый_токен",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Ошибка подключения к GitLab: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(1)


def get_all_groups(client: gitlab.Gitlab) -> List[Dict[str, Any]]:
    groups = client.groups.list(get_all=True, iterator=True)

    group_list = []
    for group in groups:
        group_info = {
            "id": group.id,
            "name": group.name,
            "path": group.path,
            "full_path": group.full_path,
            "description": getattr(group, "description", ""),
            "web_url": group.web_url,
        }
        group_list.append(group_info)

    return sorted(group_list, key=lambda x: x["id"])


def get_group_projects(client: gitlab.Gitlab, group_id: int) -> List[Dict[str, Any]]:
    try:
        group = client.groups.get(group_id, lazy=True)
        projects = group.projects.list(include_subgroups=True, iterator=True)

        project_list = []
        for project in projects:
            project_info = {
                "id": project.id,
                "name": project.name,
            }
            project_list.append(project_info)

        return sorted(project_list, key=lambda x: x["id"])
    except Exception:
        return []


def get_release_infos(
    client: gitlab.Gitlab, group_id: int
) -> Dict[str, ReleaseSchedule]:
    release_infos: Dict[str, ReleaseSchedule] = {}

    group: Group = client.groups.get(group_id, lazy=True)
    labels: List[GroupLabel] = group.labels.list(get_all=True)

    for label in labels:
        if not is_release_label(label.name):
            continue

        release_info: Optional[ReleaseSchedule] = ReleaseSchedule.from_string(
            label.name
        )

        if not release_info or release_info.name in release_infos.keys():
            continue

        release_infos[release_info.name] = release_info

    return release_infos


def get_release_info(
    client: gitlab.Gitlab, ver: str, group_id: int
) -> Optional[ReleaseSchedule]:
    release_infos = get_release_infos(client, group_id)
    if ver in release_infos:
        return release_infos[ver]
    return None


def _process_single_project(
    client: gitlab.Gitlab, project_info, release_info: ReleaseSchedule
) -> Optional["Project"]:
    project = client.projects.get(project_info.id, lazy=True)

    def get_release_issues():
        issues = []
        for issue in project.issues.list(
            labels=[release_info.raw], get_all=True, iterator=True
        ):
            issues.append(
                ReleaseIssue(
                    id=issue.id,
                    iid=issue.iid,
                    title=issue.title,
                    link=issue.web_url,
                    labels=issue.labels,
                    closed=not (issue.state == "opened" or issue.state == "active"),
                    merge_requests_count=issue.merge_requests_count,
                )
            )
        return issues

    def get_odd_issues():
        if release_info.scheduled is None:
            return []

        start_date = release_info.scheduled - timedelta(days=RELEASE_INTERVAL_IN_DAYS)
        issues = []

        for issue in project.issues.list(
            state="closed",
            order_by="updated_at",
            sort="desc",
            get_all=True,
            iterator=True,
        ):
            update_date = datetime.strptime(
                issue.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).date()

            if update_date < start_date:
                break

            if any((is_release_label(lb) for lb in issue.labels)):
                continue

            issues.append(
                ReleaseIssue(
                    id=issue.id,
                    iid=issue.iid,
                    title=issue.title,
                    link=issue.web_url,
                    labels=issue.labels,
                    closed=not (issue.state == "opened" or issue.state == "active"),
                    merge_requests_count=issue.merge_requests_count,
                )
            )
        return issues

    with ThreadPoolExecutor(max_workers=2) as executor:
        release_future = executor.submit(get_release_issues)
        odd_future = executor.submit(get_odd_issues)

        release_issues = release_future.result()
        odd_issues = odd_future.result()

    release_project = Project(
        name=project_info.name,
        issues=release_issues,
        release_info=release_info,
        odd_issues=odd_issues,
        link=project_info.web_url,
    )

    return release_project if release_project.has_release_related_changes else None


def get_release(
    client: gitlab.Gitlab, version: str, group_id: int, max_workers: int = 10
) -> Optional[Release]:
    release_info = get_release_info(client, version, group_id)
    if not release_info:
        return None

    group = client.groups.get(group_id, lazy=True)

    projects_list = list(group.projects.list(include_subgroups=True, get_all=True))

    if not projects_list:
        return Release(projects=[], info=release_info)

    actual_workers = min(max_workers, len(projects_list))

    release_projects = []

    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        future_to_project = {
            executor.submit(
                _process_single_project, client, project, release_info
            ): project
            for project in projects_list
        }

        for future in track(
            as_completed(future_to_project), total=len(future_to_project)
        ):
            project = future_to_project[future]

            try:
                result = future.result()
                if result:
                    release_projects.append(result)

            except Exception as e:
                typer.secho(
                    f"Ошибка обработки проекта {project.name}: {e}",
                    fg=typer.colors.YELLOW,
                    bold=True,
                )
                continue

    return Release(projects=release_projects, info=release_info)


def validate_project_ids(
    client: gitlab.Gitlab,
    project_ids: Iterable[int],
) -> tuple[List[int], List[int]]:
    valid_projects = []
    invalid_projects = []

    for p_id in project_ids:
        try:
            client.projects.get(p_id, lazy=True)
            valid_projects.append(p_id)
        except Exception:
            invalid_projects.append(p_id)

    return valid_projects, invalid_projects


def validate_group_ids(
    client: gitlab.Gitlab,
    group_ids: Iterable[int],
) -> tuple[List[int], List[int]]:
    valid_groups = []
    invalid_groups = []

    for g_id in group_ids:
        try:
            client.groups.get(g_id, lazy=True)
            valid_groups.append(g_id)
        except Exception:
            invalid_groups.append(g_id)

    return valid_groups, invalid_groups


def gitlab_to_issues(gitlab_issue) -> StatIssue:
    sent_for_approval_at: Optional[datetime] = None
    removed_sent_for_approval_at: Optional[datetime] = None
    release: Optional[str] = None
    labels = [
        label for label in (gitlab_issue.labels or []) if RELEASE_INDICATOR not in label
    ]

    for label_event in gitlab_issue.resourcelabelevents.list(get_all=True):
        if label_event.label["name"] == APPROVAL_LABEL and label_event.action == "add":
            sent_for_approval_at = label_event.created_at

        if (
            label_event.label["name"] == APPROVAL_LABEL
            and label_event.action == "remove"
        ):
            removed_sent_for_approval_at = label_event.created_at

        if RELEASE_INDICATOR in label_event.label["name"]:
            release = label_event.label["name"]

    return StatIssue(
        id=gitlab_issue.iid,
        title=gitlab_issue.title,
        labels=labels,
        created_at=parser.parse(gitlab_issue.created_at),
        closed_at=parser.parse(gitlab_issue.closed_at)
        if gitlab_issue.closed_at
        else None,
        sent_for_approval_at=parser.parse(sent_for_approval_at)
        if sent_for_approval_at
        else None,
        removed_sent_for_approval_at=parser.parse(removed_sent_for_approval_at)
        if removed_sent_for_approval_at
        else None,
        milestone_title=gitlab_issue.milestone["title"]
        if gitlab_issue.milestone
        else None,
        is_consulting=CONSULTATION_LABEL in gitlab_issue.labels
        if gitlab_issue.labels
        else False,
        in_backlog=any(bl in gitlab_issue.labels for bl in BACKLOG_LABELS)
        if gitlab_issue.labels
        else False,
        to_dd=EXTERNAL_LABEL in gitlab_issue.labels if gitlab_issue.labels else False,
        on_approval=APPROVAL_LABEL in gitlab_issue.labels
        if gitlab_issue.labels
        else False,
        on_analytics=ANALYTICS_LABEL in gitlab_issue.labels
        if gitlab_issue.labels
        else False,
        on_dev=DEV_LABEL in gitlab_issue.labels if gitlab_issue.labels else False,
        release=release,
    )


def get_single_project_issues(
    client: gitlab.Gitlab,
    project_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    max_workers: int = 10,
) -> List[StatIssue]:
    project: GitlabProject = client.projects.get(project_id, lazy=True)

    gitlab_issues = list(
        project.issues.list(
            get_all=True,
            created_before=date_to,
            created_after=date_from,
        )
    )

    if not gitlab_issues:
        return []

    issues = []
    batch_size = max(1, len(gitlab_issues) // max_workers)

    def process_batch(batch):
        return [gitlab_to_issues(issue) for issue in batch]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        batches = [
            gitlab_issues[i : i + batch_size]
            for i in range(0, len(gitlab_issues), batch_size)
        ]

        futures = [executor.submit(process_batch, batch) for batch in batches]

        for future in track(as_completed(futures), total=len(futures)):
            issues.extend(future.result())

    return issues
