from pathlib import Path
import typer
from reporter.utils.gitlab_client import get_single_project_issues
from reporter.reports.stat_report import write_issues_with_pandas


def process_project_stat(
    client, p_id: int, project_name: str, date_from, date_to, out: Path
) -> None:
    typer.secho(f"{project_name}", fg=typer.colors.MAGENTA, bold=True)

    issues = get_single_project_issues(client, p_id, date_from, date_to)
    if issues:
        write_issues_with_pandas(issues, out)
        typer.secho(f"Обработано {len(issues)} задач", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("Задачи не найдены", fg=typer.colors.YELLOW)

    typer.echo()
