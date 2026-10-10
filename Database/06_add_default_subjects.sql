USE StudentAdmissionDB;
GO

/* =====================================================================
   Run this AFTER add_subjects_hostel_marks.sql.
   - Adds an IsDefault flag to Subjects
   - Creates 4 default subjects (edit the names if you like)
   - Creates 2 starter hostels so a bed can be allocated straight away
   - Gives every EXISTING student the default subjects
   Safe to run more than once: nothing is duplicated.
   New students get the default subjects automatically from the backend.
   ===================================================================== */

-- Batch 1: add the column (must be its own batch before it is used below)
IF COL_LENGTH('dbo.Subjects', 'IsDefault') IS NULL
    ALTER TABLE dbo.Subjects
        ADD IsDefault BIT NOT NULL CONSTRAINT DF_Subjects_IsDefault DEFAULT (0);
GO

-- Batch 2: data
-- Default subjects (only inserted if missing)
INSERT INTO dbo.Subjects (SubjectName)
SELECT v.n
FROM (VALUES ('Mathematics'), ('Physics'), ('English'), ('Programming Fundamentals')) AS v(n)
WHERE NOT EXISTS (SELECT 1 FROM dbo.Subjects s WHERE s.SubjectName = v.n);

-- Mark them as the defaults
UPDATE dbo.Subjects
SET IsDefault = 1
WHERE SubjectName IN ('Mathematics', 'Physics', 'English', 'Programming Fundamentals');

-- Starter hostels (only inserted if missing)
INSERT INTO dbo.Hostels (HostelName)
SELECT v.n
FROM (VALUES ('Hostel A'), ('Hostel B')) AS v(n)
WHERE NOT EXISTS (SELECT 1 FROM dbo.Hostels h WHERE h.HostelName = v.n);

-- Give every existing student the default subjects (skips ones they already have)
INSERT INTO dbo.StudentSubjects (StudentID, SubjectID)
SELECT st.StudentID, sb.SubjectID
FROM dbo.Students st
CROSS JOIN dbo.Subjects sb
WHERE sb.IsDefault = 1
  AND NOT EXISTS (SELECT 1 FROM dbo.StudentSubjects x
                  WHERE x.StudentID = st.StudentID AND x.SubjectID = sb.SubjectID);
GO

-- Verify: should list the 4 default subjects and 2 hostels
SELECT SubjectID, SubjectName, IsDefault FROM dbo.Subjects ORDER BY SubjectID;
SELECT HostelID, HostelName FROM dbo.Hostels ORDER BY HostelID;
SELECT StudentID, COUNT(*) AS subjects_assigned FROM dbo.StudentSubjects GROUP BY StudentID;
GO