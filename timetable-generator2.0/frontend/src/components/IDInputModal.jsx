import React, { useState } from 'react'

export default function IDInputModal({ label='Enter ID', onSubmit }){
  const [id, setId] = useState('')
  return (
    <div className="p-4 bg-white rounded shadow">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="mt-2 flex gap-2">
        <input value={id} onChange={(e)=>setId(e.target.value)} className="border p-2 rounded flex-1" placeholder="numeric id" />
        <button onClick={()=>onSubmit(id)} className="px-4 py-2 bg-indigo-600 text-white rounded">Go</button>
      </div>
    </div>
  )
}