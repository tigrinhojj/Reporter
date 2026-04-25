from pathlib import Path
from datetime import datetime
from reporter.model.report_models import Release


def generate_changelog(
    release_data: Release,
    filename: str,
    base_folder: Path,
) -> None:
    changelog_content = []

    release_name = release_data.info.name
    release_date = release_data.info.scheduled
    date_str = (
        release_date.strftime("%d.%m.%Y")
        if release_date
        else datetime.now().strftime("%d.%m.%Y")
    )

    changelog_content.append(f"## [{release_name}] - {date_str}")

    for project in release_data.projects:
        if project.name == "iskra-support":
            continue

        for issue in project.issues:
            if not issue.closed or issue.odd:
                continue

            issue_text = f"- [#{issue.iid}]({issue.link}) {issue.title}"

            changelog_content.append(issue_text)

    output_file = base_folder / f"{filename}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(changelog_content))
