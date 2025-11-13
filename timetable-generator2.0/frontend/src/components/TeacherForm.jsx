import React, { useState } from "react";
import { createTeachers } from "../api";

export default function FacultyForm({ onCreated }) {
  const [name, setName] = useState("");
  const [maxHours, setMaxHours] = useState(16);

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await createTeachers({ name, max_hours: Number(maxHours) });
      setName("");
      setMaxHours(16);
      onCreated?.();
      alert("Faculty added!");
    } catch (err) {
      console.error(err);
      alert("Error creating faculty");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white p-4 rounded shadow mb-4">
      <h3 className="font-semibold mb-2">Add Faculty</h3>
      <div className="flex flex-col gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Faculty Name"
          className="border p-2 rounded"
          required
        />

        <input
          type="number"
          value={maxHours}
          onChange={(e) => setMaxHours(e.target.value)}
          placeholder="Max Hours"
          className="border p-2 rounded"
        />

        <button
          className="bg-green-600 text-white px-4 py-2 rounded"
          type="submit"
        >
          Create
        </button>
      </div>
    </form>
  );
}
