# backend/seed_db.py
import requests
import json
from pprint import pprint

API_URL = "http://localhost:8000"


def ensure_list(endpoint: str):
    """GET endpoint and return list or empty list on failure."""
    try:
        r = requests.get(f"{API_URL}{endpoint}")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def post_if_missing(endpoint: str, payload: dict, unique_key: str):
    """
    POST payload to endpoint if an existing object with unique_key doesn't exist.
    Returns the existing or created object (or None on failure).
    """
    existing = ensure_list(endpoint.rsplit("/", 1)[0] + "/")
    # endpoint param is full path e.g. "/teachers/"
    found = next((x for x in existing if x.get(unique_key) == payload.get(unique_key)), None)
    if found:
        return found

    try:
        r = requests.post(f"{API_URL}{endpoint}", json=payload)
        if r.status_code in (200, 201):
            return r.json()
        else:
            print(f"⚠️ POST {endpoint} failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"⚠️ Exception posting to {endpoint}: {e}")
    return None


def seed_data():
    print("---- 🌱 STARTING DATABASE SEED ----")

    # 1) Basic connectivity check
    try:
        r = requests.get(API_URL + "/")
        if r.status_code != 200:
            print(f"❌ API returned non-200: {r.status_code}")
            return
    except Exception as e:
        print(f"❌ Could not connect to {API_URL}: {e}")
        return

    # --- TEACHERS ---
    print("\n=== TEACHERS ===")
    teacher_names = [
    # Course A team
    "Prof. A1", "Prof. A2", "Prof. A3",
    # Course B team
    "Prof. B1", "Prof. B2", "Prof. B3",
    # Course C team
    "Prof. C1", "Prof. C2",
    # Lab teams
    "Prof. L1", "Prof. L2", "Prof. L3", "Prof. L4"
]

    teachers = ensure_list("/teachers/")
    created_teachers = []
    for name in teacher_names:
        obj = next((t for t in teachers if t["name"] == name), None)
        if obj:
            created_teachers.append(obj)
            print(f"ℹ️ Teacher exists: {name}")
            continue
        payload = {"name": name, "max_hours": 16}
        res = requests.post(f"{API_URL}/teachers/", json=payload)
        if res.status_code in (200, 201):
            print(f"✅ Created teacher: {name}")
            created_teachers.append(res.json())
        else:
            # try to fetch freshly (race / validation differences)
            teachers = ensure_list("/teachers/")
            obj = next((t for t in teachers if t["name"] == name), None)
            if obj:
                created_teachers.append(obj)
                print(f"ℹ️ Teacher present after re-check: {name}")
            else:
                print(f"❌ Failed to create teacher {name}: {res.status_code} {res.text}")

    teachers = created_teachers

    # --- BATCHES ---
    print("\n=== BATCHES ===")
    batches = ensure_list("/batches/")
    created_batches = []
    for i in range(1, 11):
        name = f"F{i}"
        obj = next((b for b in batches if b["name"] == name), None)
        if obj:
            created_batches.append(obj)
            print(f"ℹ️ Batch exists: {name}")
            continue
        payload = {"name": name, "size": 30}
        res = requests.post(f"{API_URL}/batches/", json=payload)
        if res.status_code in (200, 201):
            print(f"✅ Created batch: {name}")
            created_batches.append(res.json())
        else:
            batches = ensure_list("/batches/")
            obj = next((b for b in batches if b["name"] == name), None)
            if obj:
                created_batches.append(obj)
                print(f"ℹ️ Batch present after re-check: {name}")
            else:
                print(f"❌ Failed to create batch {name}: {res.status_code} {res.text}")

    batches = created_batches

    # --- ROOMS ---
    print("\n=== ROOMS ===")
    room_data = [
        {"name": "Lecture_X1", "capacity": 100, "room_type": "Lecture_X"},
        {"name": "Lecture_X2", "capacity": 100, "room_type": "Lecture_X"},
        {"name": "Tutorial_Y1", "capacity": 60, "room_type": "Tutorial_Y"},
        {"name": "Tutorial_Y2", "capacity": 60, "room_type": "Tutorial_Y"},
        {"name": "Lab1", "capacity": 60, "room_type": "Lab"},
        {"name": "Lab2", "capacity": 60, "room_type": "Lab"},
    ]
    rooms = ensure_list("/rooms/")
    created_rooms = []
    for rd in room_data:
        obj = next((r for r in rooms if r["name"] == rd["name"]), None)
        if obj:
            created_rooms.append(obj)
            print(f"ℹ️ Room exists: {rd['name']}")
            continue
        res = requests.post(f"{API_URL}/rooms/", json=rd)
        if res.status_code in (200, 201):
            created_rooms.append(res.json())
            print(f"✅ Created room: {rd['name']}")
        else:
            rooms = ensure_list("/rooms/")
            obj = next((r for r in rooms if r["name"] == rd["name"]), None)
            if obj:
                created_rooms.append(obj)
                print(f"ℹ️ Room present after re-check: {rd['name']}")
            else:
                print(f"❌ Failed to create room {rd['name']}: {res.status_code} {res.text}")

    # --- TIMESLOTS ---
    # Important: create Lecture (1h) and Lab (2h) slots.
    # NOTE: solver currently checks timeslot.slot_type == 'Lecture' for duration==1
    # and 'Lab' for duration==2. To avoid tutorial filtering issues we keep tutorials
    # as Lecture-duration slots (solver expects Lecture for duration 1).
    print("\n=== TIMESLOTS ===")
    timeslots = ensure_list("/timeslots/")
    timeslot_keys = {(ts["day"], ts["start_time"], ts["end_time"], ts["duration"], ts["slot_type"]) for ts in timeslots}

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Lecture slots: 8-17 (1 hour)
    for day in days:
        for hour in range(8, 17):  # 8AM–5PM
            key = (day, hour, hour + 1, 1, "Lecture")
            if key in timeslot_keys:
                continue
            payload = {"day": day, "start_time": hour, "end_time": hour + 1, "duration": 1, "slot_type": "Lecture"}
            r = requests.post(f"{API_URL}/timeslots/", json=payload)
            if r.status_code in (200, 201):
                timeslot_keys.add(key)

    # Lab slots: 2-hour slots from 8-16 stepping by 2
    for day in days:
        for hour in range(8, 16, 2):  # 8-10,10-12,...14-16
            key = (day, hour, hour + 2, 2, "Lab")
            if key in timeslot_keys:
                continue
            payload = {"day": day, "start_time": hour, "end_time": hour + 2, "duration": 2, "slot_type": "Lab"}
            r = requests.post(f"{API_URL}/timeslots/", json=payload)
            if r.status_code in (200, 201):
                timeslot_keys.add(key)

    print("✅ Timeslots ensured (Lecture 1h + Lab 2h).")

    # --- COURSES ---
    print("\n=== COURSES ===")
    course_data = [
        {"name": "Course A", "credit_hours": 4},
        {"name": "Course B", "credit_hours": 4},
        {"name": "Course C", "credit_hours": 3},
        {"name": "Lab 1", "credit_hours": 2},
        {"name": "Lab 2", "credit_hours": 2},
    ]
    courses = ensure_list("/courses/")
    created_courses = []
    for cd in course_data:
        obj = next((c for c in courses if c["name"] == cd["name"]), None)
        if obj:
            created_courses.append(obj)
            print(f"ℹ️ Course exists: {cd['name']}")
            continue
        res = requests.post(f"{API_URL}/courses/", json=cd)
        if res.status_code in (200, 201):
            created_courses.append(res.json())
            print(f"✅ Created course: {cd['name']}")
        else:
            courses = ensure_list("/courses/")
            obj = next((c for c in courses if c["name"] == cd["name"]), None)
            if obj:
                created_courses.append(obj)
                print(f"ℹ️ Course present after re-check: {cd['name']}")
            else:
                print(f"❌ Failed to create course {cd['name']}: {res.status_code} {res.text}")

    courses = created_courses
    course_map = {c["name"]: c["id"] for c in courses}

    # --- LINK TEACHERS <-> COURSES ---
    print("\n=== LINK TEACHERS → COURSES ===")
    course_teacher_map = {
    "Course A": ["Prof. A1", "Prof. A2", "Prof. A3"],
    "Course B": ["Prof. B1", "Prof. B2", "Prof. B3"],
    "Course C": ["Prof. C1", "Prof. C2"],
    "Lab 1": ["Prof. L1", "Prof. L3"],
    "Lab 2": ["Prof. L2", "Prof. L4"],
}

    for cname, tnames in course_teacher_map.items():
        if cname not in course_map:
            print(f"⚠️ Course not found locally: {cname}")
            continue
        course_id = course_map[cname]
        # fetch fresh teacher list (in case created above)
        teachers_full = ensure_list("/teachers/")
        teacher_ids = [t["id"] for t in teachers_full if t["name"] in tnames]
        if not teacher_ids:
            print(f"⚠️ No teacher IDs found for {cname} -> {tnames}")
            continue
        payload = {"teacher_ids": teacher_ids}
        r = requests.post(f"{API_URL}/courses/{course_id}/assign-teachers/", json=payload)
        if r.status_code in (200, 201):
            print(f"✅ Linked {tnames} → {cname}")
        else:
            # sometimes assign returns 400 if nothing changed; print response
            print(f"⚠️ Assign teachers returned {r.status_code}: {r.text}")

    # --- CREATE SCHEDULABLE EVENTS ---
    print("\n=== SCHEDULABLE EVENTS ===")
    # Refresh batches & courses data
    batches = ensure_list("/batches/")
    courses = ensure_list("/courses/")
    course_map = {c["name"]: c["id"] for c in courses}
    events = []

    # For pairwise combination F1+F2, F3+F4, ...
    for i in range(0, len(batches), 2):
        if i + 1 >= len(batches):
            break
        b1 = batches[i]
        b2 = batches[i + 1]
        batch_ids = [b1["id"], b2["id"]]
        total_size = b1["size"] + b2["size"]

        # Lectures
        for cname, n in [("Course A", 3), ("Course B", 3), ("Course C", 3)]:
            for j in range(1, n + 1):
                events.append({
                    "name": f"{cname} Lecture {j} ({b1['name']}+{b2['name']})",
                    "duration": 1,
                    "required_room_type": "Lecture_X",
                    "total_size": total_size,
                    "course_id": course_map[cname],
                    "batch_ids": batch_ids
                })

        # Labs (2h)
        for lname in ["Lab 1", "Lab 2"]:
            events.append({
                "name": f"{lname} ({b1['name']}+{b2['name']})",
                "duration": 2,
                "required_room_type": "Lab",
                "total_size": total_size,
                "course_id": course_map[lname],
                "batch_ids": batch_ids
            })

    # Tutorials (1 per batch) -- we leave slot_type as Lecture (1h) so solver accepts them
    for b in batches:
        for cname in ["Course A", "Course B", "Course C"]:
            events.append({
                "name": f"{cname} Tutorial ({b['name']})",
                "duration": 1,
                "required_room_type": "Tutorial_Y",
                "total_size": b["size"],
                "course_id": course_map[cname],
                "batch_ids": [b["id"]]
            })

    print(f"→ Attempting to create {len(events)} events...")
    success = fail = 0
    for ev in events:
        r = requests.post(f"{API_URL}/schedulable-events/", json=ev)
        if r.status_code in (200, 201):
            success += 1
        else:
            fail += 1
            msg = r.text if r is not None else "No response"
            print(f"❌ Event failed: {ev['name']} -> {r.status_code} {msg}")

    print(f"✅ Events created: {success}, failed: {fail}")

    # --- VERIFY COURSE ↔ TEACHERS MAPPING ---
    print("\n=== VERIFY COURSE ↔ TEACHERS ===")
    try:
        verify = requests.get(f"{API_URL}/debug/courses/teachers")
        if verify.status_code == 200:
            data = verify.json()
            for cname, tnames in data.items():
                print(f"{cname} -> {tnames}")
        else:
            print(f"⚠️ Debug endpoint returned {verify.status_code}")
    except Exception as e:
        print(f"⚠️ Could not verify course-teacher mapping: {e}")

    print("\n---- 🌿 SEEDING COMPLETE ----")


if __name__ == "__main__":
    seed_data()
