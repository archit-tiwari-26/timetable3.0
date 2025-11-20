import React from 'react'
import { Link } from 'react-router-dom'

export default function Home(){
  return (
    <div className="max-w-3xl mx-auto text-center py-16">
      <h1 className="text-3xl font-bold mb-4">Welcome to Timetable Generator</h1>
      <p className="mb-8 text-gray-600">Choose a role to continue </p>
      <div className="flex justify-center gap-4">
        <Link to="/student" className="px-6 py-3 bg-indigo-600 text-white rounded">Student</Link>
        <Link to="/teacher" className="px-6 py-3 bg-green-600 text-white rounded">Faculty</Link>
        <Link to="/admin" className="px-6 py-3 bg-gray-800 text-white rounded">Admin</Link>
      </div>

      
    </div>
  )
}