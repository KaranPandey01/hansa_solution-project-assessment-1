from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Student
from schemas import StudentCreate, StudentOut
from academics import router as academics_router, enroll_default_subjects  # subjects, hostel, marks, details search

app = FastAPI(title="Student Admission System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(academics_router)  # adds the new endpoints from academics.py


# ---------- Helper 1: duplicate detection (friendly pre-check) ----------
# This gives a clear message in the normal case. The real guarantee is the
# UNIQUE constraints in the database (see migrate_identity.sql), which also
# catch two simultaneous requests that both pass this check.
def find_duplicate(db: Session, data: StudentCreate, exclude_id: int = None):
    checks = [
        ("Email", func.lower(Student.Email) == data.Email.lower()),
        ("Phone", Student.Phone == data.Phone),
        ("Full Name and Date of Birth",
         and_(func.lower(Student.FullName) == data.FullName.lower(),
              Student.DOB == data.DOB)),
    ]
    for label, condition in checks:
        query = db.query(Student).filter(condition)
        if exclude_id is not None:
            query = query.filter(Student.StudentID != exclude_id)
        existing = query.first()
        if existing:
            return f"A student with the same {label} already exists (ID {existing.StudentID})."
    return None


# ---------- Helper 2: turn a constraint violation into a readable message ----------
CONSTRAINT_MESSAGES = {
    "UQ_Students_Email": "A student with the same Email already exists.",
    "UQ_Students_Phone": "A student with the same Phone already exists.",
    "UQ_Students_NameDOB": "A student with the same Full Name and Date of Birth already exists.",
}


def integrity_message(error: IntegrityError) -> str:
    text_of_error = str(error.orig)
    for name, message in CONSTRAINT_MESSAGES.items():
        if name in text_of_error:
            return message
    return "Could not save: duplicate or conflicting data."


@app.get("/")
def root():
    return {"message": "Student Admission System API is running"}


@app.get("/students", response_model=List[StudentOut])
def get_students(db: Session = Depends(get_db)):
    try:
        return db.query(Student).order_by(Student.StudentID).all()
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=str(error))


# ---------- INSERT ----------
@app.post("/students", status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    try:
        problem = find_duplicate(db, data)
        if problem:
            raise HTTPException(status_code=409, detail=problem)

        # No StudentID here: SQL Server generates it atomically (IDENTITY)
        student = Student(**data.model_dump())
        db.add(student)
        db.flush()                             # runs the INSERT now: SQL Server generates StudentID (still inside the transaction)
        enroll_default_subjects(db, student.StudentID)   # new student gets the default subjects
        db.commit()                            # student + default subjects saved together, or neither
        db.refresh(student)                    # loads the generated StudentID
        return {"message": "Student registered successfully", "StudentID": student.StudentID}

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=integrity_message(error))
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


# ---------- UPDATE ----------
@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentCreate, db: Session = Depends(get_db)):
    try:
        student = db.get(Student, student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        # Ignore this student's own row when looking for duplicates
        problem = find_duplicate(db, data, exclude_id=student_id)
        if problem:
            raise HTTPException(status_code=409, detail=problem)

        for field, value in data.model_dump().items():
            setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=integrity_message(error))
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


# ---------- DELETE ----------
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    try:
        student = db.get(Student, student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        db.delete(student)
        db.commit()
        return {"message": "Student deleted successfully"}
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))