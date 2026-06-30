"""Destructively remove all database objects from explicitly allowed schemas."""

import argparse

from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings

ALLOWED_SCHEMAS = {"public", "production", "dev1"}
CONFIRMATION = "RESET_APP_SCHEMAS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("schemas", nargs="+", choices=sorted(ALLOWED_SCHEMAS))
    parser.add_argument("--confirm", required=True)
    return parser.parse_args()


def quote(connection, identifier: str) -> str:
    return connection.dialect.identifier_preparer.quote(identifier)


def reset_schema(connection, schema: str) -> None:
    inspector = inspect(connection)
    if schema not in inspector.get_schema_names():
        connection.execute(text(f"CREATE SCHEMA {quote(connection, schema)}"))
        print(f"{schema}: created empty schema")
        return

    schema_sql = quote(connection, schema)
    for view in inspector.get_view_names(schema=schema):
        connection.execute(
            text(f"DROP VIEW {schema_sql}.{quote(connection, view)} CASCADE")
        )
    for table in inspector.get_table_names(schema=schema):
        connection.execute(
            text(f"DROP TABLE {schema_sql}.{quote(connection, table)} CASCADE")
        )
    for sequence in inspector.get_sequence_names(schema=schema):
        connection.execute(
            text(
                f"DROP SEQUENCE IF EXISTS {schema_sql}."
                f"{quote(connection, sequence)} CASCADE"
            )
        )
    print(f"{schema}: removed all tables, views and sequences")


def main() -> None:
    args = parse_args()
    if args.confirm != CONFIRMATION:
        raise SystemExit(f"Refusing reset: pass --confirm {CONFIRMATION}")
    if len(args.schemas) != len(set(args.schemas)):
        raise SystemExit("Refusing reset: schema names must be unique")

    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            for schema in args.schemas:
                reset_schema(connection, schema)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
