from __future__ import annotations

import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_TITLE = "IE Progress Portal"
DEPARTMENT = "Department of Industrial Engineering"
UNIVERSITY = "Anna University"
SUBMISSIONS_FILE = Path("cgpa_submissions.csv")
STUDENTS_FILE = Path("students.csv")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def load_students() -> pd.DataFrame:
    students = pd.read_csv(
        STUDENTS_FILE,
        dtype={"registration_number": "string", "student_name": "string"},
    )
    students["registration_number"] = students["registration_number"].str.strip()
    students["student_name"] = students["student_name"].str.strip()
    return students


def ensure_submissions_file() -> None:
    if not SUBMISSIONS_FILE.exists():
        pd.DataFrame(
            columns=[
                "entry_id",
                "registration_number",
                "student_name",
                "cgpa_third_semester",
                "submitted_at",
            ]
        ).to_csv(SUBMISSIONS_FILE, index=False)


def load_submissions() -> pd.DataFrame:
    ensure_submissions_file()
    return pd.read_csv(
        SUBMISSIONS_FILE,
        dtype={
            "entry_id": "string",
            "registration_number": "string",
            "student_name": "string",
            "cgpa_third_semester": "float64",
            "submitted_at": "string",
        },
    )


def save_submissions(submissions: pd.DataFrame) -> None:
    temp_file = SUBMISSIONS_FILE.with_suffix(".tmp")
    submissions.to_csv(temp_file, index=False)
    os.replace(temp_file, SUBMISSIONS_FILE)


def format_registration_number(value: str) -> str:
    return str(value).strip()


def find_student(students: pd.DataFrame, registration_number: str) -> pd.Series | None:
    matches = students[
        students["registration_number"]
        == format_registration_number(registration_number)
    ]
    return matches.iloc[0] if not matches.empty else None


def reset_student_lookup() -> None:
    st.session_state.student = None
    st.session_state.lookup_message = None


def submit_cgpa(registration_number: str, student_name: str, cgpa: float) -> None:
    submissions = load_submissions()
    new_entry = pd.DataFrame(
        [
            {
                "entry_id": str(uuid.uuid4()),
                "registration_number": registration_number,
                "student_name": student_name,
                "cgpa_third_semester": round(float(cgpa), 2),
                "submitted_at": datetime.now().strftime("%d %b %Y, %I:%M:%S %p"),
            }
        ]
    )
    save_submissions(pd.concat([submissions, new_entry], ignore_index=True))


def render_brand_header() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎓",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.title(APP_TITLE)
    st.caption(f"{DEPARTMENT} · {UNIVERSITY}")
    st.divider()


def render_student_portal(students: pd.DataFrame) -> None:
    st.header("Student access")
    st.write("Enter your registration number to open your personal welcome page.")

    with st.form("student_lookup_form", clear_on_submit=False):
        registration_number = st.text_input(
            "Registration number",
            placeholder="Example: 2024108001",
            max_chars=10,
        ).strip()
        lookup_clicked = st.form_submit_button(
            "Find my record",
            type="primary",
            use_container_width=True,
        )

    if lookup_clicked:
        student = find_student(students, registration_number)
        if student is None:
            st.session_state.student = None
            st.error(
                "We could not find that registration number. Please check the number and try again."
            )
        else:
            st.session_state.student = {
                "registration_number": student["registration_number"],
                "student_name": student["student_name"],
            }
            st.rerun()

    student = st.session_state.get("student")
    if not student:
        st.info("Your registration number is used only to find your name in the department list.")
        return

    st.success(f"Record found · {student['registration_number']}")
    st.subheader(f"Welcome, {student['student_name'].title()}")
    st.write(
        "Every step forward counts. Keep learning, keep improving, and trust the progress you are making."
    )

    with st.form("cgpa_submission_form", clear_on_submit=True):
        cgpa = st.number_input(
            "CGPA up to 3rd semester",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            help="Enter a value between 0.00 and 10.00.",
        )
        submitted = st.form_submit_button(
            "Submit CGPA",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        submit_cgpa(
            student["registration_number"],
            student["student_name"],
            cgpa,
        )
        st.success("Your CGPA was submitted successfully.")
        st.caption("You can submit again whenever you need to update the record.")

    if st.button("Search another registration number"):
        reset_student_lookup()
        st.rerun()


def render_admin_portal() -> None:
    st.header("Admin access")
    st.write("Authorized staff can review and manage all submitted CGPA entries.")

    if not st.session_state.get("admin_authenticated", False):
        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button(
                "Sign in as admin",
                type="primary",
                use_container_width=True,
            )

        if login_clicked:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect admin username or password.")
        return

    submissions = load_submissions()
    st.success("Admin session active")
    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.subheader("Submitted CGPA entries")
    with top_right:
        if st.button("Sign out", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

    if submissions.empty:
        st.info("No CGPA entries have been submitted yet.")
        return

    submissions = submissions.sort_values(
        by=["registration_number", "submitted_at"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)

    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Total entries", len(submissions))
    metric_two.metric("Students represented", submissions["registration_number"].nunique())
    metric_three.metric("Average CGPA", f"{submissions['cgpa_third_semester'].mean():.2f}")

    search = st.text_input(
        "Filter by registration number or student name",
        placeholder="Type to filter the table",
    ).strip().lower()
    visible = submissions
    if search:
        visible = submissions[
            submissions["registration_number"].str.lower().str.contains(search, na=False)
            | submissions["student_name"].str.lower().str.contains(search, na=False)
        ]

    display = visible[
        [
            "registration_number",
            "student_name",
            "cgpa_third_semester",
            "submitted_at",
        ]
    ].rename(
        columns={
            "registration_number": "Registration number",
            "student_name": "Student name",
            "cgpa_third_semester": "CGPA up to 3rd semester",
            "submitted_at": "Submitted at",
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "CGPA up to 3rd semester": st.column_config.NumberColumn(
                format="%.2f"
            )
        },
    )

    csv_data = submissions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download all entries as CSV",
        data=csv_data,
        file_name="cgpa_submissions.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Delete an entry")
    st.caption("Deleting an entry removes only that submission. The student can submit again afterward.")

    options = visible if not visible.empty else submissions
    option_ids = options["entry_id"].tolist()

    def option_label(entry_id: str) -> str:
        row = submissions[submissions["entry_id"] == entry_id].iloc[0]
        return (
            f"{row['registration_number']} · {row['student_name']} · "
            f"CGPA {row['cgpa_third_semester']:.2f} · {row['submitted_at']}"
        )

    selected_entry_id = st.selectbox(
        "Choose the submission to delete",
        options=option_ids,
        format_func=option_label,
    )
    confirm_delete = st.checkbox("I understand this deletion cannot be undone.")
    if st.button("Delete selected entry", type="secondary", disabled=not confirm_delete):
        remaining = submissions[submissions["entry_id"] != selected_entry_id]
        save_submissions(remaining)
        st.success("The selected entry was deleted.")
        st.rerun()


def main() -> None:
    render_brand_header()
    students = load_students()

    student_tab, admin_tab = st.tabs(["Student portal", "Admin login"])
    with student_tab:
        render_student_portal(students)
    with admin_tab:
        render_admin_portal()

    st.divider()
    st.caption("For academic record collection · Please enter your CGPA carefully.")


if __name__ == "__main__":
    main()