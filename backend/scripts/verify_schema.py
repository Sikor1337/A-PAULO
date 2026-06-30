"""Compare one migrated PostgreSQL schema with SQLAlchemy metadata."""

from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings
from app.infrastructure.sql import models_registry  # noqa: F401
from app.infrastructure.sql.base import Base


def main() -> None:
    settings = get_settings()
    schema = settings.database_schema
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    inspector = inspect(engine)
    schema_sql = engine.dialect.identifier_preparer.quote(schema)

    expected_tables = {table.name for table in Base.metadata.tables.values()}
    actual_tables = set(inspector.get_table_names(schema=schema)) - {"alembic_version"}
    errors: list[str] = []
    if expected_tables != actual_tables:
        errors.append(
            f"table mismatch: missing={sorted(expected_tables - actual_tables)}, "
            f"extra={sorted(actual_tables - expected_tables)}"
        )

    for table in Base.metadata.tables.values():
        if table.name not in actual_tables:
            continue
        expected_columns = {column.name for column in table.columns}
        actual_columns = {
            column["name"]
            for column in inspector.get_columns(table.name, schema=schema)
        }
        if expected_columns != actual_columns:
            errors.append(
                f"{table.name} columns: missing="
                f"{sorted(expected_columns - actual_columns)}, "
                f"extra={sorted(actual_columns - expected_columns)}"
            )

    with engine.connect() as connection:
        versions = (
            connection.execute(
                text(f"SELECT version_num FROM {schema_sql}.alembic_version")
            )
            .scalars()
            .all()
        )

    engine.dispose()
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"{schema}: verified {len(actual_tables)} model tables, "
        f"alembic={','.join(versions)}"
    )


if __name__ == "__main__":
    main()
