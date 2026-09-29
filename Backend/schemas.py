from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    """Data the frontend sends when adding or updating a student.
    Field names match the database columns and the frontend JSON exactly."""
    FullName: str = Field(min_length=1)
    DOB: date
    Gender: str = Field(min_length=1)
    Email: EmailStr
    Phone: str = Field(min_length=1)
    Course: str = Field(min_length=1)
    Percentage12th: float = Field(ge=0, le=100)
    Address: str = Field(min_length=1)
    GuardianName: str = Field(min_length=1)
    GuardianPhone: str = Field(min_length=1)


class StudentOut(StudentCreate):
    """Data the backend returns (includes StudentID)."""
    model_config = ConfigDict(from_attributes=True)

    StudentID: int