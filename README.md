# Alembic Enums

![example workflow](https://github.com/imankulov/alembic-enums/actions/workflows/tests.yml/badge.svg)

**Support for migrating PostgreSQL enums with Alembic**

The package doesn't detect enum changes or generate migration code automatically, but it provides a helper class to run the enum migrations in Alembic migration scripts.

## Problem statement

When you define an enum column with SQLAlchemy, the initial migration defines a custom [enum type](https://www.postgresql.org/docs/current/datatype-enum.html).

Once the enum type is created, [ALTER TYPE](https://www.postgresql.org/docs/current/sql-altertype.html) allows you to add new values or rename existing ones, but not delete them.

If you need to delete a value from an enum, you must create a new enum type and migrate all the columns to use the new type.


## Installation

```bash
pip install alembic-enums
```


## Usage

Assume you decided to rename the `state` enum values `active` and `inactive` to `enabled` and `disabled`:

```diff
 class Resource(Base):
     __tablename__ = "resources"
     id = Column(Integer, primary_key=True)
     name = Column(String(255), nullable=False)
-    state = Column(Enum("enabled", "disabled", name="resource_state"), nullable=False)
+    state = Column(Enum("active", "archived", name="resource_state"), nullable=False)
```

To migrate the database, we create a new empty migration with `alembic revision -m "Rename enum values"` and add the following code to the generated migration script:

```python
from alembic import op

from alembic_enums import EnumMigration, Column

# Define a target column. As in PostgreSQL, the same enum can be used in multiple
# column definitions, you may have more than one target column.
# The constructor arguments are the table name, the column name, and the
# server_default values for the old and new enum types.
column = Column("resources", "state", old_server_default=None, new_server_default=None)

# Define an enum migration. It defines the old and new enum values
# for the enum, and the list of target columns.
enum_migration = EnumMigration(
    op=op,
    enum_name="resource_state",
    old_options=["enabled", "disabled"],
    new_options=["active", "archived"],
    columns=[column],
)

# Define upgrade and downgrade operations. Inside upgrade_ctx and downgrade_ctx
# context managers, you can update your data.

def upgrade():
    with enum_migration.upgrade_ctx():
        enum_migration.update_value(column, "enabled", "active")
        enum_migration.update_value(column, "disabled", "archived")


def downgrade():
    with enum_migration.downgrade_ctx():
        enum_migration.update_value(column, "active", "enabled")
        enum_migration.update_value(column, "archived", "disabled")
```

Under the hood, the `EnumMigration` class creates a new enum type, updates the target columns to use the new enum type, and deletes the old enum type.


## Change column default values


To change the column default values, pass corresponding values to new_server_default and old_server_default arguments of the Column constructor. The new_server_default is used on upgrade, and the old_server_default is used on downgrade.

IMPORTANT: Setting the server_default value to None will remove the default value from the column. If you want to keep the default value as is, set old_server_default and new_server_default to the same value.

For example, to change the default value of the `state` column from `enabled` to `active`:


```python
from alembic_enums import Column

column = Column(
    "resources",
    "state",
    old_server_default="enabled",
    new_server_default="active",
)
```

## API reference

### `EnumMigration`

A helper class to run enum migrations in Alembic migration scripts.

**Constructor arguments:**

- `op`: an instance of `alembic.operations.Operations`
- `enum_name`: the name of the enum type
- `old_options`: a list of old enum values
- `new_options`: a list of new enum values
- `columns`: a list of `Column` instances that use the enum type

**Methods:**

- `upgrade_ctx()`: a context manager that creates a new enum type, updates the target columns to use the new enum type, and deletes the old enum type
- `downgrade_ctx()`: a context manager that performs the opposite operations.
- `update_value(column, old_value, new_value)`: a helper method to update the value of the `column` to `new_value` where it was `old_value` before. It's useful to update the data in the upgrade and downgrade operations within the `upgrade_ctx` and `downgrade_ctx` context managers.
- `upgrade()`: a shorthand for `with upgrade_ctx(): pass`.
- `downgrade()`: a shorthand for `with downgrade_ctx(): pass`.

### `Column`

A data class to define a target column for an enum migration.

**Constructor arguments:**

- `table_name`: the name of the table
- `column_name`: the name of the column
- `old_server_default`: the old server_default value. When set to None, the server_default value is removed on downgrade.
- `new_server_default`: the new server_default value. When set to None, the server_default value is removed on upgrade.
