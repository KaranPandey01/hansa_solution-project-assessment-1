from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Connection to the EXISTING SQL Server database (Windows Trusted Connection)
DATABASE_URL = (
    "mssql+pyodbc://@localhost/StudentAdmissionDB"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Trusted_Connection=yes"
    "&TrustServerCertificate=yes"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Give each request its own database session and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()