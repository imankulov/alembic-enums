import random
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional

import sqlalchemy as sa
from alembic.operations import Operations


@dataclass
class Column:
    table: str
    name: str


class EnumMigration:
    def __init__(
        self,
        op: Operations,
        enum_name: str,
        old_options: List[str],
        new_options: List[str],
        columns: Optional[List[Column]] = None,
    ):
        """Create a new EnumMigration instance.

        Args:
            op: The alembic operations object.
            old_options: The old options for the enum.
            new_options: The new options for the enum.
            enum_name: The name of the enum.
            columns: The columns that contain the enum.
        """
        self.op = op

        self.old_options = old_options
        self.new_options = new_options

        self.enum_name = enum_name
        self.temp_enum_name = f"_tmp_{enum_name}_{random.randint(0, 9999):04d}"

        self.old_type = sa.Enum(*old_options, name=self.enum_name)
        self.new_type = sa.Enum(*new_options, name=self.enum_name)

        temp_options = sorted({*old_options, *new_options})
        self.temp_type = sa.Enum(*temp_options, name=self.temp_enum_name)

        self.columns = columns or []

    def upgrade_ctx(self):
        return self._upgrade_or_downgrade_ctx(self.old_type, self.new_type)

    def upgrade(self):
        with self.upgrade_ctx():
            pass

    def downgrade_ctx(self):
        return self._upgrade_or_downgrade_ctx(self.new_type, self.old_type)

    @contextmanager
    def _upgrade_or_downgrade_ctx(self, from_: sa.Enum, to: sa.Enum):
        self.temp_type.create(self.op.get_bind(), checkfirst=False)
        self._adjust_columns_to_temp_type()

        yield

        from_.drop(self.op.get_bind(), checkfirst=False)
        to.create(self.op.get_bind(), checkfirst=False)
        self._adjust_columns_to_target_type()
        self.temp_type.drop(self.op.get_bind(), checkfirst=False)

    def downgrade(self):
        with self.downgrade_ctx():
            pass

    def update_value(self, column: Column, old_value: str, new_value: str):
        table = sa.table(column.table, sa.column(column.name))

        self.op.execute(
            table.update()
            .where(table.c[column.name] == self.op.inline_literal(old_value))
            .values({column.name: self.op.inline_literal(new_value)})
        )

    def _adjust_columns_to_temp_type(self):
        for column in self.columns:
            self._adjust_column_to_temp_type(column)

    def _adjust_column_to_temp_type(self, column: Column):
        self.op.execute(
            f"ALTER TABLE {column.table} ALTER COLUMN {column.name} "
            f"TYPE {self.temp_enum_name} "
            f" USING {column.name}::text::{self.temp_enum_name}"
        )

    def _adjust_columns_to_target_type(self):
        for column in self.columns:
            self._adjust_column_to_target_type(column)

    def _adjust_column_to_target_type(self, column: Column):
        self.op.execute(
            f"ALTER TABLE {column.table} ALTER COLUMN {column.name} "
            f"TYPE {self.enum_name} "
            f"USING {column.name}::text::{self.enum_name}"
        )
