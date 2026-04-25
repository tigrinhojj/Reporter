# Reporter

CLI для отчётов по релизам/статистике GitLab.

## Установка
- Требуется Python 3.11 - 3.13
- Установка: `poetry install`

## Установка из колеса
- Локальный файл (из каталога с `.whl`):
  ```bash
  pip install reporter-<версия>-py3-none-any.whl
  ```
- После установки:
  ```bash
  reporter --help
  ```

## Настройка
- Токен: `reporter config --token glpat-XXXX`
- Переменные окружения:
  - `GITLAB_URL` — адрес GitLab (по умолчанию в коде: публичный `https://gitlab.com`, для своего инстанса задайте явно).
  - `GITLAB_API_TOKEN` — токен GitLab.
- Пример `.env` см. `.env.example`

## Использование
- Список групп: `poetry run reporter groups --help`
- Проекты группы: `poetry run reporter projects --help`
- Релизы: `poetry run reporter releases --help`
- Отчёт по релизу: `poetry run reporter report --help`
- Статистика задач: `poetry run reporter stat --help`

Вывод сохраняется в `reporter_results/`
