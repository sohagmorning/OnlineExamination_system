from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "exam_secret_key_123"

DB_PATH = os.environ.get(
    "DB_PATH",
    "/tmp/exam.db" if os.environ.get("VERCEL") else "exam.db",
)

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
            for name in ["C Programming", "C++ Programming", "Python", "Algorithms", "Computer Fundamentals"]:
                db.execute("INSERT INTO subjects (name) VALUES (?)", (name,))

        # Sample questions
        q_count = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if q_count == 0:
            c_id     = db.execute("SELECT id FROM subjects WHERE name = 'C Programming'").fetchone()[0]
            cpp_id   = db.execute("SELECT id FROM subjects WHERE name = 'C++ Programming'").fetchone()[0]
            py_id    = db.execute("SELECT id FROM subjects WHERE name = 'Python'").fetchone()[0]
            algo_id  = db.execute("SELECT id FROM subjects WHERE name = 'Algorithms'").fetchone()[0]
            cf_id    = db.execute("SELECT id FROM subjects WHERE name = 'Computer Fundamentals'").fetchone()[0]

            sample = [
                # C Programming
                (c_id, "Which symbol is used to end a statement in C?",
                 ":", ";", ".", ",", "B"),
                (c_id, "Which of the following is a valid data type in C?",
                 "integer", "real", "float", "decimal", "C"),
                (c_id, "Which function is used to print output in C?",
                 "input()", "print()", "printf()", "display()", "C"),
                (c_id, "Which operator is used to get the address of a variable in C?",
                 "*", "&", "#", "%", "B"),
                (c_id, "Which loop is guaranteed to execute at least once?",
                 "for loop", "while loop", "do-while loop", "Nested loop", "C"),

                # C++ Programming
                (cpp_id, "Which feature allows C++ to support Object-Oriented Programming?",
                 "Only functions", "Classes and Objects", "Only arrays", "Preprocessors", "B"),
                (cpp_id, "Which keyword is used to create a class in C++?",
                 "object", "struct", "class", "define", "C"),
                (cpp_id, "Which of the following is used for single-line comments in C++?",
                 "//", "/* */", "#", "--", "A"),
                (cpp_id, "What is the default access specifier of a C++ class?",
                 "Public", "Private", "Protected", "Global", "B"),
                (cpp_id, "Which concept allows a class to acquire properties of another class?",
                 "Encapsulation", "Abstraction", "Inheritance", "Polymorphism", "C"),

                # Python
                (py_id, "Which keyword is used to define a function in Python?",
                 "function", "def", "func", "define", "B"),
                (py_id, "Which of the following is a mutable data type in Python?",
                 "Tuple", "String", "List", "Integer", "C"),
                (py_id, "Which symbol is used for a single-line comment in Python?",
                 "//", "/*", "#", "--", "C"),
                (py_id, "What is the output of: x = [10, 20, 30] / print(len(x))",
                 "2", "3", "10", "Error", "B"),
                (py_id, "Which keyword is used to create a loop that iterates through a sequence?",
                 "loop", "repeat", "for", "iterate", "C"),

                # Algorithms
                (algo_id, "Which algorithm is commonly used to search an element in a sorted array?",
                 "Bubble Search", "Binary Search", "Selection Search", "Merge Search", "B"),
                (algo_id, "What is the worst-case time complexity of Binary Search?",
                 "O(n)", "O(n²)", "O(log n)", "O(1)", "C"),
                (algo_id, "Which sorting algorithm repeatedly compares adjacent elements?",
                 "Merge Sort", "Quick Sort", "Bubble Sort", "Heap Sort", "C"),
                (algo_id, "Which algorithmic technique chooses the best option at each step?",
                 "Divide and Conquer", "Greedy Algorithm", "Backtracking", "Brute Force", "B"),
                (algo_id, "In Graph Coloring, what is the main condition?",
                 "All vertices must have the same color", "Adjacent vertices must have different colors",
                 "Every vertex must have two colors", "Only one vertex can be colored", "B"),

                # Computer Fundamentals
                (cf_id, "Which component is known as the brain of the computer?",
                 "RAM", "Hard Disk", "CPU", "Monitor", "C"),
                (cf_id, "Which of the following is volatile memory?",
                 "ROM", "RAM", "SSD", "Hard Disk", "B"),
                (cf_id, "Which of the following is an Operating System?",
                 "MS Word", "Google Chrome", "Windows", "MySQL", "C"),
                (cf_id, "Which device is primarily used to input text into a computer?",
                 "Monitor", "Printer", "Keyboard", "Speaker", "C"),
                (cf_id, "Which device is used to display visual output from a computer?",
                 "Keyboard", "Monitor", "Mouse", "Scanner", "B"),
            ]
            db.executemany("""
                INSERT INTO questions
                    (subject_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sample)

        # Add 20 more questions for every subject. The question-text check keeps
        # this migration safe when the application starts more than once.
        additional_questions = [
            # C Programming
            ("C Programming", "Who developed the C programming language?",
             "Dennis Ritchie", "Bjarne Stroustrup", "Guido van Rossum", "James Gosling", "A"),
            ("C Programming", "Which format specifier prints an integer in C?",
             "%f", "%c", "%s", "%d", "D"),
            ("C Programming", "What is the result of 10 % 3 in C?",
             "1", "3", "0", "3.33", "A"),
            ("C Programming", "What is the index of the first element in a C array?",
             "0", "1", "-1", "Depends on the array size", "A"),
            ("C Programming", "Which character terminates a string in C?",
             "\\n", "\\t", "\\0", "\\b", "C"),
            ("C Programming", "What is a pointer in C?",
             "A variable that stores a memory address", "A character variable",
             "A loop statement", "A preprocessor directive", "A"),
            ("C Programming", "Which operator dereferences a pointer?",
             "&", "#", "*", "@", "C"),
            ("C Programming", "What does recursion mean in C?",
             "A function calling itself", "An infinite loop",
             "A variable changing type", "A pointer storing an integer", "A"),
            ("C Programming", "Which keyword returns a value from a function?",
             "send", "print", "break", "return", "D"),
            ("C Programming", "Which header file declares printf()?",
             "stdlib.h", "stdio.h", "string.h", "math.h", "B"),
            ("C Programming", "Which function allocates memory dynamically?",
             "printf()", "strlen()", "malloc()", "strcmp()", "C"),
            ("C Programming", "Which function releases dynamically allocated memory?",
             "delete()", "remove()", "clear()", "free()", "D"),
            ("C Programming", "Which keyword defines a structure?",
             "struct", "class", "record", "union", "A"),
            ("C Programming", "Which function opens a file?",
             "openfile()", "fopen()", "fileopen()", "readfile()", "B"),
            ("C Programming", "Which statement skips the current loop iteration?",
             "break", "continue", "return", "exit", "B"),
            ("C Programming", "Which operator performs logical AND?",
             "&", "&&", "|", "||", "B"),
            ("C Programming", "Which storage class preserves a local variable between calls?",
             "auto", "register", "static", "extern", "C"),
            ("C Programming", "Which function compares two strings?",
             "strcpy()", "strcat()", "strlen()", "strcmp()", "D"),
            ("C Programming", "Which preprocessor directive includes a header file?",
             "#define", "#include", "#ifdef", "#pragma", "B"),
            ("C Programming", "Which function converts a string to a long integer?",
             "atoi()", "atol()", "itoa()", "strtolonly()", "B"),

            # C++ Programming
            ("C++ Programming", "Who developed C++?",
             "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup", "Guido van Rossum", "C"),
            ("C++ Programming", "What is a class in C++?",
             "A loop", "A type that defines data and behavior",
             "A header file", "An output function", "B"),
            ("C++ Programming", "What is an object?",
             "A compiler error", "A loop condition", "An instance of a class", "A parameter", "C"),
            ("C++ Programming", "Which access specifier allows general external access?",
             "private", "protected", "hidden", "public", "D"),
            ("C++ Programming", "Which function is called automatically when an object is created?",
             "Constructor", "Destructor", "Main function", "Friend function", "A"),
            ("C++ Programming", "Which symbol starts a destructor name?",
             "!", "~", "#", "&", "B"),
            ("C++ Programming", "What is inheritance?",
             "Repeating a loop", "Deleting a class",
             "Creating a class from an existing class", "Converting a number", "C"),
            ("C++ Programming", "Which concept represents different behaviors through one interface?",
             "Encapsulation", "Abstraction", "Inheritance", "Polymorphism", "D"),
            ("C++ Programming", "What is function overloading?",
             "Same name with different parameter lists", "Calling a function repeatedly",
             "Two functions with different names", "Deleting a function", "A"),
            ("C++ Programming", "Which keyword enables runtime polymorphism?",
             "static", "virtual", "inline", "const", "B"),
            ("C++ Programming", "Which operator is used for scope resolution?",
             "->", ".", "::", ":", "C"),
            ("C++ Programming", "Which keyword creates a dynamic object?",
             "malloc", "create", "alloc", "new", "D"),
            ("C++ Programming", "Which operator frees a single object created by new?",
             "delete", "free", "remove", "clear", "A"),
            ("C++ Programming", "Which header provides std::vector?",
             "<array.h>", "<vector>", "<list.h>", "<collection>", "B"),
            ("C++ Programming", "Which feature hides internal class data?",
             "Recursion", "Compilation", "Encapsulation", "Iteration", "C"),
            ("C++ Programming", "Which keyword marks a non-modifying member function?",
             "static", "virtual", "friend", "const", "D"),
            ("C++ Programming", "Which stream is normally used for standard output?",
             "std::cout", "std::cin", "std::cerr", "std::input", "A"),
            ("C++ Programming", "Which operator receives input with std::cin?",
             "<<", ">>", "==", "&&", "B"),
            ("C++ Programming", "Which blocks handle exceptions in C++?",
             "if-else", "switch-case", "try-catch", "for-while", "C"),
            ("C++ Programming", "Which keyword prevents a class from being inherited?",
             "sealed", "final", "stop", "private", "B"),

            # Python
            ("Python", "Who created Python?",
             "Dennis Ritchie", "James Gosling", "Bjarne Stroustrup", "Guido van Rossum", "D"),
            ("Python", "Which symbol starts a single-line comment?",
             "#", "//", "/*", "--", "A"),
            ("Python", "Which is a valid Python assignment?",
             "int x = 10", "x = 10", "let x := 10", "declare x = 10", "B"),
            ("Python", "Which function displays output?",
             "echo()", "displayText()", "print()", "printf()", "C"),
            ("Python", "Which function receives user input?",
             "scanf()", "get()", "readInput()", "input()", "D"),
            ("Python", "What is the type of True?",
             "bool", "int", "str", "float", "A"),
            ("Python", "Which data structure is mutable?",
             "Tuple", "List", "String", "Integer", "B"),
            ("Python", "Which data structure stores unique elements?",
             "List", "Tuple", "Set", "String", "C"),
            ("Python", "Which collection stores key-value pairs?",
             "List", "Tuple", "Set", "Dictionary", "D"),
            ("Python", "What is the output of print(2 ** 3)?",
             "8", "6", "9", "5", "A"),
            ("Python", "What is the output of print(10 // 3)?",
             "3.33", "3", "1", "4", "B"),
            ("Python", "Which keyword defines a function?",
             "function", "define", "def", "fun", "C"),
            ("Python", "Which keyword starts a conditional statement?",
             "when", "condition", "check", "if", "D"),
            ("Python", "Which keyword creates a class?",
             "class", "object", "struct", "define", "A"),
            ("Python", "What is the output of len('Python')?",
             "5", "6", "7", "8", "B"),
            ("Python", "Which keyword handles an exception?",
             "catch", "error", "except", "handle", "C"),
            ("Python", "Which file mode opens a file for reading?",
             "w", "a", "x", "r", "D"),
            ("Python", "What does list.append() do?",
             "Adds an element to the end", "Removes the first element",
             "Sorts the list", "Reverses the list", "A"),
            ("Python", "Which keyword imports a module?",
             "include", "import", "require", "using", "B"),
            ("Python", "What is the type of 3.14?",
             "int", "str", "float", "bool", "C"),

            # Algorithms
            ("Algorithms", "What is an algorithm?",
             "A programming language", "A computer device", "An operating system",
             "A finite sequence of steps to solve a problem", "D"),
            ("Algorithms", "Which notation represents an asymptotic upper bound?",
             "Big O", "Big Omega", "Big Theta", "Little omega", "A"),
            ("Algorithms", "What is the worst-case complexity of linear search?",
             "O(1)", "O(n)", "O(log n)", "O(n^2)", "B"),
            ("Algorithms", "What is binary search complexity in the worst case?",
             "O(n)", "O(n^2)", "O(log n)", "O(1)", "C"),
            ("Algorithms", "What condition does binary search require?",
             "Only even numbers", "Unique elements", "Prime length", "A sorted array", "D"),
            ("Algorithms", "Which algorithm uses divide and conquer?",
             "Merge sort", "Linear search", "Selection sort", "Sequential traversal", "A"),
            ("Algorithms", "What is merge sort's worst-case complexity?",
             "O(n^2)", "O(n log n)", "O(log n)", "O(1)", "B"),
            ("Algorithms", "What is quicksort's worst-case complexity?",
             "O(log n)", "O(n log n)", "O(n^2)", "O(1)", "C"),
            ("Algorithms", "Which sort compares adjacent elements?",
             "Merge sort", "Heap sort", "Insertion sort", "Bubble sort", "D"),
            ("Algorithms", "Which structure is used by breadth-first search?",
             "Queue", "Stack", "Heap", "Hash table", "A"),
            ("Algorithms", "Which structure is used by iterative depth-first search?",
             "Queue", "Stack", "Priority queue", "Sorted array", "B"),
            ("Algorithms", "Which algorithm finds shortest paths with non-negative weights?",
             "Prim's algorithm", "Kruskal's algorithm", "Dijkstra's algorithm", "Merge sort", "C"),
            ("Algorithms", "Which algorithm finds a minimum spanning tree?",
             "Binary search", "Floyd-Warshall", "Quick sort", "Prim's algorithm", "D"),
            ("Algorithms", "Which algorithm is associated with the greedy approach?",
             "Kruskal's algorithm", "Merge sort", "Binary search", "Linear search", "A"),
            ("Algorithms", "What is the main idea of dynamic programming?",
             "Choose the locally largest value", "Reuse solutions to overlapping subproblems",
             "Sort all inputs first", "Explore only one solution", "B"),
            ("Algorithms", "Which technique backtracks from an invalid partial solution?",
             "Hashing", "Greedy selection", "Backtracking", "Linear probing", "C"),
            ("Algorithms", "What does a minimum spanning tree minimize?",
             "Number of vertices", "Degree of every vertex", "Longest edge always",
             "Total weight of the tree", "D"),
            ("Algorithms", "Which class contains problems solvable in polynomial time?",
             "P", "NP-hard", "Undecidable", "EXPSPACE", "A"),
            ("Algorithms", "What is the goal of an approximation algorithm?",
             "Constant-time solutions", "Efficient near-optimal solutions",
             "Remove input data", "Turn every problem into sorting", "B"),
            ("Algorithms", "What is typical array index access complexity?",
             "O(n)", "O(log n)", "O(1)", "O(n^2)", "C"),

            # Computer Fundamentals
            ("Computer Fundamentals", "What is the full form of CPU?",
             "Computer Processing Utility", "Central Program Unit",
             "Control Processing User", "Central Processing Unit", "D"),
            ("Computer Fundamentals", "Which component performs arithmetic and logic?",
             "ALU", "Control Unit", "RAM", "Hard disk", "A"),
            ("Computer Fundamentals", "Which memory is volatile?",
             "ROM", "RAM", "SSD", "DVD", "B"),
            ("Computer Fundamentals", "Which memory retains data without power?",
             "Cache", "RAM", "ROM", "CPU register", "C"),
            ("Computer Fundamentals", "What is the smallest unit of digital information?",
             "Byte", "Kilobyte", "Nibble", "Bit", "D"),
            ("Computer Fundamentals", "How many bits are in one byte?",
             "8", "4", "16", "32", "A"),
            ("Computer Fundamentals", "Which is an input device?",
             "Monitor", "Keyboard", "Printer", "Speaker", "B"),
            ("Computer Fundamentals", "Which is an output device?",
             "Mouse", "Scanner", "Monitor", "Keyboard", "C"),
            ("Computer Fundamentals", "Which software manages hardware resources?",
             "Word processor", "Web browser", "Spreadsheet", "Operating system", "D"),
            ("Computer Fundamentals", "Which of these is an operating system?",
             "Linux", "Microsoft Word", "Google Chrome", "Adobe Photoshop", "A"),
            ("Computer Fundamentals", "What is the primary function of a compiler?",
             "Manage network cables", "Translate source code",
             "Store files permanently", "Protect the monitor", "B"),
            ("Computer Fundamentals", "Which number system uses only 0 and 1?",
             "Decimal", "Octal", "Binary", "Hexadecimal", "C"),
            ("Computer Fundamentals", "What is binary 1010 in decimal?",
             "8", "12", "14", "10", "D"),
            ("Computer Fundamentals", "Which network covers a small local area?",
             "LAN", "WAN", "MAN", "Internet backbone", "A"),
            ("Computer Fundamentals", "What is the full form of URL?",
             "Universal Routing Link", "Uniform Resource Locator",
             "Unified Reference Language", "User Resource Location", "B"),
            ("Computer Fundamentals", "What is the primary role of DNS?",
             "Encrypt every file", "Allocate CPU time",
             "Translate domain names to records such as IP addresses", "Increase RAM", "C"),
            ("Computer Fundamentals", "Which protocol securely browses websites?",
             "FTP", "HTTP only", "Telnet", "HTTPS", "D"),
            ("Computer Fundamentals", "What is a database?",
             "An organized collection of data", "A type of CPU",
             "A computer virus", "An output device", "A"),
            ("Computer Fundamentals", "Which device forwards packets between networks?",
             "Keyboard", "Router", "Scanner", "Printer", "B"),
            ("Computer Fundamentals", "What is phishing?",
             "A way to increase CPU speed", "Data compression",
             "A deceptive attempt to steal sensitive information", "Computer startup", "C"),
        ]

        for subject_name, question_text, option_a, option_b, option_c, option_d, correct_answer in additional_questions:
            subject_id = db.execute(
                "SELECT id FROM subjects WHERE name = ?", (subject_name,)
            ).fetchone()[0]
            db.execute("""
                INSERT INTO questions
                    (subject_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                SELECT ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM questions
                    WHERE subject_id = ? AND question_text = ?
                )
            """, (
                subject_id, question_text, option_a, option_b, option_c, option_d,
                correct_answer, subject_id, question_text
            ))

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
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("This username already exists!", "error")

    return render_template("register.html")

@app.route("/logout")
def logout():
    redirect_endpoint = "home" if session.get("role") == "admin" else "login"
    session.clear()
    return redirect(url_for(redirect_endpoint))

# =====================
# STUDENT ROUTES
# =====================
@app.route("/exam-portal")
def exam_portal():
    db = get_db()
    subjects = db.execute("""
        SELECT s.*, COUNT(q.id) AS question_count
        FROM subjects s
        LEFT JOIN questions q ON q.subject_id = s.id
        GROUP BY s.id
        ORDER BY s.name
    """).fetchall()
    return render_template("exam_portal.html", subjects=subjects)

@app.route("/results")
def public_results():
    sort_by = request.args.get("sort", "username")
    limit_value = request.args.get("limit", "10")

    if sort_by not in {"username", "score"}:
        sort_by = "username"
    try:
        limit = int(limit_value)
    except (TypeError, ValueError):
        limit = 10
    if limit < 1:
        limit = 10
    limit_value = str(limit)

    order_by = (
        "CAST(r.score AS REAL) / NULLIF(r.total, 0) DESC, "
        "r.score DESC, u.username COLLATE NOCASE ASC, r.id DESC"
        if sort_by == "score"
        else "u.username COLLATE NOCASE ASC, r.id DESC"
    )

    db = get_db()
    results = db.execute(f"""
        SELECT r.*, u.username, s.name AS subject_name
        FROM results r
        JOIN users u ON r.user_id = u.id
        JOIN subjects s ON r.subject_id = s.id
        ORDER BY {order_by}
        LIMIT ?
    """, (limit,)).fetchall()
    total_results = db.execute("SELECT COUNT(*) FROM results").fetchone()[0]

    return render_template(
        "public_results.html",
        results=results,
        total_results=total_results,
        sort_by=sort_by,
        limit_value=limit_value,
    )

@app.route("/dashboard")
def student_dashboard():
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    db       = get_db()
    user     = db.execute(
        "SELECT id, username, role FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    subjects = db.execute("SELECT * FROM subjects").fetchall()
    results  = db.execute("""
        SELECT r.*, s.name as subject_name
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.user_id = ?
        ORDER BY r.id DESC
    """, (session["user_id"],)).fetchall()
    performance = db.execute("""
        SELECT
            COUNT(*) AS total_exams,
            COALESCE(AVG(CAST(score AS REAL) / NULLIF(total, 0) * 100), 0) AS average_percentage,
            COALESCE(MAX(CAST(score AS REAL) / NULLIF(total, 0) * 100), 0) AS highest_percentage,
            COALESCE(SUM(CASE WHEN CAST(score AS REAL) / NULLIF(total, 0) >= 0.5 THEN 1 ELSE 0 END), 0) AS passed_exams
        FROM results
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    return render_template(
        "dashboard.html",
        user=user,
        subjects=subjects,
        results=results,
        performance=performance,
    )

@app.route("/exam/<int:subject_id>", methods=["GET", "POST"])
def exam(subject_id):
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    db       = get_db()
    subject  = db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    all_questions = db.execute(
        "SELECT * FROM questions WHERE subject_id = ?", (subject_id,)
    ).fetchall()

    if not subject:
        flash("Subject not found!", "error")
        return redirect(url_for("student_dashboard"))

    if not all_questions:
        flash("No questions available for this subject yet!", "error")
        return redirect(url_for("student_dashboard"))

    if request.method == "GET":
        return render_template(
            "exam_setup.html",
            subject=subject,
            available_questions=len(all_questions),
        )

    try:
        question_count = int(request.form.get("question_count", ""))
        duration_minutes = int(request.form.get("duration_minutes", ""))
    except (TypeError, ValueError):
        flash("Please select a valid question count and exam duration.", "error")
        return redirect(url_for("exam", subject_id=subject_id))

    if not 1 <= question_count <= len(all_questions):
        flash(f"Question count must be between 1 and {len(all_questions)}.", "error")
        return redirect(url_for("exam", subject_id=subject_id))
    if not 1 <= duration_minutes <= 180:
        flash("Exam duration must be between 1 and 180 minutes.", "error")
        return redirect(url_for("exam", subject_id=subject_id))

    questions = random.sample(all_questions, question_count)
    session["active_exam"] = {
        "subject_id": subject_id,
        "question_ids": [q["id"] for q in questions],
        "duration_minutes": duration_minutes,
    }
    return render_template(
        "exam.html",
        questions=questions,
        subject=subject,
        duration_minutes=duration_minutes,
    )

@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    subject_id = request.form.get("subject_id")
    active_exam = session.pop("active_exam", None)
    if not active_exam or str(active_exam["subject_id"]) != str(subject_id):
        flash("Your exam session has expired. Please start the exam again.", "error")
        return redirect(url_for("exam", subject_id=subject_id))

    db         = get_db()
    subject    = db.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    question_ids = active_exam["question_ids"]
    placeholders = ",".join("?" for _ in question_ids)
    questions = db.execute(
        f"SELECT * FROM questions WHERE subject_id = ? AND id IN ({placeholders})",
        [subject_id, *question_ids],
    ).fetchall()

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

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT id, role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user or user["role"] != "student":
        flash("Only registered student users can be deleted.", "error")
        return redirect(url_for("admin_dashboard"))

    db.execute("DELETE FROM results WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))

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
            flash(f"'{name}' subject added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("This subject already exists!", "error")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_subject/<int:s_id>")
def delete_subject(s_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db      = get_db()
    q_count = db.execute("SELECT COUNT(*) FROM questions WHERE subject_id = ?", (s_id,)).fetchone()[0]

    if q_count > 0:
        flash(f"This subject has {q_count} question(s). Please delete the questions first!", "error")
    else:
        db.execute("DELETE FROM subjects WHERE id = ?", (s_id,))
        db.commit()
        flash("Subject deleted successfully!", "success")

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
    flash("Question added successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_question/<int:q_id>")
def delete_question(q_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    db.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))

# =====================
# RUN
# =====================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
