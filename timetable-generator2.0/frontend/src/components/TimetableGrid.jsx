import React from "react";

// timetable: [
//   { day, timeslots: [
//       { start_time, end_time, scheduled_classes: [
//           { event_name, room_name, teacher_name, batches }
//       ]}
//   ]}
// ]

export default function TimetableGrid({ timetable }) {

  if (!timetable || !timetable.length) {
    return <div style={{ color: "#555" }}>No timetable data</div>;
  }

  // Collect unique time ranges
  const allTimes = new Set();
  timetable.forEach((day) =>
    day.timeslots.forEach((ts) =>
      allTimes.add(`${ts.start_time}-${ts.end_time}`)
    )
  );

  const timeList = Array.from(allTimes).sort((a, b) => {
    const [as] = a.split("-");
    const [bs] = b.split("-");
    return Number(as) - Number(bs);
  });

  const dayOrder = timetable.map((d) => d.day);
  const dayMap = Object.fromEntries(timetable.map((d) => [d.day, d]));

  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          minWidth: "100%",
          borderCollapse: "collapse",
          border: "1px solid #999",
          background: "#ffffff",
        }}
      >
        <thead>
          <tr>
            <th
              style={{
                border: "1px solid #999",
                padding: "8px",
                background: "#f2f2f2",
                fontWeight: "bold",
              }}
            >
              Time
            </th>

            {dayOrder.map((day) => (
              <th
                key={`day-${day}`}
                style={{
                  border: "1px solid #999",
                  padding: "8px",
                  background: "#f2f2f2",
                  fontWeight: "bold",
                }}
              >
                {day}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {timeList.map((tk) => {
            const [start, end] = tk.split("-").map(Number);

            return (
              <tr key={`row-${tk}`}>
                {/* LEFT TIME LABEL */}
                <td
                  style={{
                    border: "1px solid #999",
                    padding: "8px",
                    fontFamily: "monospace",
                    background: "#fafafa",
                    fontWeight: "bold",
                  }}
                >
                  {start}:00 - {end}:00
                </td>

                {/* DAY CELLS */}
                {dayOrder.map((day) => {
                  const dayObj = dayMap[day];
                  const ts = dayObj.timeslots.find(
                    (x) =>
                      x.start_time === start && x.end_time === end
                  );

                  return (
                    <td
                      key={`cell-${day}-${tk}`}
                      style={{
                        border: "1px solid #999",
                        padding: "8px",
                        verticalAlign: "top",
                        minWidth: "200px",
                        maxWidth: "240px",
                        background: "#ffffff",
                        wordBreak: "break-word",
                      }}
                    >
                      {ts && ts.scheduled_classes.length > 0 ? (
                        ts.scheduled_classes.map((sc) => (
                          <div
                            key={`${sc.event_name}-${sc.room_name}-${sc.teacher_name}`}
                            style={{
                              border: "1px solid #ccc",
                              background: "#ffffff",
                              padding: "6px",
                              marginBottom: "6px",
                              borderRadius: "6px",
                              boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                            }}
                          >
                            <div
                              style={{
                                fontSize: "14px",
                                fontWeight: "600",
                                marginBottom: "2px",
                              }}
                            >
                              {sc.event_name}
                            </div>

                            <div
                              style={{
                                fontSize: "12px",
                                color: "#666",
                              }}
                            >
                              {sc.room_name} • {sc.teacher_name}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div
                          style={{
                            fontSize: "13px",
                            color: "#888",
                          }}
                        >
                          Free
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
