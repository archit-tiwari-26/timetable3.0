import React, { useState } from "react";

import IDInputModal from "../components/IDInputModal";
import TimetableGrid from "../components/Timetablegrid";
import FreeSlotsList from "../components/FreeSlotsList";
import DownloadPDF from "../components/DownloadPDF";

import {
  fetchBatchTimetable,
  fetchBatchFreeSlots,
  fetchFullTimetable,
} from "../api";

export default function StudentDashboard() {
  const [timetable, setTimetable] = useState(null);
  const [freeSlots, setFreeSlots] = useState(null);
  const [fullTimetable, setFullTimetable] = useState(null);

  const [loading, setLoading] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState(null);

  async function handleBatch(id) {
    setLoading(true);
    try {
      const resp = await fetchBatchTimetable(id);
      setTimetable(resp.data.timetable);
      setCurrentBatchId(id);
    } catch (e) {
      alert("Failed to fetch batch timetable");
    }
    setLoading(false);
  }

  async function handleFreeSlots(id) {
    setLoading(true);
    try {
      const resp = await fetchBatchFreeSlots(id);
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
      alert("Failed to fetch full timetable");
    }
    setLoading(false);
  }

  // SAFE export styling (same as TeacherDashboard)
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

      {/* LEFT SIDE CONTROLS */}
      <div className="col-span-1 space-y-4">
        <IDInputModal label="Enter Batch ID" onSubmit={handleBatch} />
        <IDInputModal label="Enter Batch ID (Free Slots)" onSubmit={handleFreeSlots} />

        <button
          className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded w-full"
          onClick={handleFullTimetable}
        >
          📘 View Full Timetable (All Batches)
        </button>

        {loading && <div className="text-gray-600 text-sm">Loading…</div>}
      </div>

      {/* RIGHT SIDE CONTENT */}
      <div className="col-span-2 space-y-10">

        {/* =============== BATCH TIMETABLE =============== */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-semibold text-lg">Batch Timetable</h2>

            {timetable && (
              <DownloadPDF
                targetId="batch-timetable"
                filename={`batch_${currentBatchId}_timetable.pdf`}
              />
            )}
          </div>

          <div id="batch-timetable" className="export-safe" style={exportStyle}>
            <TimetableGrid timetable={timetable || []} />
          </div>
        </div>

        {/* =============== FREE SLOTS =============== */}
        <div>
          <h3 className="font-semibold text-lg mb-2">Free Slots</h3>
          <FreeSlotsList timetable={freeSlots || []} />
        </div>

        {/* =============== FULL TIMETABLE =============== */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="font-semibold text-lg">Full Timetable (All Batches)</h2>

            {fullTimetable && (
              <DownloadPDF
                targetId="full-timetable"
                filename="full_timetable.pdf"
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
