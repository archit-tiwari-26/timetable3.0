import React, { useState } from "react";
import IDInputModal from "../components/IDInputModal";

import {
  fetchBatchTimetable,
  fetchBatchFreeSlots,
  fetchFullTimetable,
} from "../api";
import TimetableGrid from "../components/Timetablegrid";
import FreeSlotsList from "../components/FreeSlotsList";
import { downloadJSON } from "../utils/download";

export default function StudentDashboard() {
  const [timetable, setTimetable] = useState(null);
  const [freeSlots, setFreeSlots] = useState(null);
  const [fullTimetable, setFullTimetable] = useState(null);

  const [loading, setLoading] = useState(false);

  async function handleBatch(id) {
    setLoading(true);
    try {
      const resp = await fetchBatchTimetable(id);
      setTimetable(resp.data.timetable);
    } catch (e) {
      alert("Failed to fetch timetable");
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

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="col-span-1 space-y-4">
        <IDInputModal label="Enter batch ID" onSubmit={handleBatch} />
        <IDInputModal label="Enter batch ID for free slots" onSubmit={handleFreeSlots} />

        <button
          className="px-4 py-2 bg-blue-700 text-white rounded w-full"
          onClick={handleFullTimetable}
        >
          📘 View Full Timetable (All Batches)
        </button>

        <button
          className="px-4 py-2 bg-gray-800 text-white rounded w-full"
          onClick={() => fullTimetable && downloadJSON("full-timetable.json", fullTimetable)}
        >
          ⬇️ Download Full Timetable
        </button>
      </div>

      <div className="col-span-2 space-y-8">
        <div>
          <h2 className="font-semibold mb-2">Batch Timetable</h2>
          {loading ? <div>Loading...</div> : <TimetableGrid timetable={timetable || []} />}
        </div>

        <div>
          <h3 className="font-semibold">Free slots</h3>
          <FreeSlotsList timetable={freeSlots || []} />
        </div>

        <div>
          <h2 className="font-semibold mt-6">Full Timetable (All Batches)</h2>
          <TimetableGrid timetable={fullTimetable || []} />
        </div>
      </div>
    </div>
  );
}
