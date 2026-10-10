USE StudentAdmissionDB;
GO

CREATE TABLE Students
(
    StudentID INT PRIMARY KEY,
    FullName VARCHAR(100) NOT NULL,
    DOB DATE NOT NULL,
    Gender VARCHAR(10),
    Email VARCHAR(100),
    Phone VARCHAR(15),
    Course VARCHAR(100),
    Percentage12th DECIMAL(5,2),
    Address VARCHAR(250),
    GuardianName VARCHAR(100),
    GuardianPhone VARCHAR(15)
);
GO