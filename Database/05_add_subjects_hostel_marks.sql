USE StudentAdmissionDB;
GO

/* =====================================================================
   New tables linked to Students (all IDs are IDENTITY = auto-generated):

   Subjects          master list of subjects                    (SubjectID)
   StudentSubjects   student -> MANY subjects                   (one-to-many)
   Hostels           master list of hostels                     (HostelID)
   HostelAllocation  student -> ONE hostel, room and bed        (one-to-one)
   Marks             student -> MANY marks (per subject/year)   (one-to-many)

   Pass mark is assumed to be 40. Change it in the Result column below if needed.
   All-or-nothing: any error rolls the whole script back.
   ===================================================================== */

SET XACT_ABORT ON;
BEGIN TRAN;

-- ---------- Subjects (master list) ----------
CREATE TABLE dbo.Subjects (
    SubjectID   INT IDENTITY(1, 1) NOT NULL
                CONSTRAINT PK_Subjects PRIMARY KEY,
    SubjectName VARCHAR(100) NOT NULL
                CONSTRAINT UQ_Subjects_Name UNIQUE      -- no subject listed twice
);

-- ---------- One student -> many subjects ----------
CREATE TABLE dbo.StudentSubjects (
    StudentID INT NOT NULL,
    SubjectID INT NOT NULL,
    CONSTRAINT PK_StudentSubjects PRIMARY KEY (StudentID, SubjectID),   -- a student can't take the same subject twice
    CONSTRAINT FK_StudentSubjects_Student FOREIGN KEY (StudentID)
        REFERENCES dbo.Students (StudentID) ON DELETE CASCADE,          -- deleting a student removes their subjects
    CONSTRAINT FK_StudentSubjects_Subject FOREIGN KEY (SubjectID)
        REFERENCES dbo.Subjects (SubjectID)
);

-- ---------- Hostels (master list) ----------
CREATE TABLE dbo.Hostels (
    HostelID   INT IDENTITY(1, 1) NOT NULL
               CONSTRAINT PK_Hostels PRIMARY KEY,
    HostelName VARCHAR(100) NOT NULL
               CONSTRAINT UQ_Hostels_Name UNIQUE
);

-- ---------- One student -> one hostel, room and bed ----------
CREATE TABLE dbo.HostelAllocation (
    AllocationID INT IDENTITY(1, 1) NOT NULL
                 CONSTRAINT PK_HostelAllocation PRIMARY KEY,
    StudentID    INT NOT NULL
                 CONSTRAINT UQ_HostelAllocation_Student UNIQUE,         -- one-to-one: a student gets only one bed
    HostelID     INT NOT NULL,
    RoomNo       VARCHAR(10) NOT NULL,
    BedNo        INT NOT NULL,
    CONSTRAINT UQ_HostelAllocation_Bed UNIQUE (HostelID, RoomNo, BedNo),  -- one bed can't go to two students (even if they book at the same instant)
    CONSTRAINT FK_HostelAllocation_Student FOREIGN KEY (StudentID)
        REFERENCES dbo.Students (StudentID) ON DELETE CASCADE,
    CONSTRAINT FK_HostelAllocation_Hostel FOREIGN KEY (HostelID)
        REFERENCES dbo.Hostels (HostelID)
);

-- ---------- One student -> many marks ----------
CREATE TABLE dbo.Marks (
    MarkID        INT IDENTITY(1, 1) NOT NULL
                  CONSTRAINT PK_Marks PRIMARY KEY,
    StudentID     INT NOT NULL,
    SubjectID     INT NOT NULL,
    MarksObtained DECIMAL(5, 2) NOT NULL
                  CONSTRAINT CK_Marks_Range CHECK (MarksObtained BETWEEN 0 AND 100),
    ExamYear      INT NOT NULL,                                        -- year the exam was taken/passed
    Result        AS (CASE WHEN MarksObtained >= 40 THEN 'Pass' ELSE 'Fail' END) PERSISTED,  -- calculated by SQL Server, can never be wrong or typed by hand
    CONSTRAINT UQ_Marks_Student_Subject_Year UNIQUE (StudentID, SubjectID, ExamYear),
    CONSTRAINT FK_Marks_StudentSubject FOREIGN KEY (StudentID, SubjectID)  -- marks only for subjects the student actually has
        REFERENCES dbo.StudentSubjects (StudentID, SubjectID) ON DELETE CASCADE
);

COMMIT;
GO


/* =====================================================================
   SEARCH: all details of one student (change the ID).
   Returns four result sets: profile, hostel, subjects, marks with Pass/Fail.
   ===================================================================== */
DECLARE @StudentID INT = 101;

SELECT * FROM dbo.Students WHERE StudentID = @StudentID;               -- 1. profile

SELECT h.HostelName, a.RoomNo, a.BedNo                                 -- 2. hostel, room, bed
FROM dbo.HostelAllocation a
JOIN dbo.Hostels h ON h.HostelID = a.HostelID
WHERE a.StudentID = @StudentID;

SELECT sb.SubjectName                                                  -- 3. subjects
FROM dbo.StudentSubjects ss
JOIN dbo.Subjects sb ON sb.SubjectID = ss.SubjectID
WHERE ss.StudentID = @StudentID;

SELECT sb.SubjectName, m.MarksObtained, m.ExamYear, m.Result           -- 4. marks and Pass/Fail
FROM dbo.Marks m
JOIN dbo.Subjects sb ON sb.SubjectID = m.SubjectID
WHERE m.StudentID = @StudentID
ORDER BY m.ExamYear, sb.SubjectName;
GO