import React, { useState } from 'react'

export default function AdminFormGenerator({ onCreate }){
  const [numBatches, setNumBatches] = useState(10)
  const [lectureRooms, setLectureRooms] = useState(2)
  const [tutorRooms, setTutorRooms] = useState(2)
  const [labs, setLabs] = useState(2)

  function handleCreate(){
    const payload = {
      numBatches: Number(numBatches),
      lectureRooms: Number(lectureRooms),
      tutorRooms: Number(tutorRooms),
      labRooms: Number(labs)
    }
    onCreate(payload)
  }

  return (
    <div className="bg-white p-4 rounded shadow">
      <h3 className="font-semibold mb-3">Quick admin setup</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="block">
          <div className="text-sm text-gray-600">Number of batches (creates F1..Fx)</div>
          <input type="number" min={1} max={50} value={numBatches} onChange={e=>setNumBatches(e.target.value)} className="mt-1 p-2 border rounded w-full" />
        </label>
        <label className="block">
          <div className="text-sm text-gray-600">Lecture rooms (M1..Mn)</div>
          <input type="number" min={1} value={lectureRooms} onChange={e=>setLectureRooms(e.target.value)} className="mt-1 p-2 border rounded w-full" />
        </label>
        <label className="block">
          <div className="text-sm text-gray-600">Tutorial rooms (T1..Tn)</div>
          <input type="number" min={1} value={tutorRooms} onChange={e=>setTutorRooms(e.target.value)} className="mt-1 p-2 border rounded w-full" />
        </label>
        <label className="block">
          <div className="text-sm text-gray-600">Labs (L1..Ln)</div>
          <input type="number" min={1} value={labs} onChange={e=>setLabs(e.target.value)} className="mt-1 p-2 border rounded w-full" />
        </label>
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={handleCreate} className="px-4 py-2 bg-indigo-600 text-white rounded">Create entities</button>
      </div>
    </div>
  )
}
