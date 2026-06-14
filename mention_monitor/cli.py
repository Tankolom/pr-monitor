import argparse
import time

from .collector import collect_once
from .config import load_config
from .db import backup_database, connect, due_projects, mark_project_collected, run_startup_migration
from .webapp import run_server


def main():
    parser = argparse.ArgumentParser(description="Mention Monitor MVP")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Run one collection cycle")
    collect.add_argument("--no-fetch-pages", action="store_true", help="Save search snippets without opening result pages")
    collect.add_argument("--source", action="append", dest="sources", help="Limit collection to a source type, for example serper_google")
    collect.add_argument("--period", default="30d", choices=["1d", "3d", "7d", "14d", "30d", "60d", "90d"], help="News slice period")
    collect.add_argument("--depth", default="standard", choices=["fast", "standard", "deep"], help="News slice depth")
    collect.add_argument("--project", default=None, help="Limit collection to project name")

    watch = sub.add_parser("watch", help="Run collection forever by interval")
    watch.add_argument("--minutes", type=int, default=30)
    watch.add_argument("--no-fetch-pages", action="store_true", help="Save search snippets without opening result pages")
    watch.add_argument("--source", action="append", dest="sources", help="Limit collection to a source type, for example yandex_search")
    watch.add_argument("--period", default="30d", choices=["1d", "3d", "7d", "14d", "30d", "60d", "90d"], help="News slice period")
    watch.add_argument("--depth", default="standard", choices=["fast", "standard", "deep"], help="News slice depth")
    watch.add_argument("--project", default=None, help="Limit collection to project name")

    server = sub.add_parser("server", help="Start local web dashboard")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8765)

    backup = sub.add_parser("backup", help="Create SQLite backup with rotation")
    backup.add_argument("--dir", default=None, help="Backup directory. Default: data/backups")
    backup.add_argument("--keep", type=int, default=14, help="How many recent backups to keep")

    args = parser.parse_args()

    # Однократная миграция к мультитенанту (проекты config.json -> БД).
    if args.command in {"collect", "watch", "server"}:
        run_startup_migration(args.config)

    if args.command == "collect":
        print(collect_once(args.config, fetch_pages=not args.no_fetch_pages, source_types=args.sources, period=args.period, depth=args.depth, project_name=args.project))
    elif args.command == "watch":
        # Планировщик: периодически просыпается и собирает только те проекты,
        # у которых включён автосбор и истёк их индивидуальный интервал (3–48 ч).
        # Частота опроса (--minutes) — как часто проверять; сам интервал задаётся на проекте.
        poll_seconds = max(int(args.minutes), 1) * 60
        while True:
            config = load_config(args.config)
            conn = connect(config["database"])
            try:
                due = due_projects(conn)
            finally:
                conn.close()
            if args.project and args.project != "all":
                due = [p for p in due if p.get("name") == args.project]
            for project in due:
                result = collect_once(
                    args.config, fetch_pages=not args.no_fetch_pages, source_types=args.sources,
                    period=args.period, depth=args.depth, project_name=project["name"],
                )
                mark_conn = connect(config["database"])
                try:
                    mark_project_collected(mark_conn, project["id"])
                finally:
                    mark_conn.close()
                print({"project": project["name"], "interval_h": project.get("schedule_interval_hours"), "result": result})
            if not due:
                print({"status": "idle", "reason": "нет проектов к сбору"})
            time.sleep(poll_seconds)
    elif args.command == "server":
        run_server(args.host, args.port, args.config)
    elif args.command == "backup":
        config = load_config(args.config)
        backup_dir = args.dir or config.get("backup_dir", "data/backups")
        print(backup_database(config["database"], backup_dir, keep=args.keep))
