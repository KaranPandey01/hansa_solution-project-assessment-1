"""
Endpoints for subjects, hostel allocation, marks and the "all details" search.
Uses plain parameterised SQL against the tables created by
add_subjects_hostel_marks.sql, so it does not touch models.py or schemas.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter()


# ---------- Request bodies (validated by FastAPI before our code runs) ----------
class NameIn(BaseModel):
    Name: str = Field(min_length=2, max_length=100)


class SubjectLink(BaseModel):
    SubjectID: int


class HostelAssign(BaseModel):
    HostelID: int
    RoomNo: str = Field(min_length=1, max_length=10)
    BedNo: int = Field(ge=1)


class MarkIn(BaseModel):
    SubjectID: int
    MarksObtained: float = Field(ge=0, le=100)
    ExamYear: int = Field(ge=2000, le=2100)


# ---------- Helpers ----------
# Constraint name in SQL Server -> readable message for the user
CONSTRAINT_MESSAGES = {
    "UQ_Subjects_Name": "That subject already exists.",
    "UQ_Hostels_Name": "That hostel already exists.",
    "PK_StudentSubjects": "The student already has this subject.",
    "UQ_HostelAllocation_Bed": "That bed is already allocated to another student.",
    "UQ_HostelAllocation_Student": "The student already has a bed (try again to update it).",
    "UQ_Marks_Student_Subject_Year": "Marks for this subject and year are already entered.",
    "FK_Marks_StudentSubject": "The student does not have this subject. Add the subject first.",
    "FK_StudentSubjects_Subject": "Selected subject was not found.",
    "FK_HostelAllocation_Hostel": "Selected hostel was not found.",
    "CK_Marks_Range": "Marks must be between 0 and 100.",
}


def friendly(error: IntegrityError) -> str:
    message = str(error.orig)
    for name, text_ in CONSTRAINT_MESSAGES.items():
        if name in message:
            return text_
    return "Could not save: conflicting or invalid data."


def rows(db: Session, sql: str, **params):
    """Run a SELECT and return a list of dicts."""
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]


def ensure_student(db: Session, student_id: int):
    found = db.execute(text("SELECT 1 FROM dbo.Students WHERE StudentID = :s"),
                       {"s": student_id}).first()
    if not found:
        raise HTTPException(status_code=404, detail="Student not found")


def write(db: Session, sql: str, **params):
    """Run one INSERT (optionally with OUTPUT) and commit; map DB errors to HTTP errors."""
    try:
        result = db.execute(text(sql), params)
        value = result.scalar() if result.returns_rows else None
        db.commit()
        return value
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=friendly(error))
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


def enroll_default_subjects(db: Session, student_id: int):
    """Give a student every subject flagged IsDefault. Called by create_student in main.py,
    inside the same transaction as the student INSERT (no commit here)."""
    db.execute(text(
        "INSERT INTO dbo.StudentSubjects (StudentID, SubjectID) "
        "SELECT :s, SubjectID FROM dbo.Subjects WHERE IsDefault = 1"), {"s": student_id})


# ---------- Master lists ----------
@router.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    return rows(db, "SELECT SubjectID, SubjectName FROM dbo.Subjects ORDER BY SubjectName")


@router.post("/subjects", status_code=201)
def add_subject(body: NameIn, db: Session = Depends(get_db)):
    new_id = write(db, "INSERT INTO dbo.Subjects (SubjectName) OUTPUT inserted.SubjectID VALUES (:n)",
                   n=body.Name.strip())
    return {"message": "Subject added", "SubjectID": new_id}


@router.get("/hostels")
def list_hostels(db: Session = Depends(get_db)):
    return rows(db, "SELECT HostelID, HostelName FROM dbo.Hostels ORDER BY HostelName")


@router.post("/hostels", status_code=201)
def add_hostel(body: NameIn, db: Session = Depends(get_db)):
    new_id = write(db, "INSERT INTO dbo.Hostels (HostelName) OUTPUT inserted.HostelID VALUES (:n)",
                   n=body.Name.strip())
    return {"message": "Hostel added", "HostelID": new_id}


# ---------- Per-student actions ----------
@router.post("/students/{student_id}/subjects", status_code=201)
def add_student_subject(student_id: int, body: SubjectLink, db: Session = Depends(get_db)):
    ensure_student(db, student_id)
    write(db, "INSERT INTO dbo.StudentSubjects (StudentID, SubjectID) VALUES (:s, :sub)",
          s=student_id, sub=body.SubjectID)
    return {"message": "Subject added to student"}


@router.put("/students/{student_id}/hostel")
def allocate_hostel(student_id: int, body: HostelAssign, db: Session = Depends(get_db)):
    """One hostel/room/bed per student: update the existing allocation or create it."""
    ensure_student(db, student_id)
    params = {"s": student_id, "h": body.HostelID, "r": body.RoomNo.strip(), "b": body.BedNo}
    try:
        updated = db.execute(text(
            "UPDATE dbo.HostelAllocation SET HostelID = :h, RoomNo = :r, BedNo = :b "
            "WHERE StudentID = :s"), params)
        if updated.rowcount == 0:
            db.execute(text(
                "INSERT INTO dbo.HostelAllocation (StudentID, HostelID, RoomNo, BedNo) "
                "VALUES (:s, :h, :r, :b)"), params)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=friendly(error))
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))
    return {"message": "Hostel allocated"}


@router.post("/students/{student_id}/marks", status_code=201)
def add_marks(student_id: int, body: MarkIn, db: Session = Depends(get_db)):
    ensure_student(db, student_id)
    write(db, "INSERT INTO dbo.Marks (StudentID, SubjectID, MarksObtained, ExamYear) "
              "VALUES (:s, :sub, :m, :y)",
          s=student_id, sub=body.SubjectID, m=body.MarksObtained, y=body.ExamYear)
    return {"message": "Marks saved"}   # Result (Pass/Fail) is calculated by SQL Server


# ---------- Search: everything about one student ----------
@router.get("/students/{student_id}/details")
def student_details(student_id: int, db: Session = Depends(get_db)):
    try:
        profile = rows(db,
            "SELECT StudentID, FullName, DOB, Gender, Email, Phone, Course, Percentage12th, "
            "Address, GuardianName, GuardianPhone FROM dbo.Students WHERE StudentID = :s",
            s=student_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Student not found")

        hostel = rows(db,
            "SELECT h.HostelName, a.RoomNo, a.BedNo FROM dbo.HostelAllocation a "
            "JOIN dbo.Hostels h ON h.HostelID = a.HostelID WHERE a.StudentID = :s",
            s=student_id)

        subjects = rows(db,
            "SELECT sb.SubjectID, sb.SubjectName FROM dbo.StudentSubjects ss "
            "JOIN dbo.Subjects sb ON sb.SubjectID = ss.SubjectID "
            "WHERE ss.StudentID = :s ORDER BY sb.SubjectName", s=student_id)

        marks = rows(db,
            "SELECT sb.SubjectName, m.MarksObtained, m.ExamYear, m.Result FROM dbo.Marks m "
            "JOIN dbo.Subjects sb ON sb.SubjectID = m.SubjectID "
            "WHERE m.StudentID = :s ORDER BY m.ExamYear, sb.SubjectName", s=student_id)

        return {"student": profile[0], "hostel": hostel[0] if hostel else None,
                "subjects": subjects, "marks": marks}
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=str(error))