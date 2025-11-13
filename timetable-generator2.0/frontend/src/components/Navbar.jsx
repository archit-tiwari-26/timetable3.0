import React from 'react'
import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-xl font-semibold">Timetable</Link>
          <Link to="/student" className="text-sm text-gray-600 hover:underline">Student</Link>
          <Link to="/teacher" className="text-sm text-gray-600 hover:underline">Faculty</Link>
          <Link to="/admin" className="text-sm text-gray-600 hover:underline">Admin</Link>
        </div>
      </div>
    </nav>
  )
}