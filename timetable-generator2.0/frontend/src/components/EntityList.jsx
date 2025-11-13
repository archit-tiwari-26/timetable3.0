import React from 'react'

export default function EntityList({ title, items=[] }){
  return (
    <div className="bg-white rounded shadow p-4">
      <h4 className="font-semibold mb-2">{title}</h4>
      <ul className="text-sm text-gray-700">
        {items.map((it,i)=> <li key={i}>{it}</li>)}
      </ul>
    </div>
  )
}