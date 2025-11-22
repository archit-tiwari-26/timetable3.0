# backend/seed_db.py

import requests

API = "http://localhost:8000"


def get_list(endpoint):
    try:
        r = requests.get(API + endpoint)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []


def create(endpoint, payload):
    r = requests.post(API + endpoint, json=payload)
    if r.status_code in (200, 201):
        return r.json()
    print(f"❌ Failed POST {endpoint}: {r.status_code} {r.text}")
    return None


def seed():
    print("\n🌱 SEEDING DATABASE...\n")

    # ============================
    # 1) CREATE TEACHERS
    # ============================
    print("=== TEACHERS ===")

    teacher_groups = {
        "Course A": ["Prof A1", "Prof A2", "Prof A3"],
        "Course B": ["Prof B1", "Prof B2", "Prof B3"],
        "Course C": ["Prof C1", "Prof C2"],
        "Course D": ["Prof D1", "Prof D2"],
        "Lab X": ["Prof L1", "Prof L2"],
        "Lab Y": ["Prof L3", "Prof L4"],
    }

    teacher_map = {}

    for course, tnames in teacher_groups.items():
        for name in tnames:
            res = create("/teachers/", {"name": name, "max_hours": 16})
            if res:
                teacher_map[name] = res["id"]
                print(f"✔ Created teacher: {name}")

    # ============================
    # 2) CREATE BATCHES F1–F10
    # ============================
    print("\n=== BATCHES ===")

    batch_map = {}
    for i in range(1, 11):
        name = f"F{i}"
        res = create("/batches/", {"name": name, "size": 30})
        if res:
            batch_map[name] = res["id"]
            print(f"✔ Created batch: {name}")

    # ============================
    # 3) CREATE ROOMS
    # ============================
    print("\n=== ROOMS ===")

    rooms = [
        {"name": "Lecture_X1", "capacity": 120, "room_type": "Lecture_X"},
        {"name": "Lecture_X2", "capacity": 120, "room_type": "Lecture_X"},
        {"name": "Lecture_X3", "capacity": 120, "room_type": "Lecture_X"},
        {"name": "Tutorial_Y1", "capacity": 60, "room_type": "Tutorial_Y"},
        {"name": "Tutorial_Y2", "capacity": 60, "room_type": "Tutorial_Y"},
        {"name": "Lab1", "capacity": 60, "room_type": "Lab"},
        {"name": "Lab2", "capacity": 60, "room_type": "Lab"},
    ]

    for room in rooms:
        res = create("/rooms/", room)
        if res:
            print(f"✔ Created room: {room['name']}")

    # ============================
    # 4) CREATE COURSES
    # ============================
    print("\n=== COURSES ===")

    course_data = {
        "Course A": 4,
        "Course B": 4,
        "Course C": 3,
        "Course D": 3,
        "Lab X": 2,
        "Lab Y": 2,
    }

    course_map = {}

    for cname, creds in course_data.items():
        res = create("/courses/", {"name": cname, "credit_hours": creds})
        if res:
            course_map[cname] = res["id"]
            print(f"✔ Created course: {cname}")

    # ============================
    # 5) MAP TEACHERS TO COURSES
    # ============================
    print("\n=== COURSE ↔ TEACHER MAPPING ===")

    for cname, tnames in teacher_groups.items():
        c_id = course_map[cname]
        t_ids = [teacher_map[t] for t in tnames]
        payload = {"teacher_ids": t_ids}
        r = requests.post(f"{API}/courses/{c_id}/assign-teachers/", json=payload)
        if r.status_code in (200, 201):
            print(f"✔ Linked {tnames} → {cname}")
        else:
            print(f"❌ Failed mapping for {cname}: {r.text}")

    print("\n🌿 SEEDING COMPLETE — Now run /admin/auto-prepare/ to create slots & events.\n")


if __name__ == "__main__":
    seed()
