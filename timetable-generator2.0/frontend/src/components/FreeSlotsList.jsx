import React from 'react'

// Expects timetable same format as FormattedTimetableResponse but timeslots are contiguous free ranges
export default function FreeSlotsList({ timetable }){
  if(!timetable) return null
  return (
    <div>
      {timetable.map(day=> (
        <div key={day.day} className="mb-4">
          <h3 className="font-semibold">{day.day}</h3>
          <div className="flex flex-wrap gap-2 mt-2">
            {day.timeslots.length===0 && <div className="text-gray-500">No free slots</div>}
            {day.timeslots.map((ts,i)=> (
              <div key={i} className="px-3 py-2 bg-white rounded shadow text-sm">
                {ts.start_time}:00 - {ts.end_time}:00
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

