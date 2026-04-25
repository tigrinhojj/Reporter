import time
from collections import OrderedDict
from pathlib import Path
from typing import List

import pandas as pd

from reporter.model.stat_models import StatIssue


def prepare_for_excel(df: pd.DataFrame, writer, sheet_name) -> None:
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    column_groups = {
        "basic": {"columns": ["Id", "Название", "Майлстоун"], "color": "#E6F3FF"},
        "created": {
            "columns": ["Дата создания", "Год создания", "Неделя создания"],
            "color": "#E6F7E6",
        },
        "closed": {
            "columns": ["Дата окончания"],
            "color": "#FFF9E6",
        },
        "approval": {
            "columns": [
                "Дата передачи на подтверждение",
                "Дата снятия с подтверждения",
            ],
            "color": "#FFE6CC",
        },
        "close_approval": {
            "columns": [
                "Дата Закрытия/Подтверждения",
                "Год Закрытия/Подтверждения",
                "Неделя Закрытия/Подтверждения",
            ],
            "color": "#FFE6F2",
        },
        "statuses": {
            "columns": [
                "Консультирование",
                "На разработке",
                "Беклог",
                "Эскалация",
                "Ждёт подтверждения",
                "Аналитика",
            ],
            "color": "#F2E6FF",
        },
        "types": {"columns": ["Статус", "Тип", "Тип2"], "color": "#F0F0F0"},
        "release": {"columns": ["Релиз", "Теги"], "color": "#E6FFFF"},
    }

    formats = {}
    for group_name, group_info in column_groups.items():
        formats[group_name] = workbook.add_format(
            {"bg_color": group_info["color"], "border": 1, "border_color": "#CCCCCC"}
        )

    for column in df:
        column_length = (
            min(30, max(df[column].astype(str).map(len).max(), len(column))) + 2
        )
        col_idx = df.columns.get_loc(column)

        worksheet.set_column(col_idx, col_idx, column_length)

        for group_name, group_info in column_groups.items():
            if column in group_info["columns"]:
                worksheet.write(0, col_idx, column, formats[group_name])
                break


def data_frame_for_issues(issues: List[StatIssue]) -> pd.DataFrame:
    issue_data: OrderedDict = OrderedDict()

    issue_data["Id"] = []
    issue_data["Название"] = []
    issue_data["Майлстоун"] = []
    issue_data["Дата создания"] = []
    issue_data["Год создания"] = []
    issue_data["Неделя создания"] = []
    issue_data["Дата окончания"] = []
    issue_data["Дата передачи на подтверждение"] = []
    issue_data["Дата снятия с подтверждения"] = []
    issue_data["Дата Закрытия/Подтверждения"] = []
    issue_data["Год Закрытия/Подтверждения"] = []
    issue_data["Неделя Закрытия/Подтверждения"] = []
    issue_data["Консультирование"] = []
    issue_data["На разработке"] = []
    issue_data["Беклог"] = []
    issue_data["Эскалация"] = []
    issue_data["Ждёт подтверждения"] = []
    issue_data["Аналитика"] = []
    issue_data["Статус"] = []
    issue_data["Тип"] = []
    issue_data["Тип2"] = []
    issue_data["Релиз"] = []
    issue_data["Теги"] = []

    for issue in issues:
        issue_data["Id"].append(issue.id)
        issue_data["Название"].append(issue.title)
        issue_data["Майлстоун"].append(issue.milestone_title)
        issue_data["Дата создания"].append(issue.created_at.date())
        issue_data["Год создания"].append(issue.created_at.year)
        issue_data["Неделя создания"].append(int(issue.created_at.strftime("%V")))
        issue_data["Дата окончания"].append(
            issue.closed_at.date() if issue.closed_at else None
        )
        issue_data["Дата передачи на подтверждение"].append(
            issue.sent_for_approval_at.date() if issue.sent_for_approval_at else None
        )
        issue_data["Дата снятия с подтверждения"].append(
            issue.removed_sent_for_approval_at.date()
            if issue.removed_sent_for_approval_at
            else None
        )

        if issue.closed_at:
            close_or_approval_date = issue.closed_at.date()
        elif issue.on_approval:
            close_or_approval_date = (
                issue.sent_for_approval_at.date()
                if issue.sent_for_approval_at
                else None
            )
        else:
            close_or_approval_date = None
        issue_data["Дата Закрытия/Подтверждения"].append(close_or_approval_date)

        issue_data["Год Закрытия/Подтверждения"].append(
            close_or_approval_date.year if close_or_approval_date else None
        )
        issue_data["Неделя Закрытия/Подтверждения"].append(
            int(close_or_approval_date.strftime("%V"))
            if close_or_approval_date
            else None
        )
        issue_data["На разработке"].append(issue.on_dev)
        issue_data["Консультирование"].append(issue.is_consulting)
        issue_data["Беклог"].append(issue.in_backlog)
        issue_data["Эскалация"].append(issue.to_dd)
        issue_data["Ждёт подтверждения"].append(issue.on_approval)
        issue_data["Аналитика"].append(issue.on_analytics)
        issue_data["Релиз"].append(issue.release)

        if issue.closed_at or issue.on_approval:
            state = "Закрыто"
        else:
            state = "Открыто"
        issue_data["Статус"].append(state)

        if issue.in_backlog:
            type1 = "Бэклог"
        elif issue.to_dd:
            type1 = "Эскалация"
        elif issue.is_consulting:
            type1 = "Консультация"
        elif issue.on_analytics:
            type1 = "Аналитика"
        elif issue.on_dev:
            type1 = "На разработке"
        else:
            type1 = "Входящие"
        issue_data["Тип"].append(type1)

        if type1 in ["Эскалация", "Бэклог"]:
            type2 = "Бэклог/эскалация"
        else:
            type2 = "ТП"
        issue_data["Тип2"].append(type2)

        issue_data["Теги"].append("|".join(issue.labels))

    df = pd.DataFrame.from_dict(issue_data)

    bool_columns = [
        "Консультирование",
        "На разработке",
        "Беклог",
        "Эскалация",
        "Ждёт подтверждения",
        "Аналитика",
    ]

    for col in bool_columns:
        df[col] = df[col].astype(int)

    return df


def write_issues_with_pandas(issues: List[StatIssue], out: Path) -> None:
    if not issues:
        return
    issue_df = data_frame_for_issues(issues)
    issue_df = issue_df.sort_values(by="Id")

    lt = time.localtime(time.time())
    filename = f"stat-{time.strftime('%Y%m%d', lt)}"

    with pd.ExcelWriter(
        out.joinpath(f"{filename}.xlsx"), engine="xlsxwriter"
    ) as writer:
        issue_df.to_excel(
            writer,
            sheet_name="Отчёт по задачам",
            index=False,
            na_rep="",
        )
        prepare_for_excel(issue_df, writer, "Отчёт по задачам")
