import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy_utils import create_database, database_exists, drop_database

DATABASE_URL = "postgresql+psycopg2://enums:password@127.0.0.1:15432/enums"


@pytest.fixture(scope="session")
def engine():
    return sa.create_engine(url=DATABASE_URL)


@pytest.fixture(scope="session")
def op(engine):
    """Initialize the alembic op object.

    This is needed to run migrations in tests.
    """
    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    return Operations(ctx)


@pytest.fixture(scope="session", autouse=True)
def database(engine):
    if database_exists(engine.url):
        drop_database(engine.url)
    create_database(engine.url)
    yield
    drop_database(engine.url)


@pytest.fixture
def metadata():
    return sa.MetaData()


@pytest.fixture
def state_enum(op):
    enum = sa.Enum("on", "off", name="state_enum")
    enum.create(op.get_bind(), checkfirst=True)
    yield enum
    enum.drop(op.get_bind(), checkfirst=True)


@pytest.fixture
def state_enum_with_camel_case(op):
    enum = sa.Enum("onState", "offState", name="stateEnum")
    enum.create(op.get_bind(), checkfirst=True)
    yield enum
    enum.drop(op.get_bind(), checkfirst=True)
