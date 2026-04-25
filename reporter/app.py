import datetime
import os
from pathlib import Path
from typing import Optional, List
import pyfiglet
import timeago
import typer
from dotenv import load_dotenv
from reporter.model.report_models import ReportType
from reporter.utils.gitlab_client import (
    get_all_groups,
    get_group_projects,
    get_release_infos,
    validate_project_ids,
    validate_group_ids,
    make_gitlab_client,
)
from reporter.utils.stat_processing import process_project_stat
from reporter.utils.report_processing import process_group_report


app = typer.Typer(add_completion=False)

load_dotenv()
token_file = Path.home() / ".reporter_token"
if token_file.exists():
    with open(token_file, "r") as f:
        token_from_file = f.read().strip()
        if token_from_file:
            os.environ["GITLAB_API_TOKEN"] = token_from_file


@app.command()
def releases(
    group_id: List[int] = typer.Option(
        default=[1],
        help="ID групп для получения информации о релизах",
    ),
    all: bool = typer.Option(
        False,
        help="Выводить все релизы",
    ),
) -> None:
    """
    Информация о релизах [--group-id=1] [--all=False]
    """

    client = make_gitlab_client()

    (
        valid_groups,
        invalid_groups,
    ) = validate_group_ids(client, group_id)

    for i_g in invalid_groups:
        typer.secho(
            f"Предупреждение: Не удаётся найти группу с id {i_g}",
            fg=typer.colors.YELLOW,
            bold=True,
        )

    now = datetime.datetime.now().date()

    for g_id in valid_groups:
        group = client.groups.get(g_id)
        typer.secho(f"{group.name}", fg=typer.colors.MAGENTA, bold=True)

        rel_info = get_release_infos(client, g_id)

        if not rel_info:
            typer.secho("Релизы не найдены", fg=typer.colors.RED, bold=True)
            continue

        releases_list = list(rel_info.values())
        releases_list.sort(key=lambda x: (x.scheduled is None, x.scheduled))

        if not all:
            releases_list = releases_list[-20:]

        upcoming_release = None
        min_future_days = float("inf")

        for release_info in releases_list:
            if release_info.scheduled and release_info.scheduled > now:
                days_until = (release_info.scheduled - now).days
                if days_until < min_future_days:
                    min_future_days = days_until
                    upcoming_release = release_info.name

        for release_info in releases_list:
            scheduled = release_info.scheduled
            sch_str = f" {scheduled.strftime('%d.%m.%Y')} " if scheduled else ""
            ago_str = (
                f"({timeago.format(scheduled, datetime.datetime.now())})"
                if scheduled
                else ""
            )

            release_name = typer.style(release_info.name, fg=typer.colors.MAGENTA)
            upcoming_text = ""
            if release_info.name == upcoming_release:
                upcoming_text = " " + typer.style("upcoming", fg=typer.colors.RED)

            typer.echo(f"{release_name} →{sch_str}{ago_str}{upcoming_text}")

        typer.echo()


@app.command()
def report(
    release: str = typer.Option(
        ...,
        prompt=True,
        help="Номер версии для которой требуется составить отчёт",
    ),
    group_id: List[int] = typer.Option(
        default=[1],
        help="ID групп для подготовки отчёта",
    ),
    tester: Optional[List[str]] = typer.Option(
        None,
        help="Имена специалистов, отвечающих за тестирование релиза",
    ),
    render_html: bool = typer.Option(
        False,
        help="Создавать HTML версию отчёта",
    ),
    with_open: bool = typer.Option(
        False,
        help="Отображать информацию по открытым задачам",
    ),
    dev_only: bool = typer.Option(
        False,
        help="Отображать информацию по задачам со связанными MR",
    ),
    with_odd: bool = typer.Option(
        False,
        help="Отображать информацию по неразмеченным задачам",
    ),
    with_support: bool = typer.Option(
        False,
        help="Отображать информацию по задачам поддержки",
    ),
    report_type: ReportType = typer.Option(
        default=ReportType.all,
        help="Тип генерируемого отчёта",
    ),
    with_changelog: bool = typer.Option(
        True,
        help="Создавать changelog файл",
    ),
) -> None:
    """
    Создание отчёта по релизу [--release*] [--group-id=1] [--tester=None] [--render-html=False] [--with-open=False] [--with-odd=False] [--with-support=False] [--dev-only=False] [--report-type=all] [--with-changelog=True]
    """
    if (report_type in (ReportType.all, ReportType.test)) and not tester:
        typer.secho(
            "Ошибка: При генерации отчётов all или test необходимо указать хотя бы одного специалиста по тестированию при помощи флага --tester",
            fg=typer.colors.RED,
            bold=True,
        )
        raise typer.Exit(1)

    client = make_gitlab_client()

    (
        valid_groups,
        invalid_groups,
    ) = validate_group_ids(client, group_id)

    for i_g in invalid_groups:
        typer.secho(
            f"Предупреждение: Не удаётся найти группу с id {i_g}",
            fg=typer.colors.YELLOW,
            bold=True,
        )

    out = Path.cwd() / "reporter_results"
    out.mkdir(parents=True, exist_ok=True)

    for g_id in valid_groups:
        group = client.groups.get(g_id)

        process_group_report(
            client,
            g_id,
            group.name,
            release,
            report_type,
            render_html,
            with_open,
            dev_only,
            with_odd,
            with_support,
            tester,
            out,
            with_changelog,
        )
    typer.secho(f"Сохранено в {out}", fg=typer.colors.GREEN, bold=True)


@app.command()
def groups() -> None:
    """
    Информация о доступных группах
    """

    client = make_gitlab_client()
    try:
        all_groups = get_all_groups(client)
        typer.secho(
            f"Найдено {len(all_groups)} групп:", fg=typer.colors.GREEN, bold=True
        )

        for group in all_groups:
            typer.echo(f"- ID: {group['id']} | {group['name']}")

    except Exception as e:
        typer.secho(f"Ошибка при получении групп: {e}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(1)


@app.command()
def projects(
    group_id: List[int] = typer.Option(
        default=[1],
        help="ID групп для получения проектов",
    ),
) -> None:
    """
    Информация о проектах в группах [--group-id=1]
    """

    client = make_gitlab_client()

    (
        valid_groups,
        invalid_groups,
    ) = validate_group_ids(client, group_id)

    for i_g in invalid_groups:
        typer.secho(
            f"Предупреждение: Не удаётся найти группу с id {i_g}",
            fg=typer.colors.YELLOW,
            bold=True,
        )

    for g_id in valid_groups:
        group = client.groups.get(g_id)
        typer.secho(f"{group.name}", fg=typer.colors.MAGENTA, bold=True)

        projects_list = get_group_projects(client, g_id)
        if not projects_list:
            typer.secho("Проекты не найдены", fg=typer.colors.YELLOW, bold=True)
            continue

        for project in projects_list:
            typer.echo(f"- ID: {project['id']} | {project['name']}")


@app.command()
def config(
    token: str = typer.Option(
        None,
        "--token",
        help="Установить новый GitLab API токен",
    ),
) -> None:
    """
    Управление токеном GitLab [--token]
    """
    token_file = Path.home() / ".reporter_token"

    if token:
        token_file.write_text(token)
        try:
            os.chmod(token_file, 0o600)
        except Exception:
            pass
        typer.secho("Токен обновлен!", fg=typer.colors.GREEN, bold=True)
        return

    if token_file.exists():
        current_token = token_file.read_text().strip()
        masked_token = current_token[:12] + "..." if len(current_token) > 12 else "***"
        typer.secho(f"Токен настроен: {masked_token}", fg=typer.colors.GREEN, bold=True)
        typer.secho(f"Файл: {token_file}", fg=typer.colors.GREEN, bold=True)
        typer.secho(
            "Обновить: reporter config --token glpat-новый_токен",
            fg=typer.colors.YELLOW,
            bold=True,
        )
    else:
        typer.secho("Токен не настроен", fg=typer.colors.RED, bold=True)
        typer.secho(
            "Установить: reporter config --token glpat-ваш_токен",
            fg=typer.colors.YELLOW,
            bold=True,
        )


@app.command()
def stat(
    project_id: List[int] = typer.Option(
        default=[1],
        help="ID проектов для получения статистики",
    ),
    date_from: Optional[datetime.datetime] = typer.Option(
        datetime.datetime(2022, 1, 1), help="Левая граница даты для фильтрации"
    ),
    date_to: Optional[datetime.datetime] = typer.Option(
        None, help="Правая граница даты для фильтрации"
    ),
) -> None:
    """
    Статистика по задачам [--group-id=None] [--project-id=1] [--date-from=2022-01-01] [--date-to=None]
    """

    client = make_gitlab_client()

    (
        valid_projects,
        invalid_projects,
    ) = validate_project_ids(client, project_id)

    for i_p in invalid_projects:
        typer.secho(
            f"Предупреждение: Не удаётся найти проект с id {i_p}",
            fg=typer.colors.YELLOW,
            bold=True,
        )

    out = Path.cwd() / "reporter_results" / "statistics"
    out.mkdir(parents=True, exist_ok=True)

    for p_id in valid_projects:
        project = client.projects.get(p_id)
        process_project_stat(client, p_id, project.name, date_from, date_to, out)

    typer.secho(f"Сохранено в {out}", fg=typer.colors.GREEN, bold=True)


def start() -> None:
    typer.echo(pyfiglet.Figlet(font="slant").renderText("REPORTER"))
    app()


if __name__ == "__main__":
    start()
