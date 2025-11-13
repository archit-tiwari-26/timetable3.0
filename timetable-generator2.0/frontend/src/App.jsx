import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './routes/Home'
import StudentDashboard from './routes/StudentDashboard'
import TeacherDashboard from './routes/TeacherDashboard'
import AdminDashboard from './routes/AdminDashboard'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto p-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/student" element={<StudentDashboard />} />
          <Route path="/teacher" element={<TeacherDashboard />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </main>
    </div>
  )
}