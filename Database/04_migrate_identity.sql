USE StudentAdmissionDB;
GO

/* =====================================================================
   Convert Students.StudentID to IDENTITY.
   SQL Server can't ALTER an existing column to IDENTITY, so the table
   is rebuilt. Column types below match your original CREATE TABLE.

   STEP 1 - run the three duplicate checks first. All must return NO rows,
   otherwise the UNIQUE constraints in step 2 will fail (and the whole
   migration rolls back safely).
   ===================================================================== */

SELECT Email, COUNT(*) AS cnt FROM Students GROUP BY Email HAVING COUNT(*) > 1;
SELECT Phone, COUNT(*) AS cnt FROM Students GROUP BY Phone HAVING COUNT(*) > 1;
SELECT FullName, DOB, COUNT(*) AS cnt FROM Students GROUP BY FullName, DOB HAVING COUNT(*) > 1;
GO


/* STEP 2 - the migration (all-or-nothing: any error rolls everything back) */

SET XACT_ABORT ON;
BEGIN TRAN;

CREATE TABLE dbo.Students_new (
    StudentID      INT IDENTITY(101, 1) NOT NULL
                   CONSTRAINT PK_Students_new PRIMARY KEY,
    FullName       VARCHAR(100) NOT NULL,
    DOB            DATE         NOT NULL,
    Gender         VARCHAR(10)  NULL,
    Email          VARCHAR(100) NULL,
    Phone          VARCHAR(15)  NULL,
    Course         VARCHAR(100) NULL,
    Percentage12th DECIMAL(5,2) NULL,
    Address        VARCHAR(250) NULL,
    GuardianName   VARCHAR(100) NULL,
    GuardianPhone  VARCHAR(15)  NULL
);

-- Copy existing rows with their ORIGINAL IDs. SQL Server moves the identity
-- counter past the highest copied ID automatically.
SET IDENTITY_INSERT dbo.Students_new ON;

INSERT INTO dbo.Students_new
    (StudentID, FullName, DOB, Gender, Email, Phone, Course,
     Percentage12th, Address, GuardianName, GuardianPhone)
SELECT
     StudentID, FullName, DOB, Gender, Email, Phone, Course,
     Percentage12th, Address, GuardianName, GuardianPhone
FROM dbo.Students;

SET IDENTITY_INSERT dbo.Students_new OFF;

-- Swap the tables (fails safely if another table has a foreign key to Students)
DROP TABLE dbo.Students;
EXEC sp_rename N'dbo.Students_new', N'Students';
EXEC sp_rename N'dbo.PK_Students_new', N'PK_Students', N'OBJECT';

-- The database itself now rejects duplicates, even under simultaneous requests
ALTER TABLE dbo.Students ADD CONSTRAINT UQ_Students_Email   UNIQUE (Email);
ALTER TABLE dbo.Students ADD CONSTRAINT UQ_Students_Phone   UNIQUE (Phone);
ALTER TABLE dbo.Students ADD CONSTRAINT UQ_Students_NameDOB UNIQUE (FullName, DOB);

COMMIT;
GO


/* STEP 3 - verify */
SELECT name, is_identity FROM sys.columns
WHERE object_id = OBJECT_ID('dbo.Students') AND name = 'StudentID';   -- is_identity = 1

SELECT IDENT_CURRENT('dbo.Students') AS last_id_used;
GO