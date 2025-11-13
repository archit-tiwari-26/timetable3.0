from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey, Table
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import MetaData

# --- DATABASE CONFIG ---
DATABASE_URL = "sqlite:///./timetable.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- FIX: Shared metadata to prevent duplicate-table warnings ---
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# ============================================================
#                ASSOCIATION TABLES
# ============================================================

# --- Teacher ↔ Course (many-to-many) ---
teacher_courses = Table(
    "teacher_courses",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
)

# --- Event ↔ Batch (many-to-many) ---
event_batches_table = Table(
    "event_batches",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("schedulable_events.id"), primary_key=True),
    Column("batch_id", Integer, ForeignKey("batches.id"), primary_key=True),
)

# ============================================================
#                CORE MODELS
# ============================================================

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    max_hours = Column(Integer, default=16)

    # Courses this teacher can teach
    courses = relationship("Course", secondary=teacher_courses, back_populates="teachers")

    # Optional: classes assigned in final timetable
    scheduled_classes = relationship("ScheduledClass", back_populates="teacher", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Teacher(name={self.name}, max_hours={self.max_hours})>"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    credit_hours = Column(Integer, default=4)

    # Teachers who can teach this course
    teachers = relationship("Teacher", secondary=teacher_courses, back_populates="courses")

    # Events linked to this course
    events = relationship("SchedulableEvent", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(name={self.name}, credit_hours={self.credit_hours})>"


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    size = Column(Integer)

    def __repr__(self):
        return f"<Batch(name={self.name}, size={self.size})>"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer)
    room_type = Column(String, index=True)  # e.g., Lecture_X, Tutorial_Y, Lab

    scheduled_classes = relationship("ScheduledClass", back_populates="room")

    def __repr__(self):
        return f"<Room(name={self.name}, type={self.room_type}, capacity={self.capacity})>"


class Timeslot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String)
    start_time = Column(Integer)
    end_time = Column(Integer)
    duration = Column(Integer, default=1)  # 1hr or 2hr
    slot_type = Column(String, default="Lecture")  # Lecture / Lab

    scheduled_classes = relationship("ScheduledClass", back_populates="timeslot")

    def __repr__(self):
        return f"<Timeslot(day={self.day}, start={self.start_time}, end={self.end_time}, type={self.slot_type})>"


# ============================================================
#                SCHEDULING MODELS
# ============================================================

class SchedulableEvent(Base):
    """
    Represents an event that needs to be scheduled (e.g., a lecture, tutorial, or lab).
    Linked to a course, and attended by one or more batches.
    """
    __tablename__ = "schedulable_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    duration = Column(Integer, default=1)
    required_room_type = Column(String)
    total_size = Column(Integer)

    # Linked to a course
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="events")

    # Teacher assigned (solver decides dynamically)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    teacher = relationship("Teacher")

    # Batches attending this event
    batches = relationship("Batch", secondary=event_batches_table)

    def __repr__(self):
        return f"<Event(name={self.name}, duration={self.duration}, course={self.course_id})>"


class ScheduledClass(Base):
    """
    Represents a finalized scheduled class in the timetable.
    Links event, teacher, room, and timeslot together.
    """
    __tablename__ = "scheduled_classes"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("schedulable_events.id"))
    event = relationship("SchedulableEvent")

    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    teacher = relationship("Teacher", back_populates="scheduled_classes")

    room_id = Column(Integer, ForeignKey("rooms.id"))
    room = relationship("Room", back_populates="scheduled_classes")

    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))
    timeslot = relationship("Timeslot", back_populates="scheduled_classes")

    def __repr__(self):
        return f"<ScheduledClass(event={self.event_id}, teacher={self.teacher_id}, room={self.room_id})>"


# ============================================================
#                DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)
