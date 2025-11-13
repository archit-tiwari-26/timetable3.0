import React, { useState } from "react";

import IDInputModal from "../components/IDInputModal";
import TimetableGrid from "../components/Timetablegrid";
import FreeSlotsList from "../components/FreeSlotsList";
import DownloadPDF from "../components/DownloadPDF";

import {
  fetchTeacherTimetable,
  fetchBatchFreeSlots,
  fetchFullTimetable,
} from "../api";

export default function FacultyDashboard() {
  const [timetable, setTimetable] = useState(null);
  const [freeSlots, setFreeSlots] = useState(null);
  const [fullTimetable, setFullTimetable] = useState(null);

  const [loading, setLoading] = useState(false);
  const [currentTeacherId, setCurrentTeacherId] = useState(null);

  async function handleTeacher(id) {
    setLoading(true);
    try {
      const resp = await fetchTeacherTimetable(id);
      setTimetable(resp.data.timetable);
      setCurrentTeacherId(id);
    } catch (e) {
      alert("Failed to fetch faculty timetable");
    }
    setLoading(false);
  }

  async function handleFreeSlots(batchId) {
    setLoading(true);
    try {
      const resp = await fetchBatchFreeSlots(batchId);
      setFreeSlots(resp.data.timetable);
    } catch (e) {
      alert("Failed to fetch free slots");
    }
    setLoading(false);
  }

  async function handleFullTimetable() {
    setLoading(true);
    try {
      const resp = await fetchFullTimetable();
      setFullTimetable(resp.data.timetable);
    } catch (e) {
      alert("Failed to load full timetable");
    }
    setLoading(false);
  }

  // SAFE EXPORT STYLES (HTML2Canvas compatible)
  const exportStyle = {
    minWidth: "1000px",
    backgroundColor: "#ffffff",
    padding: "16px",
    border: "1px solid #cccccc",
    borderRadius: "8px",
    boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
    overflowX: "auto",
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

      {/* LEFT PANEL */}
      <div className="col-span-1 space-y-4">
        <IDInputModal label="Enter Faculty ID" onSubmit={handleTeacher} />

        <IDInputModal
          label="Enter Batch ID (free slots)"
          onSubmit={handleFreeSlots}
        />

        <button
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded w-full"
          onClick={handleFullTimetable}
        >
          📘 View Full Timetable (All Batches)
        </button>

        {loading && <div className="text-sm text-gray-600">Loading…</div>}
      </div>

      {/* RIGHT PANEL */}
      <div className="col-span-2 space-y-10">

        {/* =============== FACULTY TIMETABLE =============== */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-semibold text-lg">Faculty Timetable</h2>

            {timetable && (
              <DownloadPDF
                targetId="teacher-timetable"
                filename={`faculty_${currentTeacherId}_timetable.pdf`}
              />
            )}
          </div>

          <div id="teacher-timetable" className="export-safe" style={exportStyle}>
            <TimetableGrid timetable={timetable || []} />
          </div>
        </div>

        {/* =============== FREE SLOTS =============== */}
        <div>
          <h3 className="font-semibold text-lg mb-2">Batch Free Slots</h3>
          <FreeSlotsList timetable={freeSlots || []} />
        </div>

        {/* =============== FULL TIMETABLE =============== */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-semibold text-lg">Full Timetable (All Batches)</h2>

            {fullTimetable && (
              <DownloadPDF
                targetId="full-timetable"
                filename={`full_timetable.pdf`}
              />
            )}
          </div>

          <div id="full-timetable" className="export-safe" style={exportStyle}>
            <TimetableGrid timetable={fullTimetable || []} />
          </div>
        </div>

      </div>
    </div>
  );
}
