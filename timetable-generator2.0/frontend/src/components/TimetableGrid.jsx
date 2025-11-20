import React from "react";

export default function TimetableGrid({ timetable }) {
  if (!timetable || !timetable.length) {
    return <div style={{ color: "#555" }}>No timetable data</div>;
  }

  // Required days in order (Saturday removed)
  const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

  // Convert timetable → map
  const dayMap = Object.fromEntries(timetable.map((d) => [d.day, d]));

  // Collect ALL real timeslots
  const allTimes = new Set();
  timetable.forEach((day) =>
    day.timeslots.forEach((ts) => {
      allTimes.add(`${ts.start_time}-${ts.end_time}`);
    })
  );

  // Ensure lunch slot is present (keeps lunch UI intact)
  allTimes.add("12-13");

  // Sort times
  const timeList = Array.from(allTimes).sort((a, b) => {
    const [as] = a.split("-");
    const [bs] = b.split("-");
    return Number(as) - Number(bs);
  });

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

            const isLunch = start === 12 && end === 13;

            return (
              <tr key={`row-${tk}`}>
                {/* TIME LABEL */}
                <td
                  style={{
                    border: "1px solid #999",
                    padding: "8px",
                    background: isLunch ? "#fff9c4" : "#fafafa",
                    fontFamily: "monospace",
                    fontWeight: "bold",
                  }}
                >
                  {start}:00 - {end}:00
                  {isLunch && (
                    <div style={{ fontSize: "10px", color: "#444" }}>
                      (Lunch Break)
                    </div>
                  )}
                </td>

                {/* DAY CELLS */}
                {dayOrder.map((day) => {
                  if (isLunch) {
                    // Lunch special rendering (Saturday removed, so simple)
                    return (
                      <td
                        key={`lunch-${day}-${tk}`}
                        style={{
                          border: "1px solid #999",
                          padding: "10px",
                          background: "#fffde7",
                          textAlign: "center",
                          fontWeight: "500",
                          color: "#666",
                        }}
                      >
                        Lunch Break
                      </td>
                    );
                  }

                  const dayObj = dayMap[day];
                  const ts =
                    dayObj?.timeslots.find(
                      (x) => x.start_time === start && x.end_time === end
                    ) || null;

                  return (
                    <td
                      key={`cell-${day}-${tk}`}
                      style={{
                        border: "1px solid #999",
                        padding: "8px",
                        minWidth: "200px",
                        verticalAlign: "top",
                        background: "#ffffff",
                        wordBreak: "break-word",
                      }}
                    >
                      {ts && ts.scheduled_classes.length > 0 ? (
                        ts.scheduled_classes.map((sc, idx) => (
                          <div
                            key={`${sc.event_name}-${sc.room_name}-${sc.teacher_name}-${idx}`}
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
