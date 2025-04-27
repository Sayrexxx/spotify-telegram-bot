from src.database.db_setup import engine, Base


def setup_database():
    """Creates all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()
