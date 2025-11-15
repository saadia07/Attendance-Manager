from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    classes = db.relationship("ClassRoom", backref="teacher", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    return Teacher.query.get(int(user_id))


class ClassRoom(db.Model):
    __tablename__ = "classrooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)

    students = db.relationship("Student", backref="classroom", lazy="dynamic", cascade="all, delete-orphan")
    attendances = db.relationship("Attendance", backref="classroom", lazy="dynamic", cascade="all, delete-orphan")


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(50), nullable=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)

    attendances = db.relationship("Attendance", backref="student", lazy="dynamic", cascade="all, delete-orphan")


class Attendance(db.Model):
    __tablename__ = "attendances"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False)  # "present" or "absent"
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
