const API_URL = "http://127.0.0.1:8001";

let allStudents = [];   // students loaded from SQL Server
let editingId = null;   // null = Add mode, otherwise the StudentID being edited

// ---------- Form elements ----------
const form = document.getElementById("studentForm");
const studentId = document.getElementById("studentId");
const fullName = document.getElementById("fullName");
const dob = document.getElementById("dob");
const gender = document.getElementById("gender");
const email = document.getElementById("email");
const phone = document.getElementById("phone");
const course = document.getElementById("course");
const percentage = document.getElementById("percentage");
const address = document.getElementById("address");
const guardianName = document.getElementById("guardianName");
const guardianPhone = document.getElementById("guardianPhone");
const submitButton = document.getElementById("submitButton");
const clearButton = document.getElementById("clearButton");
const formHeading = document.getElementById("formHeading");
const tableBody = document.getElementById("studentTableBody");
const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");


// ---------- Helper: turn a failed response into readable text ----------
async function readError(response) {
    try {
        const body = await response.json();
        console.error("Backend error:", response.status, body);
        if (Array.isArray(body.detail)) {
            // FastAPI validation error (422)
            return body.detail.map(e => e.loc[e.loc.length - 1] + ": " + e.msg).join("\n");
        }
        return body.detail || ("Error " + response.status);
    } catch (e) {
        return "Error " + response.status;
    }
}


// ---------- VALIDATION (our own rules) ----------
function validate(data) {
    if (!/^[A-Za-z ]{3,}$/.test(data.FullName))
        return "Full Name must contain only letters and spaces (minimum 3 characters).";

    if (!data.DOB) return "Date of Birth is required.";
    const today = new Date();
    const birth = new Date(data.DOB);
    const age = today.getFullYear() - birth.getFullYear();
    if (birth > today || age < 15 || age > 60)
        return "Enter a valid Date of Birth (age between 15 and 60).";

    if (!data.Gender) return "Please select a Gender.";

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.Email))
        return "Enter a valid Email address.";

    if (!/^\d{10}$/.test(data.Phone))
        return "Phone must be exactly 10 digits.";

    if (!data.Course) return "Please select a Course.";

    if (isNaN(data.Percentage12th) || data.Percentage12th < 40 || data.Percentage12th > 100)
        return "12th Percentage must be between 40 and 100.";

    if (data.Address.length < 10)
        return "Address must be at least 10 characters.";

    if (!/^[A-Za-z ]{3,}$/.test(data.GuardianName))
        return "Guardian Name must contain only letters and spaces (minimum 3 characters).";

    if (!/^\d{10}$/.test(data.GuardianPhone))
        return "Guardian Phone must be exactly 10 digits.";

    if (data.GuardianPhone === data.Phone)
        return "Guardian Phone must be different from the student's Phone.";

    return null; // everything is valid
}


// ---------- LOAD + DISPLAY ----------
async function loadStudents() {
    try {
        const response = await fetch(API_URL + "/students");
        if (!response.ok) {
            alert("Could not load students:\n" + await readError(response));
            return;
        }
        allStudents = await response.json();
        displayStudents(allStudents);
    } catch (error) {
        console.error(error);
        alert("Unable to connect to the backend. Make sure FastAPI is running on port 8001.");
    }
}

function displayStudents(students) {
    tableBody.innerHTML = "";

    if (students.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No students found</td></tr>';
        return;
    }

    students.forEach(s => {
        const row = document.createElement("tr");

        [s.StudentID, s.FullName, s.Course, s.Email, s.Phone].forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });

        const actions = document.createElement("td");

        const editBtn = document.createElement("button");
        editBtn.className = "btn btn-sm btn-warning me-1";
        editBtn.textContent = "Edit";
        editBtn.onclick = () => startEdit(s.StudentID);

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "btn btn-sm btn-danger";
        deleteBtn.textContent = "Delete";
        deleteBtn.onclick = () => deleteStudent(s.StudentID);

        actions.appendChild(editBtn);
        actions.appendChild(deleteBtn);
        row.appendChild(actions);
        tableBody.appendChild(row);
    });
}


// ---------- INSERT + UPDATE ----------
form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const data = {
        FullName: fullName.value.trim(),
        DOB: dob.value,
        Gender: gender.value,
        Email: email.value.trim(),
        Phone: phone.value.trim(),
        Course: course.value,
        Percentage12th: parseFloat(percentage.value),
        Address: address.value.trim(),
        GuardianName: guardianName.value.trim(),
        GuardianPhone: guardianPhone.value.trim()
    };

    const problem = validate(data);
    if (problem) {
        alert(problem);
        return;
    }

    const isEditing = editingId !== null;
    const url = isEditing ? API_URL + "/students/" + editingId : API_URL + "/students";

    submitButton.disabled = true;               // block double submits
    try {
        const response = await fetch(url, {
            method: isEditing ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            alert("Could not save the student:\n" + await readError(response));
            await loadStudents();               // resync in case someone else changed data
            return;
        }

        alert(isEditing ? "Student updated successfully." : "Student added successfully.");
        resetForm();
        await loadStudents();
    } catch (error) {
        console.error(error);
        alert("Unable to connect to the backend. Make sure FastAPI is running on port 8001.");
    } finally {
        submitButton.disabled = false;          // always re-enable
    }
});

// ---------- EDIT ----------
function startEdit(id) {
    const s = allStudents.find(x => x.StudentID === id);
    if (!s) return;

    editingId = id;
    studentId.value = s.StudentID;
    fullName.value = s.FullName;
    dob.value = s.DOB;                 // already "YYYY-MM-DD"
    gender.value = s.Gender;
    email.value = s.Email;
    phone.value = s.Phone;
    course.value = s.Course;
    percentage.value = s.Percentage12th;
    address.value = s.Address;
    guardianName.value = s.GuardianName;
    guardianPhone.value = s.GuardianPhone;

    submitButton.textContent = "Update Student";
    formHeading.textContent = "Edit Student";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetForm() {
    form.reset();
    editingId = null;
    studentId.value = "";
    submitButton.textContent = "Add Student";
    formHeading.textContent = "Student Admission Form";
}

// Clear button also leaves edit mode
clearButton.addEventListener("click", () => setTimeout(resetForm, 0));


// ---------- DELETE ----------
async function deleteStudent(id) {
    if (!confirm("Delete student " + id + "?")) return;

    try {
        const response = await fetch(API_URL + "/students/" + id, { method: "DELETE" });

        if (!response.ok) {
            alert("Could not delete the student:\n" + await readError(response));
            return;
        }

        alert("Student deleted successfully.");
        if (editingId === id) resetForm();
        await loadStudents();
    } catch (error) {
        console.error(error);
        alert("Unable to connect to the backend. Make sure FastAPI is running on port 8001.");
    }
}


// ---------- SEARCH ----------
function searchStudents() {
    const keyword = searchInput.value.trim().toLowerCase();

    const results = allStudents.filter(s =>
        String(s.StudentID).includes(keyword) ||
        (s.FullName || "").toLowerCase().includes(keyword) ||
        (s.Course || "").toLowerCase().includes(keyword) ||
        (s.Email || "").toLowerCase().includes(keyword) ||
        (s.Phone || "").includes(keyword)
    );
    displayStudents(results);
}

searchButton.addEventListener("click", searchStudents);
searchInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        event.preventDefault();
        searchStudents();
    }
});


// Load students when the page opens
loadStudents();