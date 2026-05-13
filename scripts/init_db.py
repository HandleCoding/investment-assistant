from app.database.session import Base, engine


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
