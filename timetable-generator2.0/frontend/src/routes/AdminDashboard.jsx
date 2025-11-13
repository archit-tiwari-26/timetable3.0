import React, { useState, useEffect } from "react";

import AdminFormGenerator from "../components/AdminFormGenerator";
import CourseForm from "../components/CourseForm";
import TeacherForm from "../components/TeacherForm";

import API, {
  createBatches,
  createRooms,
  postGenerate,
  fetchCourses,
  fetchTeachers,
} from "../api";

export default function AdminDashboard() {
  const [status, setStatus] = useState("");
  const [courses, setCourses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load courses & teachers
  async function loadData() {
    try {
      const [c, t] = await Promise.all([fetchCourses(), fetchTeachers()]);
      setCourses(c.data);
      setTeachers(t.data);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // Create batches & rooms
  async function handleCreateEntities(payload) {
    setStatus("Creating entities...");
    setLoading(true);

    try {
      for (let i = 1; i <= payload.numBatches; i++) {
        await createBatches({ name: `F${i}`, size: 30 });
      }

      for (let i = 1; i <= payload.lectureRooms; i++) {
        await createRooms({
          name: `M${i}`,
          capacity: 70,
          room_type: "Lecture_X",
        });
      }

      for (let i = 1; i <= payload.tutorRooms; i++) {
        await createRooms({
          name: `T${i}`,
          capacity: 40,
          room_type: "Tutorial_Y",
        });
      }

      for (let i = 1; i <= payload.labRooms; i++) {
        await createRooms({
          name: `L${i}`,
          capacity: 100,
          room_type: "Lab",
        });
      }

      setStatus("✅ Entities created successfully!");
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed creating entities");
    }

    setLoading(false);
  }

  // Auto Prepare (Timeslots + Events)
  async function handleAutoPrepare() {
    setLoading(true);
    setStatus("⏳ Auto-creating timeslots & events...");

    try {
      await API.post("/admin/auto-prepare/");
      setStatus("✅ Auto-preparation completed. You may now generate the timetable.");
    } catch (e) {
      console.error(e);
      setStatus("❌ Auto-preparation failed: " + (e?.response?.data?.detail || e.message));
    }

    setLoading(false);
  }

  // Generate timetable
  async function handleGenerate() {
    setStatus("⏳ Generating timetable... (may take a while)");
    setLoading(true);

    try {
      await postGenerate();
      setStatus("✅ Timetable generated successfully!");
    } catch (e) {
      console.error(e);
      setStatus("❌ Generation failed: " + (e?.response?.data?.detail || e.message));
    }

    setLoading(false);
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

      {/* LEFT COLUMN — Setup */}
      <div className="xl:col-span-2 space-y-8">

        {/* ADMIN QUICK SETUP */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
          <h2 className="text-xl font-semibold mb-3">🔧 Quick Setup</h2>
          <p className="text-gray-600 mb-4">
            Automatically create batches, lecture rooms, tutorial rooms, and labs.
          </p>

          <AdminFormGenerator onCreate={handleCreateEntities} />

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleAutoPrepare}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg shadow"
            >
              ⚡ Auto-Prepare (Timeslots + Events)
            </button>

            <button
              onClick={handleGenerate}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow"
            >
              🗓️ Generate Timetable
            </button>
          </div>

          {loading && <div className="text-indigo-600 text-sm mt-3">Processing…</div>}

          {status && (
            <div className="mt-3 text-sm font-medium text-gray-800 bg-gray-100 px-3 py-2 rounded">
              {status}
            </div>
          )}
        </div>

        {/* COURSE CREATION */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold mb-3">📚 Add New Course</h2>
          <CourseForm
            onCreated={() => {
              loadData();
              setStatus("Course created");
            }}
          />
        </div>

        {/* TEACHER CREATION */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
          <h2 className="text-lg font-semibold mb-3">👨‍🏫 Add New Faculty</h2>
          <TeacherForm
            onCreated={() => {
              loadData();
              setStatus("Faculty created");
            }}
          />
        </div>

      </div>

      {/* RIGHT COLUMN — Preview */}
      <div className="space-y-8">

        {/* COURSES LIST */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
          <h3 className="text-lg font-semibold mb-3">📘 Current Courses</h3>
          <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">

            {courses.map((c) => (
              <li key={c.id}>
                <span className="font-medium">{c.name}</span> — {c.course_type}
              </li>
            ))}

            {courses.length === 0 && (
              <li className="text-gray-400">No courses added yet.</li>
            )}

          </ul>
        </div>

        {/* TEACHERS LIST */}
        <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
          <h3 className="text-lg font-semibold mb-3">👩‍🏫 Current Faculties</h3>

          <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">
            {teachers.map((t) => (
              <li key={t.id}>
                <span className="font-medium">{t.name}</span> — Max: {t.max_hours} hrs
              </li>
            ))}

            {teachers.length === 0 && (
              <li className="text-gray-400">No faculties added yet.</li>
            )}
          </ul>

        </div>

      </div>
    </div>
  );
}
