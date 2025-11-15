from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from . import db
from .models import Teacher, ClassRoom, Student, Attendance
from .forms import SignupForm, LoginForm, ClassForm, StudentForm, MarkAttendanceForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date
from sqlalchemy import func, case
import calendar
from datetime import date, datetime, timedelta
from sqlalchemy import func, case, and_

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

# Signup
@bp.route("/signup", methods=["GET", "POST"])
def auth_signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing = Teacher.query.filter_by(email=form.email.data).first()
        if existing:
            flash("Email already registered", "danger")
            return redirect(url_for("main.auth_signup"))
        t = Teacher(name=form.name.data, email=form.email.data)
        t.set_password(form.password.data)
        db.session.add(t)
        db.session.commit()
        flash("Signup successful. Please login.", "success")
        return redirect(url_for("main.auth_login"))
    return render_template("signup.html", form=form)

# Login
@bp.route("/login", methods=["GET", "POST"])
def auth_login():
    form = LoginForm()
    if form.validate_on_submit():
        t = Teacher.query.filter_by(email=form.email.data).first()
        if t and t.check_password(form.password.data):
            login_user(t)
            flash("Logged in successfully", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

# Logout
@bp.route("/logout")
@login_required
def auth_logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("main.index"))

# Dashboard
@bp.route("/dashboard")
@login_required
def dashboard():
    classes = ClassRoom.query.filter_by(teacher_id=current_user.id).all()
    return render_template("dashboard.html", classes=classes)

# Manage classes
@bp.route("/classes", methods=["GET", "POST"])
@login_required
def classes_view():
    form = ClassForm()
    if form.validate_on_submit():
        c = ClassRoom(name=form.name.data, teacher_id=current_user.id)
        db.session.add(c)
        db.session.commit()
        flash("Class added", "success")
        return redirect(url_for("main.classes_view"))
    classes = ClassRoom.query.filter_by(teacher_id=current_user.id).all()
    return render_template("classes.html", form=form, classes=classes)

@bp.route("/classes/<int:class_id>/delete")
@login_required
def class_delete(class_id):
    c = ClassRoom.query.get_or_404(class_id)
    if c.teacher_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect(url_for("main.classes_view"))
    db.session.delete(c)
    db.session.commit()
    flash("Class deleted", "info")
    return redirect(url_for("main.classes_view"))

# Students
@bp.route("/students", methods=["GET", "POST"])
@login_required
def students_view():
    form = StudentForm()
    # populate class choices for this teacher
    form.class_id.choices = [(c.id, c.name) for c in ClassRoom.query.filter_by(teacher_id=current_user.id).all()]
    if form.validate_on_submit():
        s = Student(name=form.name.data, roll_no=form.roll_no.data, class_id=form.class_id.data)
        db.session.add(s)
        db.session.commit()
        flash("Student added", "success")
        return redirect(url_for("main.students_view"))
    # optionally filter students by class if query param given
    class_filter = request.args.get("class_id", type=int)
    if class_filter:
        students = Student.query.filter_by(class_id=class_filter).all()
    else:
        students = Student.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).all()
    return render_template("students.html", form=form, students=students)

@bp.route("/students/<int:student_id>/delete")
@login_required
def student_delete(student_id):
    s = Student.query.get_or_404(student_id)
    if s.classroom.teacher_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect(url_for("main.students_view"))
    db.session.delete(s)
    db.session.commit()
    flash("Student deleted", "info")
    return redirect(url_for("main.students_view"))

# Mark attendance for a class and date
@bp.route("/classes/<int:class_id>/attendance", methods=["GET", "POST"])
@login_required
def mark_attendance(class_id):
    class_obj = ClassRoom.query.get_or_404(class_id)
    if class_obj.teacher_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect(url_for("main.dashboard"))

    form = MarkAttendanceForm()
    # set default date to today when GET
    if request.method == "GET":
        form.date.data = date.today()

    students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_no).all()

    if form.validate_on_submit():
        att_date = form.date.data
        for s in students:
            key = f"present-{s.id}"
            status = "present" if key in request.form else "absent"
            existing = Attendance.query.filter_by(student_id=s.id, date=att_date, class_id=class_id).first()
            if existing:
                existing.status = status
            else:
                a = Attendance(student_id=s.id, class_id=class_id, date=att_date, status=status)
                db.session.add(a)
        db.session.commit()
        flash("Attendance saved", "success")
        return redirect(url_for("main.mark_attendance", class_id=class_id))

    # load attendances for date into a map for checkboxes
    att_map = {}
    if form.date.data:
        for a in Attendance.query.filter_by(class_id=class_id, date=form.date.data).all():
            att_map[a.student_id] = a.status

    return render_template("mark_attendance.html", form=form, class_obj=class_obj, students=students, att_map=att_map)

# Reports (daily / monthly / yearly)
# @bp.route("/reports", methods=["GET"])
# @login_required
# def reports():
#     class_id = request.args.get("class_id", type=int)
#     view = request.args.get("view", "daily")  # daily | monthly | yearly
#     date_str = request.args.get("date")  # yyyy-mm-dd
#     month = request.args.get("month", type=int)
#     year = request.args.get("year", type=int)

#     classes = ClassRoom.query.filter_by(teacher_id=current_user.id).all()
#     results = []

#     if view == "daily" and date_str and class_id:
#         try:
#             qdate = datetime.strptime(date_str, "%Y-%m-%d").date()
#             results = (
#                 db.session.query(Student.name, Attendance.status)
#                 .join(Attendance)
#                 .filter(
#                     Attendance.class_id == class_id,
#                     Attendance.date == qdate,
#                 )
#                 .all()
#             )
#         except ValueError:
#             flash("Invalid date format. Use YYYY-MM-DD.", "warning")

#     elif view == "monthly" and month and year and class_id:
#         # works for SQLite; if you use PostgreSQL change to extract/year functions
#         month_s = f"{month:02d}"
#         results = (
#             db.session.query(Attendance.date, Student.name, Attendance.status)
#             .join(Student)
#             .filter(
#                 Attendance.class_id == class_id,
#                 func.strftime("%Y", Attendance.date) == str(year),
#                 func.strftime("%m", Attendance.date) == month_s,
#             )
#             .order_by(Attendance.date)
#             .all()
#         )

#     elif view == "yearly" and year and class_id:
#         # number of presents and total records per student
#         present_case = case([(Attendance.status == "present", 1)], else_=0)
#         results = (
#             db.session.query(
#                 Student.name,
#                 func.sum(present_case).label("present_count"),
#                 func.count(Attendance.id).label("total"),
#             )
#             .join(Attendance)
#             .filter(
#                 Attendance.class_id == class_id,
#                 func.strftime("%Y", Attendance.date) == str(year),
#             )
#             .group_by(Student.id)
#             .all()
#         )

#     return render_template(
#         "reports.html",
#         classes=classes,
#         results=results,
#         view=view,
#         class_id=class_id,
#         date_str=date_str or "",
#         month=month or "",
#         year=year or "",
#     )
@bp.route("/reports", methods=["GET"])
@login_required
def reports():
    # parse raw params
    class_id = request.args.get("class_id", type=int)
    view = request.args.get("view", "daily")
    date_str = request.args.get("date")
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    # all classes for this teacher
    classes = ClassRoom.query.filter_by(teacher_id=current_user.id).all()
    class_ids = [c.id for c in classes]
    results = []

    # Defaults: if user chose monthly/yearly but left year empty, default to current year.
    today = date.today()
    if view == "monthly":
        if not month:
            month = today.month
        if not year:
            year = today.year
    if view == "yearly":
        if not year:
            year = today.year

    # --- DAILY ---
    if view == "daily" and date_str:
        try:
            qdate = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "warning")
            qdate = None

        if qdate:
            if class_id:
                students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_no).all()
                attendance_q = Attendance.query.filter_by(date=qdate, class_id=class_id).all()
            else:
                students = Student.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).order_by(Student.roll_no).all()
                attendance_q = Attendance.query.filter(Attendance.date == qdate, Attendance.class_id.in_(class_ids)).all()

            att_map = {a.student_id: a.status for a in attendance_q}
            results = [(s.name, att_map.get(s.id, "-")) for s in students]

    # --- MONTHLY ---
    elif view == "monthly" and month and year:
        try:
            _, ndays = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, ndays)
        except Exception:
            flash("Invalid month/year.", "warning")
            start_date = end_date = None

        if start_date and end_date:
            if class_id:
                students = Student.query.filter_by(class_id=class_id).order_by(Student.roll_no).all()
                attendance_q = Attendance.query.filter(
                    Attendance.class_id == class_id,
                    Attendance.date >= start_date,
                    Attendance.date <= end_date,
                ).all()
            else:
                students = Student.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).order_by(Student.roll_no).all()
                attendance_q = Attendance.query.filter(
                    Attendance.class_id.in_(class_ids),
                    Attendance.date >= start_date,
                    Attendance.date <= end_date,
                ).all()

            att_map = {(a.date, a.student_id): a.status for a in attendance_q}
            results = []
            for d in range(1, ndays + 1):
                current = date(year, month, d)
                for s in students:
                    status = att_map.get((current, s.id), "-")
                    results.append((current, s.name, status))

    # --- YEARLY ---
    elif view == "yearly" and year:
        present_case = case((Attendance.status == "present", 1), else_=0)

        if class_id:
            results = (
                db.session.query(
                    Student.name,
                    func.coalesce(func.sum(present_case), 0).label("present_count"),
                    func.coalesce(func.count(Attendance.id), 0).label("total"),
                )
                .outerjoin(
                    Attendance,
                    and_(
                        Attendance.student_id == Student.id,
                        Attendance.class_id == class_id,
                        func.strftime("%Y", Attendance.date) == str(year),
                    )
                )
                .filter(Student.class_id == class_id)
                .group_by(Student.id)
                .all()
            )
        else:
            if not class_ids:
                results = []
            else:
                results = (
                    db.session.query(
                        Student.name,
                        func.coalesce(func.sum(present_case), 0).label("present_count"),
                        func.coalesce(func.count(Attendance.id), 0).label("total"),
                    )
                    .outerjoin(
                        Attendance,
                        and_(
                            Attendance.student_id == Student.id,
                            Attendance.class_id.in_(class_ids),
                            func.strftime("%Y", Attendance.date) == str(year),
                        )
                    )
                    .join(ClassRoom, Student.class_id == ClassRoom.id)
                    .filter(ClassRoom.teacher_id == current_user.id)
                    .group_by(Student.id)
                    .all()
                )

    return render_template(
        "reports.html",
        classes=classes,
        results=results,
        view=view,
        class_id=class_id,
        date_str=date_str or "",
        month=month or "",
        year=year or "",
    )