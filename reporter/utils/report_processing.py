from pathlib import Path
from typing import List
import typer
from reporter.utils.gitlab_client import get_release
from reporter.reports.release_report import generate_release_report
from reporter.reports.test_report import generate_test_report
from reporter.reports.changelog_report import generate_changelog
from reporter.model.report_models import ReportType


def process_group_report(
    client,
    g_id: int,
    group_name: str,
    release: str,
    report_type: ReportType,
    render_html: bool,
    with_open: bool,
    dev_only: bool,
    with_odd: bool,
    with_support: bool,
    tester: List[str],
    base_out: Path,
    with_changelog: bool = True,
) -> None:
    typer.secho(f"{group_name}", fg=typer.colors.MAGENTA, bold=True)

    release_data = get_release(client, release, g_id)

    if not release_data:
        typer.secho(
            f"Релиз {release} не найден в группе {group_name}",
            fg=typer.colors.YELLOW,
            bold=True,
        )
        return

    typer.secho(
        "Получена информация релиза ", fg=typer.colors.GREEN, bold=True, nl=False
    )
    typer.secho(f"{release}", fg=typer.colors.MAGENTA, bold=True)

    if report_type == ReportType.release or report_type == ReportType.all:
        releases_out = base_out / "releases"
        releases_out.mkdir(parents=True, exist_ok=True)
        generate_release_report(
            release_data,
            f"{release}-{group_name}",
            render_html=render_html,
            base_folder=releases_out,
            with_open=with_open,
            dev_only=dev_only,
            with_odd=with_odd,
            with_support=with_support,
        )
        typer.secho(
            "Сгенерирован отчёт релиза ", fg=typer.colors.GREEN, bold=True, nl=False
        )
        typer.secho(f"{release}", fg=typer.colors.MAGENTA, bold=True)

    if report_type == ReportType.test or report_type == ReportType.all:
        tests_out = base_out / "tests"
        tests_out.mkdir(parents=True, exist_ok=True)
        generate_test_report(
            release_data,
            f"{release}-test-{group_name}",
            base_folder=tests_out,
            with_open=with_open,
            testers=tester,
            dev_only=dev_only,
            with_odd=with_odd,
            with_support=with_support,
        )
        typer.secho(
            "Сгенерирован план тестирования релиза ",
            fg=typer.colors.GREEN,
            bold=True,
            nl=False,
        )
        typer.secho(f"{release}", fg=typer.colors.MAGENTA, bold=True)

    if with_changelog:
        changelog_out = base_out / "changelogs"
        changelog_out.mkdir(parents=True, exist_ok=True)
        generate_changelog(
            release_data,
            f"{release}-changelog-{group_name}",
            changelog_out,
        )
        typer.secho(
            "Сгенерирован changelog релиза ",
            fg=typer.colors.GREEN,
            bold=True,
            nl=False,
        )
        typer.secho(f"{release}", fg=typer.colors.MAGENTA, bold=True)

    typer.echo()
