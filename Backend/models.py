from sqlalchemy import Column, Integer, String, Float, Date
from database import Base


class Student(Base):
    """Maps to the SQL Server table 'Students'."""
    __tablename__ = "Students"

    # StudentID is an IDENTITY column: SQL Server generates it atomically on
    # INSERT, so the backend never assigns it (see create_student in main.py).
    StudentID = Column(Integer, primary_key=True, autoincrement=True)
    FullName = Column(String)
    DOB = Column(Date)
    Gender = Column(String)
    Email = Column(String)
    Phone = Column(String)
    Course = Column(String)
    Percentage12th = Column(Float)
    Address = Column(String)
    GuardianName = Column(String)
    GuardianPhone = Column(String)