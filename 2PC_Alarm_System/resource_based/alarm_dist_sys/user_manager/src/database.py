import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/users.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
    pool_pre_ping=True
)

# https://www.sqlite.org/pragma.html
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")     # Concurrent reads during writes
    cursor.execute("PRAGMA synchronous=NORMAL;")   # Best for high concurrency situations
    cursor.execute("PRAGMA cache_size=10000;")     # Cache for 10000 pages (page size default is 4KB)
    cursor.execute("PRAGMA temp_store=MEMORY;")    # Avoid disk temp files
    cursor.execute("PRAGMA locking_mode=NORMAL;")  # Avoid exclusive locks
    cursor.execute("PRAGMA busy_timeout=5000;")    # Wait 5s if DB is locked
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
