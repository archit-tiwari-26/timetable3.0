import React, { useState, useEffect } from "react";

import AdminFormGenerator from "../components/AdminFormGenerator";
import CourseForm from "../components/CourseForm";
import TeacherForm from "../components/TeacherForm";
import EditableList from "../components/EditableList";

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

  // ------------------------------
  // CREATE ENTITIES
  // ------------------------------
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

      setStatus("Entities created successfully 🎉");
    } catch (e) {
      console.error(e);
      setStatus("Failed creating entities ❌");
    }

    setLoading(false);
  }

  // ------------------------------
  // AUTO PREPARE
  // ------------------------------
  async function handleAutoPrepare() {
    setLoading(true);
    setStatus("Preparing…");

    try {
      await API.post("/admin/auto-prepare/");
      setStatus("Auto-preparation complete ✨");
    } catch (e) {
      console.error(e);
      setStatus("Auto-preparation failed: " + (e?.response?.data?.detail || e.message));
    }

    setLoading(false);
  }

  // ------------------------------
  // GENERATE TIMETABLE
  // ------------------------------
  async function handleGenerate() {
    setStatus("Generating timetable…");
    setLoading(true);

    try {
      await postGenerate();
      setStatus("Timetable generated successfully!");
    } catch (e) {
      console.error(e);
      setStatus("Generation failed: " + (e?.response?.data?.detail || e.message));
    }

    setLoading(false);
  }

  // ------------------------------
  // EDIT / DELETE HANDLERS
  // ------------------------------
  async function editCourse(id, updated) {
    await API.put(`/courses/${id}`, updated);
    loadData();
  }

  async function deleteCourse(id) {
    if (!window.confirm("Delete this course?")) return;
    await API.delete(`/courses/${id}`);
    loadData();
  }

  async function editTeacher(id, updated) {
    await API.put(`/teachers/${id}`, updated);
    loadData();
  }

  async function deleteTeacher(id) {
    if (!window.confirm("Delete this faculty?")) return;
    await API.delete(`/teachers/${id}`);
    loadData();
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-12 p-2">

      {/* LEFT PANEL */}
      <div className="xl:col-span-2 space-y-12">
        
        {/* QUICK SETUP CARD */}
        <div className="
          rounded-3xl p-0.5 
          bg-linear-to-r from-indigo-400 via-purple-400 to-pink-400
          shadow-xl animate-[fadeIn_0.6s_ease]
        ">
          <div className="bg-white/90 rounded-3xl p-10 backdrop-blur-2xl shadow-xl">
            <h2 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
              Admin Quick Setup
            </h2>
            <p className="text-slate-600 mb-6">
              Create batches, lecture rooms, tutorials, and labs in one go.
            </p>

            <AdminFormGenerator onCreate={handleCreateEntities} />

            <div className="mt-8 flex gap-4">
              <button
                onClick={handleAutoPrepare}
                className="
                  px-6 py-3 rounded-xl
                  bg-linear-to-r from-indigo-500 to-purple-500 
                  text-white font-medium shadow-md
                  hover:scale-[1.03] hover:shadow-lg
                  transition-all duration-200
                "
              >
                Auto-Prepare
              </button>

              <button
                onClick={handleGenerate}
                className="
                  px-6 py-3 rounded-xl
                  bg-slate-900 text-white shadow-md
                  hover:bg-black hover:shadow-lg hover:scale-[1.03]
                  transition-all duration-200
                "
              >
                Generate Timetable
              </button>
            </div>

            {loading && (
              <div className="text-indigo-600 text-sm mt-4 animate-pulse">
                Processing…
              </div>
            )}

            {status && (
              <div className="
                mt-4 text-sm text-slate-700 
                bg-slate-100 border border-slate-200 
                px-4 py-2 rounded-xl
              ">
                {status}
              </div>
            )}
          </div>
        </div>

        {/* FACULTY CREATION */}
        <div className="rounded-3xl p-0.5 bg-linear-to-r from-purple-300 to-indigo-300 shadow-xl">
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-10">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              Add Faculty
            </h2>
            <TeacherForm
              onCreated={() => {
                loadData();
                setStatus("Faculty created");
              }}
            />
          </div>
        </div>

        {/* COURSE CREATION */}
        <div className="rounded-3xl p-0.5 bg-linear-to-r from-sky-300 to-indigo-300 shadow-xl">
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-10">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              Add Course
            </h2>
            <CourseForm
              onCreated={() => {
                loadData();
                setStatus("Course created");
              }}
            />
          </div>
        </div>

      </div>

      {/* RIGHT PANEL */}
      <div className="space-y-12">

        {/* FACULTY LIST with edit/delete */}
        {/* FACULTY LIST */}
<div className="rounded-3xl p-0.5 bg-linear-to-br from-indigo-300 to-purple-300 shadow-xl">
  <div className="bg-white/90 rounded-3xl p-8 backdrop-blur-xl">
    <h3 className="text-lg font-semibold text-slate-900 mb-4">
      Faculty List
    </h3>

    <EditableList
      title="Faculty"
      items={teachers}
      fields={["name", "max_hours"]}
      onEdit={editTeacher}
      onDelete={deleteTeacher}
      itemClassName="hover:bg-slate-100 transition rounded-lg px-2 py-2"
      labelColor="text-slate-900"
      valueColor="text-slate-500"
    />
  </div>
</div>


        {/* COURSES LIST with edit/delete */}
        {/* COURSES LIST */}
<div className="rounded-3xl p-0.5 bg-linear-to-br from-sky-300 to-indigo-300 shadow-xl">
  <div className="bg-white/90 rounded-3xl p-8 backdrop-blur-xl">
    <h3 className="text-lg font-semibold text-slate-900 mb-4">
      Courses List
    </h3>

    <EditableList
      title="Courses"
      items={courses}
      fields={["name", "credit_hours"]}
      onEdit={editCourse}
      onDelete={deleteCourse}
      itemClassName="hover:bg-slate-100 transition rounded-lg px-2 py-2"
      labelColor="text-slate-900"
      valueColor="text-slate-500"
    />
  </div>
</div>



      </div>
    </div>
  );
}
