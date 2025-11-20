import React, { useState } from "react";

export default function EditableList({
  title,
  items,
  fields,
  onEdit,
  onDelete
}) {
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({});

  function startEdit(item) {
    setEditItem(item);
    setForm(item); // preload
  }

  function handleChange(field, value) {
    setForm(prev => ({ ...prev, [field]: value }));
  }

  async function saveEdit() {
    await onEdit(editItem.id, form);
    setEditItem(null);
  }

  return (
    <div className="bg-white rounded-xl shadow p-6 border border-gray-200">
      <h3 className="text-lg font-semibold mb-3">{title}</h3>

      <ul className="text-sm text-gray-700 space-y-2">
        {items.map(item => (
          <li key={item.id} className="flex justify-between items-center">
            <span>
              {fields.map(f => (
                <span key={f} className="mr-2">
                  <b>{f}:</b> {item[f]}
                </span>
              ))}
            </span>

            <div className="space-x-2">
              <button
                onClick={() => startEdit(item)}
                className="text-blue-600 hover:text-blue-800 text-xs"
              >
                Edit
              </button>

              <button
                onClick={() => onDelete(item.id)}
                className="text-red-600 hover:text-red-800 text-xs"
              >
                Delete
              </button>
            </div>
          </li>
        ))}

        {items.length === 0 && (
          <li className="text-gray-400">No items yet.</li>
        )}
      </ul>

      {/* -------- EDIT MODAL -------- */}
      {editItem && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center">
          <div className="bg-white p-6 rounded shadow-lg w-96">
            <h3 className="text-lg font-semibold mb-3">Edit {title}</h3>

            {fields.map(field => (
              <input
                key={field}
                value={form[field]}
                onChange={e => handleChange(field, e.target.value)}
                className="w-full mb-3 border p-2 rounded"
                placeholder={field}
              />
            ))}

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setEditItem(null)}
                className="px-4 py-2 bg-gray-200 rounded"
              >
                Cancel
              </button>

              <button
                onClick={saveEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
