"""PART 1 - DATA. Creates the database tables and fills them with FAKE demo data."""
import os
import random
import sqlite3

DB_PATH = os.environ.get("CLASSBRAIN_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "classbrain.db"))


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


def init_db():
    conn = connect()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL, subject TEXT NOT NULL, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assessment_topics (
        id INTEGER PRIMARY KEY, assessment_id INTEGER NOT NULL, topic TEXT NOT NULL, max_marks REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS scores (
        student_id INTEGER NOT NULL, assessment_topic_id INTEGER NOT NULL, marks REAL NOT NULL,
        PRIMARY KEY (student_id, assessment_topic_id));
    """)
    conn.commit()
    conn.close()


def seed_demo():
    """Only runs if the database is empty. All names and marks are made up."""
    conn = connect()
    if conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0] > 0:
        conn.close()
        return
    rnd = random.Random(42)  # fixed seed = same fake data every time
    conn.execute("INSERT INTO classes (id, name) VALUES (1, 'Class 11 Commerce')")
    first = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Isha", "Arjun", "Anaya", "Vihaan", "Saanvi",
             "Aditya", "Kiara", "Reyansh", "Myra", "Ishaan", "Tara", "Dhruv", "Navya", "Krish", "Riya"]
    last = ["Sharma", "Iyer", "Nair", "Patel", "Reddy", "Khan"]
    names = [f"{first[i % 20]} {last[(i * 7 + i // 20) % 6]}" for i in range(30)]
    for i, n in enumerate(names, start=1):
        conn.execute("INSERT INTO students (id, class_id, name) VALUES (?, 1, ?)", (i, n))
    conn.execute("INSERT INTO assessments (id, class_id, subject, name) VALUES (1, 1, 'Economics', 'Unit Test 1')")
    # (topic, max marks, typical % the fake class scores)
    topics = [("Introduction to Economics", 10, 0.85), ("Basic Concepts", 10, 0.78),
              ("Demand", 15, 0.52), ("Elasticity", 15, 0.38), ("Application Questions", 10, 0.42)]
    for t_id, (topic, mx, _) in enumerate(topics, start=1):
        conn.execute("INSERT INTO assessment_topics (id, assessment_id, topic, max_marks) VALUES (?, 1, ?, ?)",
                     (t_id, topic, mx))
    for s_id in range(1, 31):
        ability = rnd.uniform(-0.18, 0.18)  # some students stronger, some weaker overall
        for t_id, (_, mx, typical) in enumerate(topics, start=1):
            pct = min(1.0, max(0.0, typical + ability + rnd.uniform(-0.12, 0.12)))
            conn.execute("INSERT INTO scores (student_id, assessment_topic_id, marks) VALUES (?, ?, ?)",
                         (s_id, t_id, round(pct * mx)))
    # --- second fake test, a few weeks later (different topics, partly overlapping) ---
    conn.execute("INSERT INTO assessments (id, class_id, subject, name) VALUES (2, 1, 'Economics', 'Unit Test 2')")
    topics2 = [("Demand", 15, 0.58), ("Elasticity", 15, 0.55), ("Application Questions", 10, 0.43), ("Supply", 15, 0.50)]
    for i, (topic, mx, _) in enumerate(topics2):
        conn.execute("INSERT INTO assessment_topics (id, assessment_id, topic, max_marks) VALUES (?, 2, ?, ?)",
                     (6 + i, topic, mx))
    rnd2 = random.Random(7)
    for s_id in range(1, 31):
        ability = rnd.uniform(-0.18, 0.18) * 0.5 + rnd2.uniform(-0.1, 0.1)
        for i, (_, mx, typical) in enumerate(topics2):
            pct = min(1.0, max(0.0, typical + ability + rnd2.uniform(-0.12, 0.12)))
            conn.execute("INSERT INTO scores (student_id, assessment_topic_id, marks) VALUES (?, ?, ?)",
                         (s_id, 6 + i, round(pct * mx)))
    # --- three more subjects. Chapter names are ILLUSTRATIVE: replace them with your school's syllabus. ---
    rnd3 = random.Random(2024)
    base = {sid: rnd3.uniform(-0.15, 0.15) for sid in range(1, 31)}  # a student's general level, shared by subjects
    others = {
        "Accountancy": [
            ("Unit Test 1", [("Introduction to Accounting", 8, .82), ("Theory Base of Accounting", 10, .70),
                             ("Recording of Transactions", 12, .58), ("Trial Balance and Rectification of Errors", 10, .40)]),
            ("Unit Test 2", [("Recording of Transactions", 12, .62), ("Trial Balance and Rectification of Errors", 10, .52),
                             ("Bank Reconciliation Statement", 10, .36), ("Depreciation", 8, .55)])],
        "Business Studies": [
            ("Unit Test 1", [("Business, Trade and Commerce", 8, .80), ("Forms of Business Organisations", 12, .66),
                             ("Public, Private and Global Enterprises", 10, .55), ("Business Services", 10, .72)]),
            ("Unit Test 2", [("Forms of Business Organisations", 12, .72), ("Business Services", 10, .70),
                             ("Emerging Modes of Business", 8, .60), ("Social Responsibilities and Business Ethics", 10, .48)])],
        "English": [
            ("Unit Test 1", [("Reading Comprehension", 10, .74), ("Writing Skills", 10, .50),
                             ("Grammar", 10, .66), ("Literature", 10, .60)]),
            ("Unit Test 2", [("Reading Comprehension", 10, .76), ("Writing Skills", 10, .58),
                             ("Grammar", 10, .63), ("Literature", 10, .52)])],
    }
    for subject, tests in others.items():
        for test_name, tops in tests:
            a_id = conn.execute("INSERT INTO assessments (class_id, subject, name) VALUES (1, ?, ?)",
                                (subject, test_name)).lastrowid
            for topic, mx, typical in tops:
                t_id = conn.execute("INSERT INTO assessment_topics (assessment_id, topic, max_marks) VALUES (?, ?, ?)",
                                    (a_id, topic, mx)).lastrowid
                for sid in range(1, 31):
                    pct = min(1.0, max(0.0, typical + base[sid] + rnd3.uniform(-0.14, 0.14)))
                    conn.execute("INSERT INTO scores (student_id, assessment_topic_id, marks) VALUES (?, ?, ?)",
                                 (sid, t_id, round(pct * mx)))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_demo()
    print("Database ready:", DB_PATH)
