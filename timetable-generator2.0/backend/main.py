# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from collections import defaultdict
from typing import List
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import os
import models
import schemas
import solver
from models import (
    SessionLocal, engine, Base,
    Teacher, Batch, Room, Timeslot,
    SchedulableEvent, ScheduledClass, event_batches_table
)

# --- Database Setup ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Timetable Generator API")

# --- CORS ---
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Root ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Timetable Generator API"}


# ==========================================================
# ===============  BASIC CRUD ENDPOINTS  ===================
# ==========================================================

# --- TEACHERS ---
@app.post("/teachers/", response_model=schemas.Teacher)
def create_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    db_teacher = db.query(Teacher).filter(Teacher.name == teacher.name).first()
    if db_teacher:
        return db_teacher
    new_teacher = Teacher(**teacher.model_dump(exclude_unset=True))
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    return new_teacher

@app.get("/teachers/", response_model=List[schemas.Teacher])
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()


# --- BATCHES ---
@app.post("/batches/", response_model=schemas.Batch)
def create_batch(batch: schemas.BatchCreate, db: Session = Depends(get_db)):
    existing = db.query(Batch).filter(Batch.name == batch.name).first()
    if existing:
        return existing
    new_batch = Batch(**batch.model_dump())
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch

@app.get("/batches/", response_model=List[schemas.Batch])
def get_batches(db: Session = Depends(get_db)):
    return db.query(Batch).all()


# --- ROOMS ---
@app.post("/rooms/", response_model=schemas.Room)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter(Room.name == room.name).first()
    if existing:
        return existing
    new_room = Room(**room.model_dump())
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room

@app.get("/rooms/", response_model=List[schemas.Room])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


# --- TIMESLOTS ---
@app.post("/timeslots/", response_model=schemas.Timeslot)
def create_timeslot(timeslot: schemas.TimeslotCreate, db: Session = Depends(get_db)):
    existing = db.query(Timeslot).filter(
        Timeslot.day == timeslot.day,
        Timeslot.start_time == timeslot.start_time,
        Timeslot.end_time == timeslot.end_time
    ).first()
    if existing:
        return existing
    new_ts = Timeslot(**timeslot.model_dump())
    db.add(new_ts)
    db.commit()
    db.refresh(new_ts)
    return new_ts

@app.get("/timeslots/", response_model=List[schemas.Timeslot])
def get_timeslots(db: Session = Depends(get_db)):
    return db.query(Timeslot).all()


# --- COURSES ---
@app.post("/courses/", response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    db_course = models.Course(name=course.name, credit_hours=course.credit_hours)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/courses/", response_model=List[schemas.Course])
def get_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()

@app.post("/courses/{course_id}/assign-teachers/")
def assign_teachers_to_course(course_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    teacher_ids = payload.get("teacher_ids", [])
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    teachers = db.query(models.Teacher).filter(models.Teacher.id.in_(teacher_ids)).all()
    if not teachers:
        raise HTTPException(status_code=404, detail="No valid teachers found")

    for teacher in teachers:
        if teacher not in course.teachers:
            course.teachers.append(teacher)

    db.add(course)
    db.commit()
    db.refresh(course)
    db.flush()
    return {"message": f"Assigned {len(teachers)} teachers to {course.name}"}


# --- SCHEDULABLE EVENTS ---
@app.post("/schedulable-events/", response_model=schemas.SchedulableEvent)
def create_schedulable_event(event: schemas.SchedulableEventCreate, db: Session = Depends(get_db)):
    course = db.get(models.Course, event.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    batches = db.query(models.Batch).filter(models.Batch.id.in_(event.batch_ids)).all()
    if len(batches) != len(event.batch_ids):
        raise HTTPException(status_code=404, detail="One or more batch IDs not found")

    db_event = models.SchedulableEvent(
        name=event.name,
        duration=event.duration,
        required_room_type=event.required_room_type,
        total_size=event.total_size,
        course_id=event.course_id,
    )
    db_event.batches = batches
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.get("/schedulable-events/", response_model=List[schemas.SchedulableEvent])
def get_schedulable_events(db: Session = Depends(get_db)):
    return db.query(SchedulableEvent).all()


# --- DEBUG ---
@app.get("/debug/courses/teachers")
def debug_courses_teachers(db: Session = Depends(get_db)):
    data = {}
    for course in db.query(models.Course).all():
        data[course.name] = [t.name for t in course.teachers]
    return data


# ==========================================================
# ==============  SHARED TIMETABLE FORMATTER  ==============
# ==========================================================
def build_formatted_timetable(db: Session, scheduled_classes, free_only: bool = False):
    """Helper: builds a FormattedTimetableResponse list from scheduled classes."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    all_timeslots = db.query(Timeslot).all()
    occupied = {(sc.timeslot_id) for sc in scheduled_classes}

    final_timetable = []
    for day in days:
        day_schedule = schemas.FormattedDay(day=day, timeslots=[])
        day_timeslots = sorted([ts for ts in all_timeslots if ts.day == day],
                               key=lambda x: x.start_time)

        for ts in day_timeslots:
            is_busy = ts.id in occupied
            if free_only and is_busy:
                continue
            formatted_ts = schemas.FormattedTimeslot(
                id=ts.id, start_time=ts.start_time, end_time=ts.end_time,
                duration=ts.duration, slot_type=ts.slot_type, scheduled_classes=[]
            )

            if not free_only and is_busy:
                for sc in [x for x in scheduled_classes if x.timeslot_id == ts.id]:
                    event = db.get(SchedulableEvent, sc.event_id)
                    teacher = db.get(Teacher, sc.teacher_id) if sc.teacher_id else None
                    room = db.get(Room, sc.room_id)
                    if event and room:
                        formatted_class = schemas.FormattedClass(
                            event_name=event.name,
                            room_name=room.name,
                            teacher_name=teacher.name if teacher else "Unassigned",
                            batches=[b.name for b in event.batches],
                        )
                        formatted_ts.scheduled_classes.append(formatted_class)

            day_schedule.timeslots.append(formatted_ts)
        final_timetable.append(day_schedule)

    return final_timetable


# ==========================================================
# ====================  SOLVER  ============================
# ==========================================================
@app.post("/generate-timetable/", response_model=schemas.FormattedTimetableResponse)
def generate_timetable_endpoint(db: Session = Depends(get_db)):
    all_events = db.query(SchedulableEvent).all()
    all_rooms = db.query(Room).all()
    all_timeslots = db.query(Timeslot).all()
    all_teachers = db.query(Teacher).all()
    all_courses = db.query(models.Course).all()

    db_data = {
        "events": all_events,
        "rooms": all_rooms,
        "timeslots": all_timeslots,
        "teachers": all_teachers,
        "courses": all_courses,
    }

    solution = solver.create_timetable_solver(db_data, time_limit_seconds=120.0, debug=True)

    if not solution:
        raise HTTPException(status_code=400, detail="No solution found for the given constraints.")

    db.query(ScheduledClass).delete()
    db.commit()

    scheduled_map = defaultdict(list)
    for event_id, (teacher_id, room_id, timeslot_id) in solution.items():
        scheduled = ScheduledClass(
            event_id=event_id, teacher_id=teacher_id,
            room_id=room_id, timeslot_id=timeslot_id
        )
        db.add(scheduled)
        scheduled_map[timeslot_id].append(scheduled)
    db.commit()

    timetable = build_formatted_timetable(db, [s for sl in scheduled_map.values() for s in sl])
    return {"message": "Timetable generated successfully!", "timetable": timetable}


# ==========================================================
# ==========  TEACHER & BATCH TIMETABLE ENDPOINTS  =========
# ==========================================================
@app.get("/teachers/{teacher_id}/timetable/", response_model=schemas.FormattedTimetableResponse)
def get_teacher_timetable(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    scheduled_classes = (
        db.query(ScheduledClass)
        .join(SchedulableEvent)
        .filter(ScheduledClass.teacher_id == teacher_id)
        .all()
    )

    if not scheduled_classes:
        return {"message": f"No scheduled classes found for {teacher.name}", "timetable": []}

    timetable_by_day = {}

    for sc in scheduled_classes:
        ts = db.get(Timeslot, sc.timeslot_id)
        if not ts:
            continue

        event = db.get(SchedulableEvent, sc.event_id)
        if not event:
            continue

        room = db.get(Room, sc.room_id)
        formatted_class = schemas.FormattedClass(
            event_name=event.name,
            room_name=room.name if room else "Unknown",
            teacher_name=teacher.name,
            batches=[b.name for b in event.batches],
        )

        day_entry = timetable_by_day.setdefault(ts.day, [])
        day_entry.append({
            "start_time": ts.start_time,
            "end_time": ts.end_time,
            "duration": ts.duration,
            "class_info": formatted_class,
        })

    final_timetable = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if day not in timetable_by_day:
            continue

        sorted_slots = sorted(timetable_by_day[day], key=lambda x: x["start_time"])
        formatted_timeslots = [
            schemas.FormattedTimeslot(
                id=i + 1,
                start_time=s["start_time"],
                end_time=s["end_time"],
                duration=s["duration"],
                slot_type="",
                scheduled_classes=[s["class_info"]],
            )
            for i, s in enumerate(sorted_slots)
        ]

        final_timetable.append(schemas.FormattedDay(day=day, timeslots=formatted_timeslots))

    return {"message": f"Timetable for {teacher.name}", "timetable": final_timetable}


@app.get("/batches/{batch_id}/timetable/", response_model=schemas.FormattedTimetableResponse)
def get_batch_timetable(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    scheduled_classes = (
        db.query(ScheduledClass)
        .join(SchedulableEvent)
        .join(event_batches_table)
        .filter(event_batches_table.c.batch_id == batch_id)
        .all()
    )

    if not scheduled_classes:
        return {"message": f"No scheduled classes found for {batch.name}", "timetable": []}

    timetable_by_day = {}

    for sc in scheduled_classes:
        ts = db.get(Timeslot, sc.timeslot_id)
        if not ts:
            continue

        event = db.get(SchedulableEvent, sc.event_id)
        if not event:
            continue

        room = db.get(Room, sc.room_id)
        teacher_name = (
            event.course.teachers[0].name if event.course and event.course.teachers else "Unassigned"
        )

        formatted_class = schemas.FormattedClass(
            event_name=event.name,
            room_name=room.name if room else "Unknown",
            teacher_name=teacher_name,
            batches=[b.name for b in event.batches],
        )

        day_entry = timetable_by_day.setdefault(ts.day, [])
        day_entry.append({
            "start_time": ts.start_time,
            "end_time": ts.end_time,
            "duration": ts.duration,
            "class_info": formatted_class,
        })

    final_timetable = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        if day not in timetable_by_day:
            continue

        sorted_slots = sorted(timetable_by_day[day], key=lambda x: x["start_time"])
        formatted_timeslots = [
            schemas.FormattedTimeslot(
                id=i + 1,
                start_time=s["start_time"],
                end_time=s["end_time"],
                duration=s["duration"],
                slot_type="",
                scheduled_classes=[s["class_info"]],
            )
            for i, s in enumerate(sorted_slots)
        ]

        final_timetable.append(schemas.FormattedDay(day=day, timeslots=formatted_timeslots))

    return {"message": f"Timetable for {batch.name}", "timetable": final_timetable}



@app.get("/batches/{batch_id}/free-slots/", response_model=schemas.FormattedTimetableResponse)
def get_batch_free_slots(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get all busy timeslots for this batch
    busy_classes = (
        db.query(ScheduledClass)
        .join(SchedulableEvent)
        .join(event_batches_table)
        .filter(event_batches_table.c.batch_id == batch_id)
        .all()
    )

    # Track occupied hours
    busy_hours = set()
    for sc in busy_classes:
        timeslot = db.get(Timeslot, sc.timeslot_id)
        if not timeslot:
            continue
        for h in range(timeslot.start_time, timeslot.end_time):
            busy_hours.add((timeslot.day, h))

    # Prepare response
    final_timetable = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    all_timeslots = db.query(Timeslot).all()

    for day in days:
        # Extract all possible hours for the day (from 8–17)
        day_hours = sorted({ts.start_time for ts in all_timeslots if ts.day == day})
        if not day_hours:
            continue

        # Find contiguous free blocks
        free_blocks = []
        start = None
        for hour in range(min(day_hours), max(day_hours) + 1):
            is_free = (day, hour) not in busy_hours
            next_is_busy = (day, hour + 1) in busy_hours

            if is_free and start is None:
                start = hour
            if start is not None and (not is_free or next_is_busy or hour == max(day_hours)):
                end = hour + 1 if is_free else hour
                free_blocks.append((start, end))
                start = None

        # Format output
        formatted_timeslots = [
            schemas.FormattedTimeslot(
                id=i + 1,
                start_time=start,
                end_time=end,
                duration=end - start,
                slot_type="",  # remove type
                scheduled_classes=[],
            )
            for i, (start, end) in enumerate(free_blocks)
        ]

        final_timetable.append(
            schemas.FormattedDay(day=day, timeslots=formatted_timeslots)
        )

    return {
        "message": f"Free slots for {batch.name}",
        "timetable": final_timetable,
    }
@app.get("/timetable/full/", response_model=schemas.FormattedTimetableResponse)
def get_full_timetable(db: Session = Depends(get_db)):
    """Fetch the latest full timetable from ScheduledClass (without rerunning solver)."""
    scheduled_classes = db.query(ScheduledClass).all()

    if not scheduled_classes:
        raise HTTPException(status_code=404, detail="No timetable found. Please generate one first.")

    timetable = build_formatted_timetable(db, scheduled_classes)
    return {"message": "Full timetable fetched successfully!", "timetable": timetable}

@app.post("/admin/auto-prepare/")
def auto_prepare(db: Session = Depends(get_db)):

    # 1) CREATE TIMESLOTS --------------------------------------------------
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    existing = db.query(models.Timeslot).all()
    existing_keys = {(ts.day, ts.start_time, ts.end_time, ts.duration, ts.slot_type) for ts in existing}

    # Lecture slots (1 hour)
    for day in days:
        for hour in range(8, 17):
            key = (day, hour, hour + 1, 1, "Lecture")
            if key not in existing_keys:
                ts = models.Timeslot(
                    day=day,
                    start_time=hour,
                    end_time=hour + 1,
                    duration=1,
                    slot_type="Lecture"
                )
                db.add(ts)

    # Lab slots (2 hours)
    for day in days:
        for hour in range(8, 16, 2):
            key = (day, hour, hour + 2, 2, "Lab")
            if key not in existing_keys:
                ts = models.Timeslot(
                    day=day,
                    start_time=hour,
                    end_time=hour + 2,
                    duration=2,
                    slot_type="Lab"
                )
                db.add(ts)

    db.commit()

    # 2) CREATE EVENTS ------------------------------------------------------
    batches = db.query(models.Batch).all()
    courses = db.query(models.Course).all()

    # Clear old events before regenerating
    db.query(models.SchedulableEvent).delete()
    db.commit()

    pair_batches = []
    for i in range(0, len(batches), 2):
        if i + 1 < len(batches):
            pair_batches.append([batches[i], batches[i + 1]])

    events_to_add = []

    for course in courses:

        # Determine type from credit hours
        if course.credit_hours == 4:
            class_type = "4-credit"
        elif course.credit_hours == 3:
            class_type = "3-credit"
        elif course.credit_hours == 2:
            class_type = "lab"
        else:
            continue  # unsupported

        # ----- For paired batches (lectures & labs) -----
        for b1, b2 in pair_batches:
            batch_ids = [b1.id, b2.id]
            total_size = b1.size + b2.size

            if class_type == "4-credit":
                # 3 lectures
                for i in range(1, 4):
                    events_to_add.append(models.SchedulableEvent(
                        name=f"{course.name} Lecture {i} ({b1.name}+{b2.name})",
                        duration=1,
                        required_room_type="Lecture_X",
                        total_size=total_size,
                        course_id=course.id,
                        batches=[b1, b2]
                    ))

                # 1 tutorial (each batch individually)
                events_to_add.append(models.SchedulableEvent(
                    name=f"{course.name} Tutorial ({b1.name})",
                    duration=1,
                    required_room_type="Tutorial_Y",
                    total_size=b1.size,
                    course_id=course.id,
                    batches=[b1]
                ))
                events_to_add.append(models.SchedulableEvent(
                    name=f"{course.name} Tutorial ({b2.name})",
                    duration=1,
                    required_room_type="Tutorial_Y",
                    total_size=b2.size,
                    course_id=course.id,
                    batches=[b2]
                ))

            elif class_type == "3-credit":
                for i in range(1, 4):
                    events_to_add.append(models.SchedulableEvent(
                        name=f"{course.name} Lecture {i} ({b1.name}+{b2.name})",
                        duration=1,
                        required_room_type="Lecture_X",
                        total_size=total_size,
                        course_id=course.id,
                        batches=[b1, b2]
                    ))

            elif class_type == "lab":
                events_to_add.append(models.SchedulableEvent(
                    name=f"{course.name} ({b1.name}+{b2.name})",
                    duration=2,
                    required_room_type="Lab",
                    total_size=total_size,
                    course_id=course.id,
                    batches=[b1, b2]
                ))

    # Save all events
    for ev in events_to_add:
        db.add(ev)

    db.commit()

    return {"message": f"Auto-prepared {len(events_to_add)} events + timeslots"}

