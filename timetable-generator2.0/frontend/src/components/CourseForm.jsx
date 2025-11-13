// File: src/components/CourseForm.jsx
import React, { useEffect, useState } from 'react'
import { fetchTeachers, createCourse, assignTeachers } from '../api'

export default function CourseForm({ onCreated = () => {} }) {
  const [name, setName] = useState('')
  const [creditHours, setCreditHours] = useState(4)
  const [teachers, setTeachers] = useState([])
  const [selectedTeacherIds, setSelectedTeacherIds] = useState([])
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const resp = await fetchTeachers()
        setTeachers(resp.data || [])
      } catch (e) {
        console.error('Failed to load faculties', e)
      }
    }
    load()
  }, [])

  function toggleTeacher(id) {
    setSelectedTeacherIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  async function handleSubmit(e) {
    e?.preventDefault()
    setLoading(true)
    setMsg('')

    // Build primary payload including teacher_ids (most likely backend expects this)
    const payloadWithTeachers = {
      name: name.trim(),
      credit_hours: Number(creditHours),
      teacher_ids: selectedTeacherIds,
    }

    const payloadMinimal = {
      name: name.trim(),
      credit_hours: Number(creditHours),
    }

    try {
      // First, try sending with teacher_ids (works if backend accepts assignment during creation)
      let resp = await createCourse(payloadWithTeachers)
      // If creation succeeded but teacher assignment wasn't applied (some backends ignore teacher_ids),
      // also call assign-teachers endpoint if selectedTeacherIds present and API supports it.
      if (resp?.status === 200 || resp?.status === 201) {
        const created = resp.data
        // If backend didn't attach teachers but we have teacher ids, attempt explicit assign
        if (selectedTeacherIds && selectedTeacherIds.length > 0) {
          try {
            await assignTeachers(created.id, { teacher_ids: selectedTeacherIds })
          } catch (err) {
            // ignore assign error, but surface to admin
            console.warn('assign-teachers failed (non-fatal):', err?.response?.data || err)
            setMsg('Course created, but teacher assignment returned an error.')
          }
        }

        setMsg('Course created successfully.')
        setName('')
        setCreditHours(4)
        setSelectedTeacherIds([])
        onCreated()
        setLoading(false)
        return
      }
    } catch (err) {
      // If first attempt produced 422 Unprocessable Entity, try minimal payload
      const status = err?.response?.status
      const detail = err?.response?.data || err.message
      if (status === 422) {
        try {
          const resp2 = await createCourse(payloadMinimal)
          if (resp2?.status === 200 || resp2?.status === 201) {
            const created = resp2.data
            // Now attach teachers explicitly if user selected them
            if (selectedTeacherIds && selectedTeacherIds.length > 0) {
              try {
                await assignTeachers(created.id, { teacher_ids: selectedTeacherIds })
              } catch (err2) {
                console.warn('assign-teachers failed (non-fatal):', err2?.response?.data || err2)
                setMsg('Course created; teacher assignment failed.')
              }
            }
            setMsg('Course created successfully (minimal payload).')
            setName('')
            setCreditHours(4)
            setSelectedTeacherIds([])
            onCreated()
            setLoading(false)
            return
          }
        } catch (err2) {
          console.error('Retry minimal payload failed', err2)
          setMsg('Failed creating course (retry minimal payload). See console for details.')
          setLoading(false)
          return
        }
      }

      // Other errors: show message
      console.error('Create course error', detail)
      setMsg('Failed creating course: ' + (detail?.detail || detail?.message || JSON.stringify(detail)))
      setLoading(false)
      return
    }

    setLoading(false)
  }

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-2">Add Course</h3>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm text-gray-700">Course name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Course A"
            required
            className="mt-1 p-2 border rounded w-full"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-700">Type / Credit hours</label>
          <select
            value={creditHours}
            onChange={(e) => setCreditHours(e.target.value)}
            className="mt-1 p-2 border rounded w-full"
          >
            <option value={4}>4 (Lecture)</option>
            <option value={3}>3 (Lecture)</option>
            <option value={2}>2 (Lab)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-700">Assign faculties </label>
          <div className="mt-2 grid grid-cols-2 gap-2 max-h-40 overflow-auto">
            {teachers.length === 0 && <div className="text-gray-500">No teachers yet</div>}
            {teachers.map((t) => (
              <label key={t.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedTeacherIds.includes(t.id)}
                  onChange={() => toggleTeacher(t.id)}
                />
                <span>{t.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded disabled:opacity-60"
          >
            {loading ? 'Creating…' : 'Create Course'}
          </button>
          <button
            type="button"
            onClick={() => { setName(''); setCreditHours(4); setSelectedTeacherIds([]); setMsg('') }}
            className="px-4 py-2 border rounded"
          >
            Reset
          </button>
        </div>

        {msg && <div className="text-sm text-gray-700 mt-2">{msg}</div>}
      </form>
    </div>
  )
}
