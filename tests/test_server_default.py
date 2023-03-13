import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from alembic_enums import Change, Column, EnumMigration


@pytest.fixture
def resources_table_with_server_default(op, metadata, state_enum):
    table = sa.Table(
        "resources",
        metadata,
        sa.Column("state", state_enum, nullable=False, server_default="on"),
    )
    table.create(op.get_bind(), checkfirst=True)
    yield table
    table.drop(op.get_bind(), checkfirst=True)


def test_upgrade_should_update_server_default(op, resources_table_with_server_default):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources",
                "state",
                server_default=Change(old="on", new="enabled"),
            )
        ],
    )
    migration.upgrade()
    op.bulk_insert(resources_table_with_server_default, [{}])


def test_downgrade_should_roll_back_server_default_changes(
    op, resources_table_with_server_default
):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources",
                "state",
                server_default=Change(old="on", new="enabled"),
            )
        ],
    )
    migration.upgrade()
    migration.downgrade()
    op.bulk_insert(resources_table_with_server_default, [{}])


def test_upgrade_should_drop_server_default(op, resources_table_with_server_default):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources",
                "state",
                server_default=Change(old="on", new=None),
            )
        ],
    )
    migration.upgrade()
    with pytest.raises(IntegrityError):
        op.bulk_insert(resources_table_with_server_default, [{}])


def test_downgrade_should_roll_back_server_default_drop(
    op, resources_table_with_server_default
):
    migration = EnumMigration(
        op=op,
        enum_name="state_enum",
        old_options=["on", "off"],
        new_options=["enabled", "disabled"],
        columns=[
            Column(
                "resources",
                "state",
                server_default=Change(old="on", new=None),
            )
        ],
    )
    migration.upgrade()
    migration.downgrade()
    op.bulk_insert(resources_table_with_server_default, [{}])
