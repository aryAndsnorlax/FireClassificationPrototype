"""Database initialization script to create tables in PostGIS."""
from api.db.models import Base
from api.db.session import engine


def init_db():
    """Create all tables registered with SQLAlchemy Base metadata."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
