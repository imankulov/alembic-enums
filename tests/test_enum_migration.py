import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DataError

from alembic_enums import Column, EnumMigration


@pytest.fixture
def resources_table(op, metadata, state_enum):
    table = sa.Table(
        "resources",
        metadata,
        sa.Column("state", state_enum, nullable=False),
    )
    table.create(op.get_bind(), checkfirst=True)
    yield table
    table.drop(op.get_bind(), checkfirst=True)


@pytest.fixture
def resources_table_with_camel_case(op, metadata, state_enum_with_camel_case):
    table = sa.Table(
        "resourcesWithCamelCase",
        metadata,
        sa.Column("stateColumn", state_enum_with_camel_case, nullable=False),
    )
    table.create(op.get_bind(), checkfirst=True)
    yield table
    table.drop(op.get_bind(), checkfirst=True)


def test_upgrade_should_extend_options(op, resources_table):
    with pytest.raises(DataError):
        op.bulk_insert(resources_table, [{"state": "unknown"}])
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["on", "off", "unknown"],
        columns=[
            Column(
                "resources", "state", old_server_default=None, new_server_default=None
            )
        ],
    )
    migration.upgrade()
    op.bulk_insert(
        resources_table, [{"state": "on"}, {"state": "off"}, {"state": "unknown"}]
    )


def test_upgrade_should_replace_options(op, resources_table):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources", "state", old_server_default=None, new_server_default=None
            )
        ],
    )
    migration.upgrade()
    op.bulk_insert(resources_table, [{"state": "enabled"}, {"state": "disabled"}])


def test_downgrade_should_roll_back_changes(op, resources_table):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources", "state", old_server_default=None, new_server_default=None
            )
        ],
    )
    migration.upgrade()
    migration.downgrade()
    op.bulk_insert(resources_table, [{"state": "on"}, {"state": "off"}])


def test_upgrade_context_should_allow_update_values(op, resources_table):
    op.bulk_insert(resources_table, [{"state": "on"}, {"state": "off"}])
    column = Column(
        "resources", "state", old_server_default=None, new_server_default=None
    )
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[column],
    )
    with migration.upgrade_ctx():
        migration.update_value(column, "on", "enabled")
        migration.update_value(column, "off", "disabled")
    op.bulk_insert(resources_table, [{"state": "enabled"}, {"state": "disabled"}])


def test_downgrade_context_should_allow_update_values(op, resources_table):
    column = Column(
        "resources", "state", old_server_default=None, new_server_default=None
    )
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[column],
    )
    migration.upgrade()
    op.bulk_insert(resources_table, [{"state": "enabled"}, {"state": "disabled"}])
    with migration.downgrade_ctx():
        migration.update_value(column, "enabled", "on")
        migration.update_value(column, "disabled", "off")
    op.bulk_insert(resources_table, [{"state": "on"}, {"state": "off"}])


def test_upgrade_with_capital_letters_extends_options(op, resources_table_with_camel_case):
    with pytest.raises(DataError):
        op.bulk_insert(resources_table_with_camel_case, [{"stateColumn": "unknown"}])
    migration = EnumMigration(
        op=op,
        enum_name="stateEnum",
        old_options=["onState", "offState"],
        new_options=["onState", "offState", "unknown"],
        columns=[
            Column(
                "resourcesWithCamelCase", "stateColumn", old_server_default=None, new_server_default=None
            )
        ],
    )
    migration.upgrade()
    op.bulk_insert(
        resources_table_with_camel_case, [
            {"stateColumn": "onState"},
            {"stateColumn": "offState"},
            {"stateColumn": "unknown"}
        ]
    )

