from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURATION
# =========================================================

APP_TITLE = "IE Progress Portal"
DEPARTMENT = "Department of Industrial Engineering"
UNIVERSITY = "Anna University"

SUBMISSIONS_FILE = Path("cgpa_submissions.csv")
STUDENTS_FILE = Path("students.csv")

# ---------------------------------------------------------
# Credit structure
# ---------------------------------------------------------
# Previous credits = credits completed up to 3rd semester
# 4th semester credits = total credits in 4th semester
#
# These values are based on the structure you provided:
# Previous Credits = 66
# 4th Semester Credits = 23
# ---------------------------------------------------------

PREVIOUS_CREDITS = 66
FOURTH_SEMESTER_CREDITS = 23

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# STUDENT DATA
# =========================================================

def load_students() -> pd.DataFrame:

    students = pd.read_csv(
        STUDENTS_FILE,
        dtype={
            "registration_number": "string",
            "student_name": "string",
        },
    )

    students["registration_number"] = (
        students["registration_number"]
        .astype("string")
        .str.strip()
    )

    students["student_name"] = (
        students["student_name"]
        .astype("string")
        .str.strip()
    )

    return students


# =========================================================
# CGPA SUBMISSION FILE
# =========================================================

def ensure_submissions_file() -> None:

    if not SUBMISSIONS_FILE.exists():

        pd.DataFrame(
            columns=[
                "entry_id",
                "registration_number",
                "student_name",
                "cgpa_third_semester",
                "fourth_semester_gpa",
                "cgpa_fourth_semester",
                "submitted_at",
            ]
        ).to_csv(
            SUBMISSIONS_FILE,
            index=False,
        )


# =========================================================
# LOAD CGPA DATA
# =========================================================

def load_submissions() -> pd.DataFrame:

    ensure_submissions_file()

    submissions = pd.read_csv(
        SUBMISSIONS_FILE,
        dtype={
            "entry_id": "string",
            "registration_number": "string",
            "student_name": "string",
            "cgpa_third_semester": "float64",
            "fourth_semester_gpa": "float64",
            "cgpa_fourth_semester": "float64",
            "submitted_at": "string",
        },
    )

    # -----------------------------------------------------
    # Compatibility with old CSV
    # -----------------------------------------------------
    # Your previous file may only have:
    # cgpa_third_semester
    #
    # These columns will automatically be created if
    # they are missing.
    # -----------------------------------------------------

    if "entry_id" not in submissions.columns:

        submissions["entry_id"] = [
            str(uuid.uuid4())
            for _ in range(len(submissions))
        ]

    if "student_name" not in submissions.columns:

        submissions["student_name"] = ""

    if "cgpa_third_semester" not in submissions.columns:

        submissions["cgpa_third_semester"] = pd.NA

    if "fourth_semester_gpa" not in submissions.columns:

        submissions["fourth_semester_gpa"] = pd.NA

    if "cgpa_fourth_semester" not in submissions.columns:

        submissions["cgpa_fourth_semester"] = pd.NA

    if "submitted_at" not in submissions.columns:

        submissions["submitted_at"] = ""

    # -----------------------------------------------------
    # Clean columns
    # -----------------------------------------------------

    submissions["registration_number"] = (
        submissions["registration_number"]
        .astype("string")
        .str.strip()
    )

    submissions["student_name"] = (
        submissions["student_name"]
        .astype("string")
        .str.strip()
    )

    submissions["cgpa_third_semester"] = pd.to_numeric(
        submissions["cgpa_third_semester"],
        errors="coerce",
    )

    submissions["fourth_semester_gpa"] = pd.to_numeric(
        submissions["fourth_semester_gpa"],
        errors="coerce",
    )

    submissions["cgpa_fourth_semester"] = pd.to_numeric(
        submissions["cgpa_fourth_semester"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Keep latest record for each student
    # -----------------------------------------------------

    submissions = submissions.drop_duplicates(
        subset=["registration_number"],
        keep="last",
    ).reset_index(drop=True)

    return submissions


# =========================================================
# SAVE CGPA DATA
# =========================================================

def save_submissions(
    submissions: pd.DataFrame,
) -> None:

    temp_file = SUBMISSIONS_FILE.with_suffix(".tmp")

    submissions.to_csv(
        temp_file,
        index=False,
    )

    os.replace(
        temp_file,
        SUBMISSIONS_FILE,
    )


# =========================================================
# CALCULATE CGPA UP TO 4TH SEMESTER
# =========================================================

def calculate_fourth_semester_cgpa(
    previous_cgpa: float,
    fourth_semester_gpa: float,
) -> float:

    total_credits = (
        PREVIOUS_CREDITS
        + FOURTH_SEMESTER_CREDITS
    )

    calculated_cgpa = (
        (
            previous_cgpa
            * PREVIOUS_CREDITS
        )
        +
        (
            fourth_semester_gpa
            * FOURTH_SEMESTER_CREDITS
        )
    ) / total_credits

    # Keep CGPA within 0–10
    calculated_cgpa = max(
        0.0,
        min(10.0, calculated_cgpa),
    )

    return round(
        calculated_cgpa,
        2,
    )


# =========================================================
# FIND STUDENT
# =========================================================

def format_registration_number(
    value: str,
) -> str:

    return str(value).strip()


def find_student(
    students: pd.DataFrame,
    registration_number: str,
) -> pd.Series | None:

    registration_number = (
        format_registration_number(
            registration_number
        )
    )

    matches = students[
        students["registration_number"]
        == registration_number
    ]

    if matches.empty:

        return None

    return matches.iloc[0]


# =========================================================
# RESET STUDENT SEARCH
# =========================================================

def reset_student_lookup() -> None:

    st.session_state.student = None
    st.session_state.lookup_message = None


# =========================================================
# SAVE / UPDATE STUDENT RECORD
# =========================================================

def save_student_record(
    registration_number: str,
    student_name: str,
    cgpa_third: float,
    fourth_gpa: float,
    entry_id: str | None = None,
) -> None:

    submissions = load_submissions()

    registration_number = (
        format_registration_number(
            registration_number
        )
    )

    # -----------------------------------------------------
    # Calculate CGPA up to 4th semester
    # -----------------------------------------------------

    cgpa_fourth = calculate_fourth_semester_cgpa(
        previous_cgpa=float(cgpa_third),
        fourth_semester_gpa=float(fourth_gpa),
    )

    # -----------------------------------------------------
    # Remove old record for this student
    # -----------------------------------------------------

    submissions = submissions[
        submissions["registration_number"]
        != registration_number
    ]

    # -----------------------------------------------------
    # Create updated record
    # -----------------------------------------------------

    new_entry = pd.DataFrame(
        [
            {
                "entry_id":
                    entry_id
                    if entry_id
                    else str(uuid.uuid4()),

                "registration_number":
                    registration_number,

                "student_name":
                    student_name,

                "cgpa_third_semester":
                    round(
                        float(cgpa_third),
                        2,
                    ),

                "fourth_semester_gpa":
                    round(
                        float(fourth_gpa),
                        2,
                    ),

                "cgpa_fourth_semester":
                    cgpa_fourth,

                "submitted_at":
                    datetime.now().strftime(
                        "%d %b %Y, %I:%M:%S %p"
                    ),
            }
        ]
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    submissions = pd.concat(
        [
            submissions,
            new_entry,
        ],
        ignore_index=True,
    )

    save_submissions(
        submissions
    )


# =========================================================
# BRAND HEADER
# =========================================================

def render_brand_header() -> None:

    st.title(
        APP_TITLE
    )

    st.caption(
        f"{DEPARTMENT} · {UNIVERSITY}"
    )

    st.divider()


# =========================================================
# STUDENT PORTAL
# =========================================================

def render_student_portal(
    students: pd.DataFrame,
) -> None:

    st.header(
        "Student access"
    )

    st.write(
        "Enter your registration number to view your academic progress."
    )

    # -----------------------------------------------------
    # Registration number
    # -----------------------------------------------------

    with st.form(
        "student_lookup_form",
        clear_on_submit=False,
    ):

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

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if lookup_clicked:

        student = find_student(
            students,
            registration_number,
        )

        if student is None:

            st.session_state.student = None

            st.error(
                "We could not find that registration number. "
                "Please check the number and try again."
            )

        else:

            st.session_state.student = {
                "registration_number":
                    student["registration_number"],

                "student_name":
                    student["student_name"],
            }

            st.rerun()

    # -----------------------------------------------------
    # Student session
    # -----------------------------------------------------

    student = st.session_state.get(
        "student"
    )

    if not student:

        st.info(
            "Your registration number is used only to "
            "find your name in the department list."
        )

        return

    # -----------------------------------------------------
    # Load student's CGPA record
    # -----------------------------------------------------

    submissions = load_submissions()

    student_record = submissions[
        submissions["registration_number"]
        == student["registration_number"]
    ]

    # -----------------------------------------------------
    # Student details
    # -----------------------------------------------------

    st.success(
        f"Record found · "
        f"{student['registration_number']}"
    )

    st.subheader(
        f"Welcome, "
        f"{student['student_name'].title()}"
    )

    st.write(
        "Here you can view your CGPA progress "
        "and understand how your 4th-semester "
        "result affects your overall CGPA."
    )

    st.divider()

    # =====================================================
    # NO RECORD
    # =====================================================

    if student_record.empty:

        st.info(
            "Your CGPA up to 3rd semester has not "
            "been submitted yet."
        )

    else:

        record = student_record.iloc[0]

        previous_cgpa = record[
            "cgpa_third_semester"
        ]

        fourth_gpa = record[
            "fourth_semester_gpa"
        ]

        fourth_cgpa = record[
            "cgpa_fourth_semester"
        ]

        # =================================================
        # PREVIOUS CGPA
        # =================================================

        st.subheader(
            "Academic Progress"
        )

        col1, col2 = st.columns(2)

        with col1:

            if pd.notna(previous_cgpa):

                st.metric(
                    "CGPA up to 3rd Semester",
                    f"{float(previous_cgpa):.2f}",
                )

            else:

                st.metric(
                    "CGPA up to 3rd Semester",
                    "Not available",
                )

        with col2:

            st.metric(
                "Previous Credits",
                PREVIOUS_CREDITS,
            )

        # =================================================
        # 4TH SEMESTER INFORMATION
        # =================================================

        st.divider()

        st.subheader(
            "4th Semester"
        )

        col3, col4 = st.columns(2)

        with col3:

            if pd.notna(fourth_gpa):

                st.metric(
                    "4th Semester GPA",
                    f"{float(fourth_gpa):.2f}",
                )

            else:

                st.metric(
                    "4th Semester GPA",
                    "Not updated",
                )

        with col4:

            st.metric(
                "4th Semester Credits",
                FOURTH_SEMESTER_CREDITS,
            )

        # =================================================
        # CALCULATED CGPA
        # =================================================

        st.divider()

        st.subheader(
            "CGPA up to 4th Semester"
        )

        if (
            pd.notna(previous_cgpa)
            and pd.notna(fourth_gpa)
        ):

            calculated_cgpa = (
                calculate_fourth_semester_cgpa(
                    previous_cgpa=float(
                        previous_cgpa
                    ),
                    fourth_semester_gpa=float(
                        fourth_gpa
                    ),
                )
            )

            # -------------------------------------------------
            # Main result
            # -------------------------------------------------

            st.success(
                f"Your CGPA up to 4th Semester is "
                f"{calculated_cgpa:.2f}"
            )

            # -------------------------------------------------
            # Formula
            # -------------------------------------------------

            st.write(
                "### How was your CGPA calculated?"
            )

            st.write(
                "Your previous CGPA is combined with "
                "your 4th Semester GPA using the "
                "corresponding credit weights."
            )

            st.latex(
                rf"""
                \mathrm{{CGPA}}_{{4th}}
                =
                \frac{{(
                {float(previous_cgpa):.2f}
                \times
                {PREVIOUS_CREDITS}
                )
                +
                (
                {float(fourth_gpa):.2f}
                \times
                {FOURTH_SEMESTER_CREDITS}
                )}}
                {{
                {PREVIOUS_CREDITS}
                +
                {FOURTH_SEMESTER_CREDITS}
                }}
                """
            )

            st.latex(
                rf"""
                =
                \frac{{(
                {float(previous_cgpa):.2f}
                \times
                {PREVIOUS_CREDITS}
                )
                +
                (
                {float(fourth_gpa):.2f}
                \times
                {FOURTH_SEMESTER_CREDITS}
                )}}
                {{
                {PREVIOUS_CREDITS + FOURTH_SEMESTER_CREDITS}
                }}
                """
            )

            previous_weighted_points = (
                float(previous_cgpa)
                * PREVIOUS_CREDITS
            )

            fourth_weighted_points = (
                float(fourth_gpa)
                * FOURTH_SEMESTER_CREDITS
            )

            total_weighted_points = (
                previous_weighted_points
                + fourth_weighted_points
            )

            st.write(
                f"**Previous CGPA contribution:** "
                f"{float(previous_cgpa):.2f} × "
                f"{PREVIOUS_CREDITS} = "
                f"{previous_weighted_points:.2f}"
            )

            st.write(
                f"**4th Semester contribution:** "
                f"{float(fourth_gpa):.2f} × "
                f"{FOURTH_SEMESTER_CREDITS} = "
                f"{fourth_weighted_points:.2f}"
            )

            st.write(
                f"**Total weighted points:** "
                f"{total_weighted_points:.2f}"
            )

            st.write(
                f"**Total credits:** "
                f"{PREVIOUS_CREDITS + FOURTH_SEMESTER_CREDITS}"
            )

            st.latex(
                rf"""
                \mathrm{{CGPA}}_{{4th}}
                =
                \frac{{{total_weighted_points:.2f}}}
                {{{PREVIOUS_CREDITS + FOURTH_SEMESTER_CREDITS}}}
                =
                \mathbf{{{calculated_cgpa:.2f}}}
                """
            )

            # -------------------------------------------------
            # Simple table
            # -------------------------------------------------

            st.write(
                "### Summary"
            )

            summary = pd.DataFrame(
                [
                    {
                        "Particular":
                            "CGPA up to 3rd Semester",

                        "Value":
                            f"{float(previous_cgpa):.2f}",
                    },
                    {
                        "Particular":
                            "Previous Credits",

                        "Value":
                            str(PREVIOUS_CREDITS),
                    },
                    {
                        "Particular":
                            "4th Semester GPA",

                        "Value":
                            f"{float(fourth_gpa):.2f}",
                    },
                    {
                        "Particular":
                            "4th Semester Credits",

                        "Value":
                            str(
                                FOURTH_SEMESTER_CREDITS
                            ),
                    },
                    {
                        "Particular":
                            "Total Credits",

                        "Value":
                            str(
                                PREVIOUS_CREDITS
                                + FOURTH_SEMESTER_CREDITS
                            ),
                    },
                    {
                        "Particular":
                            "CGPA up to 4th Semester",

                        "Value":
                            f"{calculated_cgpa:.2f}",
                    },
                ]
            )

            st.table(
                summary
            )

        else:

            st.warning(
                "Your 4th Semester GPA has not been "
                "updated by the administrator yet."
            )

            st.info(
                "Once your 4th Semester GPA is entered, "
                "your CGPA up to 4th Semester will be "
                "calculated automatically."
            )

    # =====================================================
    # SEARCH ANOTHER STUDENT
    # =====================================================

    st.divider()

    if st.button(
        "Search another registration number",
        use_container_width=True,
    ):

        reset_student_lookup()

        st.rerun()


# =========================================================
# ADMIN PORTAL
# =========================================================

def render_admin_portal() -> None:

    st.header(
        "Admin access"
    )

    st.write(
        "Authorized staff can manage student CGPA "
        "and 4th Semester GPA records."
    )

    # =====================================================
    # ADMIN WARNING
    # =====================================================

    if not st.session_state.get(
        "admin_warning_acknowledged",
        False,
    ):

        st.warning(
            "Are you an authorized admin? This area contains "
            "confidential student academic records and is "
            "only for department administrators."
        )

        if st.button(
            "Okay, I am an authorized admin",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.admin_warning_acknowledged = True

            st.rerun()

        return

    # =====================================================
    # ADMIN LOGIN
    # =====================================================

    if not st.session_state.get(
        "admin_authenticated",
        False,
    ):

        with st.form(
            "admin_login_form"
        ):

            username = st.text_input(
                "Username"
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            login_clicked = st.form_submit_button(
                "Sign in as admin",
                type="primary",
                use_container_width=True,
            )

        if login_clicked:

            if (
                username == ADMIN_USERNAME
                and password == ADMIN_PASSWORD
            ):

                st.session_state.admin_authenticated = True

                st.rerun()

            else:

                st.error(
                    "Incorrect admin username or password."
                )

        return

    # =====================================================
    # AUTHENTICATED ADMIN
    # =====================================================

    submissions = load_submissions()

    students = load_students()

    st.success(
        "Admin session active"
    )

    top_left, top_right = st.columns(
        [3, 1]
    )

    with top_left:

        st.subheader(
            "Student CGPA Management"
        )

    with top_right:

        if st.button(
            "Sign out",
            use_container_width=True,
        ):

            st.session_state.admin_authenticated = False

            st.session_state.admin_warning_acknowledged = False

            st.rerun()

    # =====================================================
    # ADD / EDIT STUDENT RECORD
    # =====================================================

    st.divider()

    st.subheader(
        "Add / Edit Student Record"
    )

    st.write(
        "The student submits their CGPA up to 3rd semester. "
        "Admin only needs to enter or update the 4th Semester GPA."
    )

    st.info(
        f"Credit structure: "
        f"{PREVIOUS_CREDITS} previous credits + "
        f"{FOURTH_SEMESTER_CREDITS} 4th semester credits"
    )

    # -----------------------------------------------------
    # Registration numbers
    # -----------------------------------------------------

    registration_numbers = (
        students[
            "registration_number"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not registration_numbers:

        st.error(
            "No students were found in students.csv."
        )

        return

    # -----------------------------------------------------
    # Select student
    # -----------------------------------------------------

    selected_registration = st.selectbox(
        "Select registration number",
        options=registration_numbers,
        index=None,
        placeholder="Select a student",
        key="admin_selected_student",
    )

    if selected_registration:

        selected_student = find_student(
            students,
            selected_registration,
        )

        if selected_student is None:

            st.error(
                "Student record could not be found."
            )

        else:

            student_name = selected_student[
                "student_name"
            ]

            st.success(
                f"Student: {student_name.title()}"
            )

            # -------------------------------------------------
            # Find existing submission
            # -------------------------------------------------

            existing = submissions[
                submissions["registration_number"]
                == selected_registration
            ]

            if not existing.empty:

                existing_record = existing.iloc[0]

                existing_third = (
                    existing_record[
                        "cgpa_third_semester"
                    ]
                )

                existing_fourth_gpa = (
                    existing_record[
                        "fourth_semester_gpa"
                    ]
                )

                existing_entry_id = (
                    existing_record[
                        "entry_id"
                    ]
                )

            else:

                existing_third = pd.NA

                existing_fourth_gpa = pd.NA

                existing_entry_id = None

            # =================================================
            # STUDENT'S PREVIOUS CGPA
            # =================================================

            st.write(
                "### Student's CGPA up to 3rd Semester"
            )

            if pd.notna(existing_third):

                st.metric(
                    "Previous CGPA",
                    f"{float(existing_third):.2f}",
                )

            else:

                st.warning(
                    "This student has not submitted "
                    "their CGPA up to 3rd semester yet."
                )

            # =================================================
            # ADMIN 4TH SEMESTER GPA
            # =================================================

            st.write(
                "### 4th Semester GPA"
            )

            if pd.notna(existing_fourth_gpa):

                default_fourth_gpa = float(
                    existing_fourth_gpa
                )

            else:

                default_fourth_gpa = 0.0

            fourth_gpa = st.number_input(
                "Enter / update 4th Semester GPA",
                min_value=0.0,
                max_value=10.0,
                value=default_fourth_gpa,
                step=0.01,
                format="%.2f",
                key=f"fourth_gpa_{selected_registration}",
                help="Enter the GPA obtained by the student in the 4th semester.",
            )

            st.caption(
                f"4th Semester Credits: "
                f"{FOURTH_SEMESTER_CREDITS}"
            )

            # =================================================
            # PREVIEW CALCULATION
            # =================================================

            if pd.notna(existing_third):

                preview_cgpa = (
                    calculate_fourth_semester_cgpa(
                        previous_cgpa=float(
                            existing_third
                        ),
                        fourth_semester_gpa=float(
                            fourth_gpa
                        ),
                    )
                )

                st.write(
                    "### Calculated CGPA Preview"
                )

                st.latex(
                    rf"""
                    CGPA_{{4th}}
                    =
                    \frac{{(
                    {float(existing_third):.2f}
                    \times
                    {PREVIOUS_CREDITS}
                    )
                    +
                    (
                    {float(fourth_gpa):.2f}
                    \times
                    {FOURTH_SEMESTER_CREDITS}
                    )}}
                    {{
                    {PREVIOUS_CREDITS + FOURTH_SEMESTER_CREDITS}
                    }}
                    =
                    {preview_cgpa:.2f}
                    """
                )

                st.success(
                    f"Calculated CGPA up to 4th Semester: "
                    f"{preview_cgpa:.2f}"
                )

            else:

                st.info(
                    "Enter the student's 3rd semester CGPA "
                    "from the student submission before calculating."
                )

            # =================================================
            # SAVE / UPDATE
            # =================================================

            if st.button(
                "Submit / Update 4th Semester GPA",
                type="primary",
                use_container_width=True,
            ):

                if pd.isna(existing_third):

                    st.error(
                        "Cannot save the 4th Semester GPA "
                        "because the student's CGPA up to "
                        "3rd semester is not available."
                    )

                else:

                    save_student_record(
                        registration_number=
                            selected_registration,

                        student_name=
                            student_name,

                        cgpa_third=
                            float(existing_third),

                        fourth_gpa=
                            float(fourth_gpa),

                        entry_id=
                            existing_entry_id,
                    )

                    st.success(
                        f"4th Semester GPA for "
                        f"{student_name.title()} "
                        f"has been saved successfully."
                    )

                    st.rerun()

    # =====================================================
    # ALL RECORDS
    # =====================================================

    st.divider()

    st.subheader(
        "All Student CGPA Records"
    )

    submissions = load_submissions()

    if submissions.empty:

        st.info(
            "No student CGPA records have been submitted yet."
        )

    else:

        # =================================================
        # METRICS
        # =================================================

        metric_one, metric_two, metric_three = st.columns(3)

        metric_one.metric(
            "Total entries",
            len(submissions),
        )

        metric_two.metric(
            "Students represented",
            submissions[
                "registration_number"
            ].nunique(),
        )

        fourth_gpa_values = submissions[
            "fourth_semester_gpa"
        ].dropna()

        if not fourth_gpa_values.empty:

            average_fourth_gpa = (
                fourth_gpa_values.mean()
            )

            metric_three.metric(
                "Average 4th Sem GPA",
                f"{average_fourth_gpa:.2f}",
            )

        else:

            metric_three.metric(
                "Average 4th Sem GPA",
                "N/A",
            )

        # =================================================
        # SEARCH
        # =================================================

        search = st.text_input(
            "Filter by registration number or student name",
            placeholder="Type to filter the table",
            key="admin_search",
        ).strip().lower()

        visible = submissions

        if search:

            visible = submissions[
                submissions[
                    "registration_number"
                ]
                .astype(str)
                .str.lower()
                .str.contains(
                    search,
                    na=False,
                )
                |
                submissions[
                    "student_name"
                ]
                .astype(str)
                .str.lower()
                .str.contains(
                    search,
                    na=False,
                )
            ]

        # =================================================
        # DISPLAY TABLE
        # =================================================

        display = visible[
            [
                "registration_number",
                "student_name",
                "cgpa_third_semester",
                "fourth_semester_gpa",
                "cgpa_fourth_semester",
                "submitted_at",
            ]
        ].rename(
            columns={
                "registration_number":
                    "Registration Number",

                "student_name":
                    "Student Name",

                "cgpa_third_semester":
                    "CGPA up to 3rd Semester",

                "fourth_semester_gpa":
                    "4th Semester GPA",

                "cgpa_fourth_semester":
                    "CGPA up to 4th Semester",

                "submitted_at":
                    "Last Updated",
            }
        )

        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
            column_config={

                "CGPA up to 3rd Semester":
                    st.column_config.NumberColumn(
                        format="%.2f"
                    ),

                "4th Semester GPA":
                    st.column_config.NumberColumn(
                        format="%.2f"
                    ),

                "CGPA up to 4th Semester":
                    st.column_config.NumberColumn(
                        format="%.2f"
                    ),
            },
        )

        # =================================================
        # DOWNLOAD CSV
        # =================================================

        csv_data = submissions.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download all entries as CSV",
            data=csv_data,
            file_name="cgpa_submissions.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # =================================================
        # DELETE RECORD
        # =================================================

        st.divider()

        st.subheader(
            "Delete Student Record"
        )

        st.caption(
            "Deleting a record removes the student's "
            "CGPA and 4th Semester GPA record."
        )

        delete_options = visible[
            "entry_id"
        ].tolist()

        if delete_options:

            def delete_option_label(
                entry_id: str,
            ) -> str:

                row = submissions[
                    submissions["entry_id"]
                    == entry_id
                ].iloc[0]

                third_value = row[
                    "cgpa_third_semester"
                ]

                fourth_gpa_value = row[
                    "fourth_semester_gpa"
                ]

                if pd.notna(third_value):

                    third_text = (
                        f"{float(third_value):.2f}"
                    )

                else:

                    third_text = "N/A"

                if pd.notna(fourth_gpa_value):

                    fourth_text = (
                        f"{float(fourth_gpa_value):.2f}"
                    )

                else:

                    fourth_text = "Not updated"

                return (
                    f"{row['registration_number']} · "
                    f"{row['student_name']} · "
                    f"3rd CGPA: {third_text} · "
                    f"4th GPA: {fourth_text}"
                )

            selected_delete_id = st.selectbox(
                "Choose student to delete",
                options=delete_options,
                format_func=delete_option_label,
                key="delete_student",
            )

            confirm_delete = st.checkbox(
                "I understand this deletion cannot be undone.",
                key="confirm_delete",
            )

            if st.button(
                "Delete Selected Student",
                type="secondary",
                disabled=not confirm_delete,
                use_container_width=True,
            ):

                remaining = submissions[
                    submissions["entry_id"]
                    != selected_delete_id
                ]

                save_submissions(
                    remaining
                )

                st.success(
                    "Student CGPA record deleted successfully."
                )

                st.rerun()


# =========================================================
# MAIN
# =========================================================

def main() -> None:

    render_brand_header()

    students = load_students()

    student_tab, admin_tab = st.tabs(
        [
            "🎓 Student Portal",
            "🔐 Admin Login",
        ]
    )

    with student_tab:

        render_student_portal(
            students
        )

    with admin_tab:

        render_admin_portal()

    st.divider()

    st.caption(
        "For academic record collection · "
        "Please enter your CGPA carefully."
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    main()
