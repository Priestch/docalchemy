from advanced_alchemy.extensions.litestar import (
    AlembicAsyncConfig,
    AlembicSyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemySyncConfig,
    SyncSessionConfig,
    async_autocommit_before_send_handler,
    sync_autocommit_before_send_handler,
)

from .base import get_settings

settings = get_settings()

alchemy = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler=async_autocommit_before_send_handler,
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)

alchemy_sync = SQLAlchemySyncConfig(
    engine_instance=settings.db.get_sync_engine(),
    before_send_handler=sync_autocommit_before_send_handler,
    session_config=SyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicSyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)
