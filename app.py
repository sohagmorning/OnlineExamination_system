from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "exam_secret_key_123"

DB_PATH = "exam.db"

# =====================
# DATABASE CONNECTION
# =====================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# =====================
# DATABASE INIT
# =====================
def init_db():
    with app.app_context():
        db = get_db()

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (subject_id) REFERENCES subjects(id)
            )
        """)

        # Default admin
        admin = db.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
        if not admin:
            hashed = generate_password_hash("admin123")
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed, "admin"))

        # Default subjects
        count = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        if count == 0:
            for name in ["বাংলা", "ইংরেজি", "গণিত", "বিজ্ঞান"]:
                db.execute("INSERT INTO subjects (name) VALUES (?)", (name,))

        # Sample questions
        q_count = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if q_count == 0:
            bangla_id = db.execute("SELECT id FROM subjects WHERE name = 'বাংলা'").fetchone()[0]
            math_id   = db.execute("SELECT id FROM subjects WHERE name = 'গণিত'").fetchone()[0]

            sample = [
                (bangla_id, "বাংলাদেশের রাজধানী কোথায়?",       "চট্টগ্রাম", "ঢাকা",   "রাজশাহী", "সিলেট",    "B"),
                (bangla_id, "বাংলাদেশের জাতীয় ফুল কোনটি?",     "গোলাপ",    "শাপলা",  "পদ্ম",    "সূর্যমুখী","B"),
                (bangla_id, "বাংলা বর্ণমালায় স্বরবর্ণ কতটি?",  "১০টি",     "১২টি",   "১১টি",    "৯টি",      "C"),
                (math_id,   "২ + ২ = ?",                          "৩",        "৫",      "৪",       "৬",        "C"),
                (math_id,   "১০ × ৫ = ?",                         "৪০",       "৬০",     "৫৫",      "৫০",       "D"),
                (math_id,   "৮১ এর বর্গমূল কত?",                 "৭",        "৮",      "৯",       "১০",       "C"),
            ]
            db.executemany("""
                INSERT INTO questions
                    (subject_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sample)

        db.commit()

# =====================
# AUTH ROUTES
# =====================
@app.route("/")
def home():
    if "user_id" in session:
        if session["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("student_dashboard"))
    return render_template("index.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password!", "error")

    return render_template("admin_login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db   = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid username or password!", "error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed   = generate_password_hash(password)
        try:
            db = get_db()
            db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed, "student"))
            db.commit()
            flash("Registration সফল! এখন login করুন।", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("এই username আগে থেকেই আছে!", "error")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =====================
# STUDENT ROUTES
# =====================
@app.route("/dashboard")
def student_dashboard():
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    db       = get_db()
    subjects = db.execute("SELECT * FROM subjects").fetchall()
    results  = db.execute("""
        SELECT r.*, s.name as subject_name
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.user_id = ?
        ORDER BY r.id DESC
    """, (session["user_id"],)).fetchall()

    return render_template("dashboard.html", subjects=subjects, results=results)

@app.route("/exam/<int:subject_id>")
def exam(subject_id):
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    db       = get_db()
    subject  = db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    questions = db.execute("SELECT * FROM questions WHERE subject_id = ?", (subject_id,)).fetchall()

    if not subject:
        flash("Subject পাওয়া যায়নি!", "error")
        return redirect(url_for("student_dashboard"))

    if not questions:
        flash("এই subject এ এখনো কোনো প্রশ্ন নেই!", "error")
        return redirect(url_for("student_dashboard"))

    return render_template("exam.html", questions=questions, subject=subject)

@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    subject_id = request.form.get("subject_id")
    db         = get_db()
    subject    = db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    questions  = db.execute("SELECT * FROM questions WHERE subject_id = ?", (subject_id,)).fetchall()

    score   = 0
    total   = len(questions)
    details = []

    for q in questions:
        answer     = request.form.get(f"q{q['id']}", "")
        correct    = q["correct_answer"]
        is_correct = answer == correct
        if is_correct:
            score += 1
        details.append({
            "question":       q["question_text"],
            "your_answer":    answer,
            "correct_answer": correct,
            "is_correct":     is_correct,
            "option_a":       q["option_a"],
            "option_b":       q["option_b"],
            "option_c":       q["option_c"],
            "option_d":       q["option_d"],
        })

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute(
        "INSERT INTO results (user_id, subject_id, score, total, date) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], subject_id, score, total, date_str)
    )
    db.commit()

    return render_template("result.html", score=score, total=total, details=details, subject=subject)

# =====================
# ADMIN ROUTES
# =====================
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db        = get_db()
    subjects  = db.execute("SELECT * FROM subjects").fetchall()
    questions = db.execute("""
        SELECT q.*, s.name as subject_name
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        ORDER BY s.name
    """).fetchall()
    users = db.execute("SELECT * FROM users WHERE role = 'student'").fetchall()

    return render_template("admin.html", subjects=subjects, questions=questions, users=users)

@app.route("/admin/add_subject", methods=["POST"])
def add_subject():
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    name = request.form["subject_name"].strip()
    if name:
        try:
            db = get_db()
            db.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
            db.commit()
            flash(f"'{name}' subject সফলভাবে যোগ হয়েছে!", "success")
        except sqlite3.IntegrityError:
            flash("এই subject আগে থেকেই আছে!", "error")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_subject/<int:s_id>")
def delete_subject(s_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db      = get_db()
    q_count = db.execute("SELECT COUNT(*) FROM questions WHERE subject_id = ?", (s_id,)).fetchone()[0]

    if q_count > 0:
        flash(f"এই subject এ {q_count}টি প্রশ্ন আছে। আগে প্রশ্নগুলো মুছুন!", "error")
    else:
        db.execute("DELETE FROM subjects WHERE id = ?", (s_id,))
        db.commit()
        flash("Subject মুছে ফেলা হয়েছে!", "success")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add_question", methods=["POST"])
def add_question():
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db = get_db()
    db.execute("""
        INSERT INTO questions
            (subject_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["subject_id"],
        request.form["question_text"],
        request.form["option_a"],
        request.form["option_b"],
        request.form["option_c"],
        request.form["option_d"],
        request.form["correct_answer"],
    ))
    db.commit()
    flash("প্রশ্ন সফলভাবে যোগ হয়েছে!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_question/<int:q_id>")
def delete_question(q_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    db.commit()
    flash("প্রশ্ন মুছে ফেলা হয়েছে!", "success")
    return redirect(url_for("admin_dashboard"))

# =====================
# RUN
# =====================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
