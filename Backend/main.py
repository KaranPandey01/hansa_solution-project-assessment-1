from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text, and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Student
from schemas import StudentCreate, StudentOut

app = FastAPI(title="Student Admission System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# ---------- Helper 1: lock the table and return the highest ID ----------
def lock_and_get_max_id(db: Session):
    """Reads MAX(StudentID) while holding a lock until commit/rollback.
    UPDLOCK + HOLDLOCK make other writers WAIT here, so two requests can
    never read the same MAX at the same time."""
    return db.execute(
        text("SELECT MAX(StudentID) FROM Students WITH (UPDLOCK, HOLDLOCK)")
    ).scalar()


# ---------- Helper 2: duplicate detection ----------
def find_duplicate(db: Session, data: StudentCreate, exclude_id: int = None):
    """Return an error message if another student has the same details,
    otherwise None. exclude_id lets a student be saved without clashing
    with its own row (used by PUT)."""
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
        # 1. Lock first, so the steps below cannot interleave with another request
        max_id = lock_and_get_max_id(db)

        # 2. Reject duplicates (checked while we hold the lock)
        problem = find_duplicate(db, data)
        if problem:
            db.rollback()                      # release the lock immediately
            raise HTTPException(status_code=409, detail=problem)

        # 3. Safe to generate the ID and insert
        next_id = (max_id + 1) if max_id is not None else 101
        student = Student(StudentID=next_id, **data.model_dump())
        db.add(student)
        db.commit()                            # lock released here
        return {"message": "Student registered successfully", "StudentID": next_id}

    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not save: duplicate or conflicting data.")
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


# ---------- UPDATE ----------
@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentCreate, db: Session = Depends(get_db)):
    try:
        lock_and_get_max_id(db)                # same lock: serialises writes

        student = db.get(Student, student_id)
        if student is None:
            db.rollback()
            raise HTTPException(status_code=404, detail="Student not found")

        # Ignore this student's own row when looking for duplicates
        problem = find_duplicate(db, data, exclude_id=student_id)
        if problem:
            db.rollback()
            raise HTTPException(status_code=409, detail=problem)

        for field, value in data.model_dump().items():
            setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not save: duplicate or conflicting data.")
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