USE StudentAdmissionDB;
GO

-- ============================================
-- STUDENT ADMISSION DATABASE PROJECT
-- ============================================


-- 1. Display all students
SELECT *
FROM Students;


-- 2. Display students ordered by StudentID
SELECT *
FROM Students
ORDER BY StudentID;


-- 3. Students with 12th percentage >= 80
SELECT *
FROM Students
WHERE Percentage12th >= 80;


-- 4. Students belonging to B.Tech CSE
SELECT *
FROM Students
WHERE Course = 'B.Tech CSE';


-- 5. Students with 12th percentage below 80
SELECT *
FROM Students
WHERE Percentage12th < 80;


-- 6. Students ordered by percentage (highest first)
SELECT *
FROM Students
ORDER BY Percentage12th DESC;


-- ============================================
-- AGGREGATE FUNCTIONS
-- ============================================

-- 7. Total number of students
SELECT COUNT(*) AS TotalStudents
FROM Students;


-- 8. Average 12th percentage
SELECT AVG(Percentage12th) AS AveragePercentage
FROM Students;


-- 9. Highest 12th percentage
SELECT MAX(Percentage12th) AS HighestPercentage
FROM Students;


-- 10. Lowest 12th percentage
SELECT MIN(Percentage12th) AS LowestPercentage
FROM Students;


-- 11. Average percentage by course
SELECT Course,
       AVG(Percentage12th) AS AveragePercentage
FROM Students
GROUP BY Course;


-- ============================================
-- UPDATE OPERATION
-- ============================================

-- 12. Update student's address
UPDATE Students
SET Address = 'Pune'
WHERE StudentID = 101;


-- 13. Verify updated student
SELECT *
FROM Students
WHERE StudentID = 101;