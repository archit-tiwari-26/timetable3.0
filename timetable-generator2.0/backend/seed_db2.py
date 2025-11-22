# backend/solver.py
from ortools.sat.python import cp_model
import statistics
from collections import defaultdict, Counter

def create_timetable_solver(db_data, time_limit_seconds: float = 120.0, debug: bool = False):
    """
    CP-SAT solver that:
    - Assigns each event to (teacher, room, timeslot)
      where the teacher must be eligible for the event.course.
    - Respects room capacity/type, timeslot duration/type.
    - Prevents teacher/batch/room conflicts including overlapping timeslots.
    - Enforces teacher weekly workload (sum of assigned event durations <= max_hours).
    Returns:
        dict: mapping event_id -> (teacher_id, room_id, timeslot_id)
        or None if no feasible solution found.

    New param:
        debug (bool): if True, prints detailed diagnostics during domain-building
                      and when infeasible.
    Required db_data keys:
        - events: list of SchedulableEvent ORM objects (should include .course and .batches)
        - rooms: list of Room ORM objects
        - timeslots: list of Timeslot ORM objects
        - teachers: list of Teacher ORM objects
    """

    events = db_data.get("events", []) or []
    rooms = db_data.get("rooms", []) or []
    timeslots = db_data.get("timeslots", []) or []
    teachers = db_data.get("teachers", []) or []

    # quick sanity
    if not events:
        if debug: print("Solver: no events provided.")
        return {}
    if not rooms:
        if debug: print("Solver: no rooms provided.")
        return None
    if not timeslots:
        if debug: print("Solver: no timeslots provided.")
        return None
    if not teachers and debug:
        print("Solver: warning - no teachers list provided (will rely on course.teachers).")

    # convenience lookups
    events_by_id = {e.id: e for e in events}
    teachers_by_id = {t.id: t for t in teachers}
    rooms_by_id = {r.id: r for r in rooms}
    timeslots_by_id = {ts.id: ts for ts in timeslots}

    if debug:
        print("=== Solver debug: DB summary ===")
        print(f"Events: {len(events)}, Rooms: {len(rooms)}, Timeslots: {len(timeslots)}, Teachers: {len(teachers)}")
        room_types = Counter(r.room_type for r in rooms)
        ts_types = Counter(ts.slot_type for ts in timeslots)
        print(f"Room types: {dict(room_types)}")
        print(f"Timeslot slot_types: {dict(ts_types)}")
        print("===============================")

    model = cp_model.CpModel()

    # var_matrix[(event_id, teacher_id, room_id, timeslot_id)] = BoolVar
    var_matrix = {}
    event_vars_map = {event.id: [] for event in events}
    event_candidate_counts = {}

    # Additional debug tracking
    rejection_reasons = defaultdict(Counter)  # event_id -> Counter(reason -> count)
    event_candidate_keys = defaultdict(list)

    # Pre-index rooms and timeslots by useful attributes for fast checks
    rooms_by_type = defaultdict(list)
    for r in rooms:
        rooms_by_type[r.room_type].append(r)

    timeslots_by_duration_and_type = defaultdict(list)
    for ts in timeslots:
        key = (ts.duration, ts.slot_type)
        timeslots_by_duration_and_type[key].append(ts)

    # Build domain: only combos that obey hard filters
    for event in events:
        course = getattr(event, "course", None)
        if not course:
            if debug:
                print(f"Error: Event {event.id} ('{getattr(event,'name',None)}') has no course relationship.")
            return None

        eligible_teachers = getattr(course, "teachers", []) or []
        if not eligible_teachers:
            if debug:
                print(f"Error: No teachers assigned to course '{course.name}' (event {event.id}).")
            return None

        added_any = False
        # For debugging: possible rooms of right type and capacity
        possible_rooms = [r for r in rooms_by_type.get(event.required_room_type, []) if r.capacity >= event.total_size]
        possible_ts = []
        # choose slot_type corresponding to duration: heuristics
        expected_slot_type = 'Lecture' if event.duration == 1 else 'Lab' if event.duration == 2 else None
        if expected_slot_type:
            possible_ts = timeslots_by_duration_and_type.get((event.duration, expected_slot_type), [])
        else:
            # fallback: any timeslot matching duration
            possible_ts = [ts for ts in timeslots if ts.duration == event.duration]

        # build combos
        for teacher in eligible_teachers:
            t_id = getattr(teacher, "id", None)
            if t_id is None:
                rejection_reasons[event.id]["teacher_missing_id"] += 1
                continue

            # optional: if caller passed teachers list, filter to only those
            if teachers and t_id not in teachers_by_id:
                rejection_reasons[event.id]["teacher_not_in_passed_teachers"] += 1
                continue

            # iterate candidate rooms/timeslots (use prefiltered lists)
            for room in possible_rooms:
                for timeslot in possible_ts:
                    # final check (again) for safety: duration vs slot_type
                    if event.duration != timeslot.duration:
                        rejection_reasons[event.id]["timeslot_duration_mismatch"] += 1
                        continue
                    if expected_slot_type and timeslot.slot_type != expected_slot_type:
                        rejection_reasons[event.id]["timeslot_type_mismatch"] += 1
                        continue

                    # valid candidate -> create bool var
                    var = model.NewBoolVar(f"e{event.id}_t{t_id}_r{room.id}_s{timeslot.id}")
                    key = (event.id, t_id, room.id, timeslot.id)
                    var_matrix[key] = var
                    event_vars_map[event.id].append(var)
                    event_candidate_keys[event.id].append(key)
                    added_any = True

        candidate_count = len(event_candidate_keys[event.id])
        event_candidate_counts[event.id] = candidate_count

        if debug:
            print(f"Event {event.id} ('{getattr(event,'name',None)}') candidates: {candidate_count}")
            if candidate_count == 0:
                # detailed diagnostics for this event
                print("  --- DIAGNOSTIC for event with ZERO candidates ---")
                print(f"  Course: {course.name}")
                print(f"  Assigned course.teachers: {[getattr(t,'name',None) for t in getattr(course,'teachers',[])]}")
                print(f"  Required room type: {event.required_room_type}, total_size: {event.total_size}")
                print(f"  Matching rooms (by type & capacity >= size): {[(r.name, r.capacity) for r in possible_rooms]}")
                print(f"  Matching timeslots (duration={event.duration}, slot_type={expected_slot_type}): "
                      f"{[(ts.id, ts.day, ts.start_time) for ts in possible_ts][:10]} (showing up to 10)")
                # show teachers passed vs teachers in DB_data
                if teachers:
                    print(f"  Teachers passed to solver (ids): {list(teachers_by_id.keys())[:20]}")
                # counts of various rejection reasons
                print("  Rejection reasons summary:", dict(rejection_reasons[event.id]))
                print("  -------------------------------------------------")
                # return early — event can't be scheduled at all
                return None

    # --- after domain building debug summary ---
    if debug:
        counts = list(event_candidate_counts.values())
        if counts:
            print("=== Domain statistics ===")
            print(f"Min candidates: {min(counts)}, Max: {max(counts)}, Mean: {statistics.mean(counts):.2f}")
            try:
                print(f"Median: {statistics.median(counts):.1f}")
            except Exception:
                pass
            small = sorted([(eid, cnt) for eid, cnt in event_candidate_counts.items()], key=lambda x: x[1])[:10]
            print("10 smallest domains (event_id, candidates):", small)
            # Top global rejection reasons
            agg_reasons = Counter()
            for ev, c in rejection_reasons.items():
                agg_reasons.update(c)
            print("Aggregate rejection reasons (top 10):", agg_reasons.most_common(10))
            print("=========================")

    # --- Core constraints ---

    # 1) Each event must be scheduled exactly once (one teacher + one room + one timeslot).
    for event_id, vars_list in event_vars_map.items():
        if not vars_list:
            if debug:
                print(f"Error: Event {event_id} has empty domain — aborting.")
            return None
        model.AddExactlyOne(vars_list)

    # Helper: function to test overlap of two timeslots
    def timeslots_overlap(ts1, ts2):
        if ts1.day != ts2.day:
            return False
        # intervals [start, end) overlap if start1 < end2 and start2 < end1
        return (ts1.start_time < ts2.end_time) and (ts2.start_time < ts1.end_time)

    # Build reverse index: resource -> list of (key, var, timeslot_obj, event_id)
    # We'll create lists for rooms, teachers and batches and then add pairwise non-overlap constraints.
    room_index = defaultdict(list)
    teacher_index = defaultdict(list)
    batch_index = defaultdict(list)

    for (event_id, teacher_id, room_id, timeslot_id), var in var_matrix.items():
        ts = timeslots_by_id[timeslot_id]
        room_index[room_id].append((event_id, var, ts))
        teacher_index[teacher_id].append((event_id, var, ts))
        # event -> batches
        for batch in getattr(events_by_id[event_id], "batches", []):
            b_id = getattr(batch, "id", None)
            if b_id is not None:
                batch_index[b_id].append((event_id, var, ts))

    # 2) No two events in the same room at overlapping timeslots.
    for room_id, entries in room_index.items():
        n = len(entries)
        for i in range(n):
            e1_id, var1, ts1 = entries[i]
            for j in range(i + 1, n):
                e2_id, var2, ts2 = entries[j]
                if timeslots_overlap(ts1, ts2):
                    model.Add(var1 + var2 <= 1)

    # 3) No teacher in two overlapping timeslots.
    for teacher_id, entries in teacher_index.items():
        n = len(entries)
        for i in range(n):
            e1_id, var1, ts1 = entries[i]
            for j in range(i + 1, n):
                e2_id, var2, ts2 = entries[j]
                if timeslots_overlap(ts1, ts2):
                    model.Add(var1 + var2 <= 1)

    # 4) No batch in two overlapping timeslots.
    for batch_id, entries in batch_index.items():
        n = len(entries)
        for i in range(n):
            e1_id, var1, ts1 = entries[i]
            for j in range(i + 1, n):
                e2_id, var2, ts2 = entries[j]
                if timeslots_overlap(ts1, ts2):
                    model.Add(var1 + var2 <= 1)

    # --- Teacher workload constraint ---
    # sum(duration * assigned_vars) <= teacher.max_hours
    for teacher in teachers:
        t_id = teacher.id
        teacher_vars = []
        teacher_weights = []
        for (event_id, teacher_id, room_id, timeslot_id), var in var_matrix.items():
            if teacher_id == t_id:
                teacher_vars.append(var)
                event = events_by_id[event_id]
                teacher_weights.append(event.duration)

        if teacher_vars:
            model.Add(
                cp_model.LinearExpr.WeightedSum(teacher_vars, teacher_weights) <= getattr(teacher, "max_hours", 16)
            )

    # --- Solve ---
        # --- Solve ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds

    if debug:
        print("Solving timetable with CP-SAT... (debug ON)")
    else:
        print("Solving timetable with CP-SAT...")

    try:
        status = solver.Solve(model)
    except Exception as e:
        if debug:
            print("Solver raised exception:", e)
        return None

    # normalize status name
    try:
        status_name = solver.StatusName(status)
    except Exception:
        status_name = str(status)

    print("Solver finished with status:", status_name)

    # --- ✅ Conflict Detector Helper ---
    def detect_conflicts(solution):
        """Check for overlapping resource usage among rooms, teachers, and batches."""
        conflicts = {"teachers": [], "rooms": [], "batches": []}

        # Build reverse indexes from solution
        assignment = {}
        for e_id, (t_id, r_id, ts_id) in solution.items():
            e = events_by_id[e_id]
            ts = timeslots_by_id[ts_id]
            assignment[e_id] = {"event": e, "teacher": t_id, "room": r_id, "ts": ts}

        def overlap(ts1, ts2):
            return ts1.day == ts2.day and (ts1.start_time < ts2.end_time and ts2.start_time < ts1.end_time)

        # === Teacher conflicts ===
        for t_id in teachers_by_id:
            items = [(aid, a) for aid, a in assignment.items() if a["teacher"] == t_id]
            for i in range(len(items)):
                e1_id, a1 = items[i]
                for j in range(i + 1, len(items)):
                    e2_id, a2 = items[j]
                    if overlap(a1["ts"], a2["ts"]):
                        conflicts["teachers"].append({
                            "teacher": teachers_by_id[t_id].name,
                            "day": a1["ts"].day,
                            "events": [a1["event"].name, a2["event"].name],
                            "time_ranges": [
                                f"{a1['ts'].start_time}-{a1['ts'].end_time}",
                                f"{a2['ts'].start_time}-{a2['ts'].end_time}"
                            ]
                        })

        # === Room conflicts ===
        for r_id in rooms_by_id:
            items = [(aid, a) for aid, a in assignment.items() if a["room"] == r_id]
            for i in range(len(items)):
                e1_id, a1 = items[i]
                for j in range(i + 1, len(items)):
                    e2_id, a2 = items[j]
                    if overlap(a1["ts"], a2["ts"]):
                        conflicts["rooms"].append({
                            "room": rooms_by_id[r_id].name,
                            "day": a1["ts"].day,
                            "events": [a1["event"].name, a2["event"].name],
                            "time_ranges": [
                                f"{a1['ts'].start_time}-{a1['ts'].end_time}",
                                f"{a2['ts'].start_time}-{a2['ts'].end_time}"
                            ]
                        })

        # === Batch conflicts ===
        for b in {b.id for e in events for b in getattr(e, "batches", [])}:
            items = [(aid, a) for aid, a in assignment.items() if any(bb.id == b for bb in a["event"].batches)]
            for i in range(len(items)):
                e1_id, a1 = items[i]
                for j in range(i + 1, len(items)):
                    e2_id, a2 = items[j]
                    if overlap(a1["ts"], a2["ts"]):
                        conflicts["batches"].append({
                            "batch": b,
                            "day": a1["ts"].day,
                            "events": [a1["event"].name, a2["event"].name],
                            "time_ranges": [
                                f"{a1['ts'].start_time}-{a1['ts'].end_time}",
                                f"{a2['ts'].start_time}-{a2['ts'].end_time}"
                            ]
                        })

        return conflicts

    # --- Handle results ---
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution = {}
        for (event_id, teacher_id, room_id, timeslot_id), var in var_matrix.items():
            try:
                val = solver.Value(var)
            except Exception:
                val = 0
            if val == 1:
                solution[event_id] = (teacher_id, room_id, timeslot_id)

        if debug:
            print(f"✅ Found solution: {len(solution)} events scheduled.")

            # Run conflict check
            conflicts = detect_conflicts(solution)
            if any(conflicts.values()):
                print("\n⚠️ Detected scheduling conflicts:")
                for ctype, clist in conflicts.items():
                    if clist:
                        print(f"--- {ctype.upper()} ---")
                        for c in clist:
                            print(f"{ctype[:-1].capitalize()}: {c.get(ctype[:-1])}, Day: {c['day']}")
                            print(f"  Events: {c['events']}")
                            print(f"  Times: {c['time_ranges']}")
            else:
                print("✅ No conflicts detected! 🎉")

        return solution

    # --- If infeasible or unknown ---
    if debug:
        print("No feasible solution found — diagnostic snapshot:")
        domain_sizes = {eid: len(keys) for eid, keys in event_candidate_keys.items()}
        sizes = sorted(domain_sizes.items(), key=lambda x: x[1])
        print("Event domain sizes (smallest 20):", sizes[:20])
        ts_by_type_duration = defaultdict(set)
        for ts in timeslots:
            ts_by_type_duration[(ts.duration, ts.slot_type)].add(ts.id)
        room_count_by_type = {rt: len(lst) for rt, lst in rooms_by_type.items()}
        print("Rooms per type:", room_count_by_type)
        print("Timeslots per (duration,slot_type):",
              {k: len(v) for k, v in ts_by_type_duration.items()})
        req_by_type = defaultdict(list)
        for ev in events:
            req_by_type[ev.required_room_type].append(ev.id)
        print("Events per required_room_type (counts):",
              {k: len(v) for k, v in req_by_type.items()})
        teacher_upper = {}
        for t in (teachers or []):
            eligible_events = [e for e in events if any(getattr(cand, "id", None) == t.id for cand in getattr(e.course, "teachers", []))]
            teacher_upper[t.id] = {
                "name": getattr(t, "name", None),
                "max_hours": getattr(t, "max_hours", 16),
                "eligible_event_durations_sum": sum(e.duration for e in eligible_events)
            }
        print("Teacher rough capacity snapshot (id -> info):")
        for tid, info in teacher_upper.items():
            print(f"  T{tid}: {info}")
        print("Aggregate rejection reasons (top 30):")
        agg_reasons = Counter()
        for ev, c in rejection_reasons.items():
            agg_reasons.update(c)
        print(agg_reasons.most_common(30))

    print("No feasible solution found.")
    return None