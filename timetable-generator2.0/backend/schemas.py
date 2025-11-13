from typing import List, Optional
from pydantic import BaseModel

# =========================
# --- TEACHER ---
# =========================
class TeacherBase(BaseModel):
    name: str
    max_hours: Optional[int] = 16

class TeacherCreate(TeacherBase):
    pass

class Teacher(TeacherBase):
    id: int
    class Config:
        from_attributes = True


# =========================
# --- COURSE ---
# =========================
class CourseBase(BaseModel):
    name: str
    credit_hours: int

class CourseCreate(CourseBase):
    # no teacher_ids here – handled later via /assign-teachers/
    pass

class Course(CourseBase):
    id: int
    teachers: List[Teacher] = []
    class Config:
        from_attributes = True


# =========================
# --- BATCH ---
# =========================
class BatchBase(BaseModel):
    name: str
    size: int

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    id: int
    class Config:
        from_attributes = True


# =========================
# --- ROOM ---
# =========================
class RoomBase(BaseModel):
    name: str
    capacity: int
    room_type: str

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: int
    class Config:
        from_attributes = True


# =========================
# --- TIMESLOT ---
# =========================
class TimeslotBase(BaseModel):
    day: str
    start_time: int
    end_time: int
    duration: int
    slot_type: str

class TimeslotCreate(TimeslotBase):
    pass

class Timeslot(TimeslotBase):
    id: int
    class Config:
        from_attributes = True


# =========================
# --- SCHEDULABLE EVENT ---
# =========================
class SchedulableEventBase(BaseModel):
    name: str
    duration: int
    required_room_type: str
    total_size: int
    course_id: int

class SchedulableEventCreate(SchedulableEventBase):
    batch_ids: List[int]

class SchedulableEvent(SchedulableEventBase):
    id: int
    course: Optional["Course"] = None
    teacher: Optional["Teacher"] = None
    batches: List["Batch"] = []
    class Config:
        from_attributes = True


# =========================
# --- FORMATTED TIMETABLE ---
# =========================
class FormattedClass(BaseModel):
    event_name: str
    room_name: str
    teacher_name: str
    batches: List[str]

class FormattedTimeslot(BaseModel):
    id: int
    start_time: int
    end_time: int
    duration: int
    slot_type: str
    scheduled_classes: List[FormattedClass]

class FormattedDay(BaseModel):
    day: str
    timeslots: List[FormattedTimeslot]

class FormattedTimetableResponse(BaseModel):
    message: str
    timetable: List[FormattedDay]
