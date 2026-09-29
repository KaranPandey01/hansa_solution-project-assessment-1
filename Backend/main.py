from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import Student
from schemas import StudentCreate, StudentOut

app = FastAPI(title="Student Admission System")

# Allow the frontend (port 5500) to talk to this API (port 8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creates the table only if it is missing; existing data is never touched
Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Student Admission System API is running"}


# VIEW: return all students (searching is done in the frontend)
@app.get("/students", response_model=List[StudentOut])
def get_students(db: Session = Depends(get_db)):
    try:
        return db.query(Student).order_by(Student.StudentID).all()
    except SQLAlchemyError as error:
        raise HTTPException(status_code=500, detail=str(error))


# INSERT: next ID = highest existing ID + 1 (table has no IDENTITY column)
@app.post("/students", status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    try:
        max_id = db.query(func.max(Student.StudentID)).scalar()
        next_id = (max_id + 1) if max_id is not None else 101

        student = Student(StudentID=next_id, **data.model_dump())
        db.add(student)
        db.commit()
        return {"message": "Student registered successfully", "StudentID": next_id}
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


# UPDATE: change all fields of an existing student
@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentCreate, db: Session = Depends(get_db)):
    try:
        student = db.get(Student, student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        for field, value in data.model_dump().items():
            setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(error))


# DELETE: remove a student
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