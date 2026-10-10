// Logic for the "Student Details" section of index.html.
// Wrapped in a function so its names can never clash with script.js.
(function () {
    const API = "http://127.0.0.1:8001";
    let currentId = null;   // the student currently shown

    const $ = id => document.getElementById(id);

    // ---------- Talk to the backend; throw a readable error on failure ----------
    async function api(path, method = "GET", body) {
        const res = await fetch(API + path, {
            method: method,
            headers: body ? { "Content-Type": "application/json" } : {},
            body: body ? JSON.stringify(body) : undefined
        });
        let data = null;
        try { data = await res.json(); } catch (e) { /* no body */ }
        if (!res.ok) {
            let message = "Error " + res.status;
            if (data && data.detail) {
                message = Array.isArray(data.detail)
                    ? data.detail.map(e => e.loc[e.loc.length - 1] + ": " + e.msg).join("\n")
                    : data.detail;
            }
            throw new Error(message);
        }
        return data;
    }

    // Run an action; show any error in a popup
    async function safe(action) {
        try { await action(); } catch (e) { alert(e.message); }
    }

    function fillSelect(select, items, valueKey, labelKey, placeholder) {
        select.innerHTML = "";
        const first = document.createElement("option");
        first.value = "";
        first.textContent = placeholder;
        select.appendChild(first);
        items.forEach(item => {
            const option = document.createElement("option");
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            select.appendChild(option);
        });
    }

    // ---------- Master lists (subjects + hostels) ----------
    async function loadMaster() {
        const subjects = await api("/subjects");
        const hostels = await api("/hostels");
        fillSelect($("subjectSelect"), subjects, "SubjectID", "SubjectName", "Choose subject...");
        fillSelect($("hostelSelect"), hostels, "HostelID", "HostelName", "Choose hostel...");
    }

    // ---------- Show everything about one student ----------
    async function loadDetails() {
        const d = await api("/students/" + currentId + "/details");
        $("detailsResult").classList.remove("d-none");

        // Profile
        const profile = $("detailsProfile");
        profile.innerHTML = "";
        const labels = {
            StudentID: "ID", FullName: "Name", DOB: "Date of Birth", Gender: "Gender", Email: "Email",
            Phone: "Phone", Course: "Course", Percentage12th: "12th %", Address: "Address",
            GuardianName: "Guardian", GuardianPhone: "Guardian Phone"
        };
        Object.keys(labels).forEach(key => {
            const dt = document.createElement("dt");
            dt.className = "col-sm-3";
            dt.textContent = labels[key];
            const dd = document.createElement("dd");
            dd.className = "col-sm-9";
            dd.textContent = d.student[key];
            profile.appendChild(dt);
            profile.appendChild(dd);
        });

        // Hostel
        $("hostelText").textContent = d.hostel
            ? d.hostel.HostelName + "  |  Room " + d.hostel.RoomNo + "  |  Bed " + d.hostel.BedNo
            : "No hostel allocated yet.";

        // Subjects
        const list = $("subjectList");
        list.innerHTML = "";
        if (d.subjects.length === 0) list.textContent = "No subjects yet.";
        d.subjects.forEach(s => {
            const badge = document.createElement("span");
            badge.className = "badge text-bg-secondary me-1";
            badge.textContent = s.SubjectName;
            list.appendChild(badge);
        });
        fillSelect($("markSubject"), d.subjects, "SubjectID", "SubjectName", "Subject...");

        // Marks with Pass/Fail
        const body = $("marksBody");
        body.innerHTML = "";
        if (d.marks.length === 0) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 4;
            td.textContent = "No marks yet.";
            tr.appendChild(td);
            body.appendChild(tr);
        }
        d.marks.forEach(m => {
            const tr = document.createElement("tr");
            [m.SubjectName, m.MarksObtained, m.ExamYear].forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                tr.appendChild(td);
            });
            const resultCell = document.createElement("td");
            const badge = document.createElement("span");
            badge.className = "badge " + (m.Result === "Pass" ? "text-bg-success" : "text-bg-danger");
            badge.textContent = m.Result;
            resultCell.appendChild(badge);
            tr.appendChild(resultCell);
            body.appendChild(tr);
        });
    }

    // Called by the "Details" button in the student table (script.js)
    window.showDetails = function (id) {
        currentId = id;
        $("detailsSearchId").value = id;
        safe(loadDetails);
        $("detailsCard").scrollIntoView({ behavior: "smooth" });
    };

    // ---------- Buttons ----------
    $("detailsSearchBtn").addEventListener("click", () => safe(async () => {
        const id = $("detailsSearchId").value.trim();
        if (!id) { alert("Enter a Student ID."); return; }
        currentId = id;
        await loadDetails();
    }));

    $("addSubjectBtn").addEventListener("click", () => safe(async () => {
        await api("/subjects", "POST", { Name: $("newSubject").value });
        $("newSubject").value = "";
        await loadMaster();
    }));

    $("addHostelBtn").addEventListener("click", () => safe(async () => {
        await api("/hostels", "POST", { Name: $("newHostel").value });
        $("newHostel").value = "";
        await loadMaster();
    }));

    $("addStudentSubjectBtn").addEventListener("click", () => safe(async () => {
        if (!$("subjectSelect").value) { alert("Choose a subject."); return; }
        await api("/students/" + currentId + "/subjects", "POST", { SubjectID: Number($("subjectSelect").value) });
        await loadDetails();
    }));

    $("allocateBtn").addEventListener("click", () => safe(async () => {
        if (!$("hostelSelect").value) { alert("Choose a hostel."); return; }
        await api("/students/" + currentId + "/hostel", "PUT", {
            HostelID: Number($("hostelSelect").value),
            RoomNo: $("roomNo").value,
            BedNo: Number($("bedNo").value)
        });
        await loadDetails();
    }));

    $("addMarkBtn").addEventListener("click", () => safe(async () => {
        if (!$("markSubject").value) { alert("Choose a subject."); return; }
        await api("/students/" + currentId + "/marks", "POST", {
            SubjectID: Number($("markSubject").value),
            MarksObtained: Number($("markValue").value),
            ExamYear: Number($("markYear").value)
        });
        await loadDetails();
    }));

    // Load the subject and hostel dropdowns when the page opens
    safe(loadMaster);
})();