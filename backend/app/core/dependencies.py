from sqlalchemy import Engine

from app.core.config import get_settings
from app.infrastructure.sql.factory import SQLConnectionFactory
from app.infrastructure.storage.attachments import AttachmentStorage
from app.infrastructure.storage.factory import AttachmentStorageFactory

# =============================================================================
# Factory Instances (Singletons)
# =============================================================================

sql_factory = SQLConnectionFactory()
attachment_storage_factory = AttachmentStorageFactory()

# =============================================================================
# SQL Database Setup
# =============================================================================


def _create_sql_engine() -> Engine:
    """Create a new SQLAlchemy engine based on current settings."""
    settings = get_settings()
    return sql_factory.get_or_create_engine(
        settings.database_url, settings.database_schema
    )


# Initialize SQL engine and session factory
_sql_engine = _create_sql_engine()
_sql_session_factory = sql_factory.create_session_factory(_sql_engine)

# FastAPI dependency for SQL sessions
get_sql_session = sql_factory.get_session_dependency(_sql_session_factory)
get_db = get_sql_session

# =============================================================================
# Attachment Storage Setup
# =============================================================================


def get_attachment_storage() -> AttachmentStorage:
    """Return the configured attachment storage backend."""
    settings = get_settings()
    return attachment_storage_factory.get_or_create_local_storage(
        settings.attachment_storage_path
    )
