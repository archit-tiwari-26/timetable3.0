import React, { useEffect, useState } from 'react'
import { fetchCourses, fetchTeachers, assignTeachers } from '../api'

export default function CourseTeacherMapping() {
  const [courses, setCourses] = useState([])
  const [teachers, setTeachers] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')
  const [selectedTeachers, setSelectedTeachers] = useState([])

  async function loadData() {
    const [c, t] = await Promise.all([fetchCourses(), fetchTeachers()])
    setCourses(c.data)
    setTeachers(t.data)
  }

  useEffect(() => { loadData() }, [])

  function toggleTeacher(id) {
    setSelectedTeachers(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  async function handleAssign() {
    if (!selectedCourse || selectedTeachers.length === 0) {
      alert('Select course and at least one teacher')
      return
    }
    try {
      await assignTeachers(selectedCourse, { teacher_ids: selectedTeachers })
      alert('Teachers assigned!')
    } catch (err) {
      console.error(err)
      alert('Failed assigning teachers')
    }
  }

  return (
    <div className="bg-white p-4 rounded shadow mt-4">
      <h3 className="font-semibold mb-2">Map Course ↔ Teachers</h3>

      <select
        className="border p-2 rounded mb-2 w-full"
        value={selectedCourse}
        onChange={e => setSelectedCourse(e.target.value)}
      >
        <option value="">Select course</option>
        {courses.map(c => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {teachers.map(t => (
          <label key={t.id} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={selectedTeachers.includes(t.id)}
              onChange={() => toggleTeacher(t.id)}
            />
            {t.name}
          </label>
        ))}
      </div>

      <button
        onClick={handleAssign}
        className="mt-3 bg-indigo-600 text-white px-4 py-2 rounded"
      >
        Assign
      </button>
    </div>
  )
}
