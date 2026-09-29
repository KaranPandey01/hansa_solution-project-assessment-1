from sqlalchemy import Column, Integer, String, Float, Date
from database import Base


class Student(Base):
    """Maps to the existing SQL Server table 'Students'."""
    __tablename__ = "Students"

    # StudentID is NOT an IDENTITY column in the existing database,
    # so the backend assigns it manually (see create_student in main.py).
    StudentID = Column(Integer, primary_key=True, autoincrement=False)
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