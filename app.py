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

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# CREDIT STRUCTURE
# =========================================================

# Credits completed up to 3rd semester
PREVIOUS_CREDITS = 66

# Credits in 4th semester
FOURTH_SEMESTER_CREDITS = 23

# Total credits after 4th semester
TOTAL_CREDITS = (
    PREVIOUS_CREDITS
    + FOURTH_SEMESTER_CREDITS
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# LOAD STUDENTS
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
# CREATE SUBMISSION FILE IF IT DOES NOT EXIST
# =========================================================

def ensure_submissions_file() -> None:

    if not SUBMISSIONS_FILE.exists():

        pd.DataFrame(
            columns=[
                "entry_id",
                "registration_number",
                "student_name",
                "cgpa_third_semester",
                "submitted_at",
                "fourth_semester_gpa",
                "cgpa_fourth_semester",
            ]
        ).to_csv(
            SUBMISSIONS_FILE,
            index=False,
        )


# =========================================================
# LOAD SUBMISSIONS
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
            "submitted_at": "string",
        },
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Do NOT remove the existing student records.
    # Add the new columns only if they do not exist.
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

    if "submitted_at" not in submissions.columns:

        submissions["submitted_at"] = ""

    # -----------------------------------------------------
    # NEW 4TH SEMESTER COLUMNS
    # -----------------------------------------------------

    if "fourth_semester_gpa" not in submissions.columns:

        submissions["fourth_semester_gpa"] = pd.NA

    if "cgpa_fourth_semester" not in submissions.columns:

        submissions["cgpa_fourth_semester"] = pd.NA

    # -----------------------------------------------------
    # Clean values
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

    return submissions


# =========================================================
# SAVE SUBMISSIONS
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
# CALCULATE 4TH SEMESTER CGPA
# =========================================================

def calculate_fourth_semester_cgpa(
    previous_cgpa: float,
    fourth_semester_gpa: float,
) -> float:

    result = (
        (
            previous_cgpa
            * PREVIOUS_CREDITS
        )
        +
        (
            fourth_semester_gpa
            * FOURTH_SEMESTER_CREDITS
        )
    ) / TOTAL_CREDITS

    result = max(
        0.0,
        min(10.0, result),
    )

    return round(
        result,
        2,
    )


# =========================================================
# FIND STUDENT
# =========================================================

def find_student(
    students: pd.DataFrame,
    registration_number: str,
) -> pd.Series | None:

    registration_number = str(
        registration_number
    ).strip()

    matches = students[
        students["registration_number"]
        == registration_number
    ]

    if matches.empty:

        return None

    return matches.iloc[0]


# =========================================================
# FIND LATEST CGPA RECORD FOR STUDENT
# =========================================================

def find_latest_submission(
    submissions: pd.DataFrame,
    registration_number: str,
) -> pd.Series | None:

    matches = submissions[
        submissions["registration_number"]
        == registration_number
    ]

    if matches.empty:

        return None

    # Use the latest row in the CSV.
    return matches.iloc[-1]


# =========================================================
# RESET STUDENT LOOKUP
# =========================================================

def reset_student_lookup() -> None:

    st.session_state.student = None


# =========================================================
# STUDENT SUBMITS CGPA UP TO 3RD SEMESTER
# =========================================================

def submit_third_semester_cgpa(
    registration_number: str,
    student_name: str,
    cgpa: float,
) -> None:

    submissions = load_submissions()

    registration_number = str(
        registration_number
    ).strip()

    # -----------------------------------------------------
    # Remove previous submission for this student
    # -----------------------------------------------------
    # This preserves the original behavior where the latest
    # student submission becomes the current record.
    # -----------------------------------------------------

    submissions = submissions[
        submissions["registration_number"]
        != registration_number
    ]

    new_entry = pd.DataFrame(
        [
            {
                "entry_id":
                    str(uuid.uuid4()),

                "registration_number":
                    registration_number,

                "student_name":
                    student_name,

                "cgpa_third_semester":
                    round(
                        float(cgpa),
                        2,
                    ),

                "submitted_at":
                    datetime.now().strftime(
                        "%d %b %Y, %I:%M:%S %p"
                    ),

                # 4th semester not entered yet
                "fourth_semester_gpa":
                    pd.NA,

                "cgpa_fourth_semester":
                    pd.NA,
            }
        ]
    )

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
        "🎓 Student Access"
    )

    st.write(
        "Enter your registration number to access "
        "your academic progress."
    )

    # =====================================================
    # REGISTRATION NUMBER
    # =====================================================

    with st.form(
        "student_lookup_form",
        clear_on_submit=False,
    ):

        registration_number = st.text_input(
            "Registration Number",
            placeholder="Example: 2024108051",
            max_chars=10,
        ).strip()

        lookup_clicked = st.form_submit_button(
            "Find My Record",
            type="primary",
            use_container_width=True,
        )

    # =====================================================
    # SEARCH STUDENT
    # =====================================================

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

    # =====================================================
    # GET CURRENT STUDENT
    # =====================================================

    student = st.session_state.get(
        "student"
    )

    if not student:

        st.info(
            "Enter your registration number above "
            "to view your academic record."
        )

        return

    # =====================================================
    # LOAD STUDENT RECORD
    # =====================================================

    submissions = load_submissions()

    student_record = find_latest_submission(
        submissions,
        student["registration_number"],
    )

    # =====================================================
    # STUDENT INFORMATION
    # =====================================================

    st.success(
        f"Record Found · "
        f"{student['registration_number']}"
    )

    st.subheader(
        f"Welcome, "
        f"{student['student_name'].title()}"
    )

    # =====================================================
    # EXISTING 3RD SEMESTER SUBMISSION
    # =====================================================

    if student_record is not None:

        previous_cgpa = student_record[
            "cgpa_third_semester"
        ]

        fourth_gpa = student_record[
            "fourth_semester_gpa"
        ]

        fourth_cgpa = student_record[
            "cgpa_fourth_semester"
        ]

    else:

        previous_cgpa = None
        fourth_gpa = None
        fourth_cgpa = None

    # =====================================================
    # STUDENT SUBMISSION SECTION
    # =====================================================

    st.divider()

    st.subheader(
        "📚 CGPA up to 3rd Semester"
    )

    st.write(
        "Your CGPA up to the 3rd semester is submitted "
        "by you and stored as your previous CGPA."
    )

    # -----------------------------------------------------
    # Show existing CGPA
    # -----------------------------------------------------

    if (
        previous_cgpa is not None
        and pd.notna(previous_cgpa)
    ):

        st.success(
            f"Your submitted CGPA up to 3rd semester: "
            f"**{float(previous_cgpa):.2f}**"
        )

        st.caption(
            "Your 3rd-semester CGPA is already recorded."
        )

    else:

        st.warning(
            "Your CGPA up to 3rd semester has not "
            "been submitted yet."
        )

        with st.form(
            "cgpa_submission_form",
            clear_on_submit=True,
        ):

            cgpa = st.number_input(
                "Enter CGPA up to 3rd Semester",
                min_value=0.0,
                max_value=10.0,
                value=0.0,
                step=0.01,
                format="%.2f",
            )

            submitted = st.form_submit_button(
                "Submit CGPA",
                type="primary",
                use_container_width=True,
            )

        if submitted:

            if cgpa <= 0:

                st.error(
                    "Please enter a valid CGPA."
                )

            else:

                submit_third_semester_cgpa(
                    student[
                        "registration_number"
                    ],
                    student[
                        "student_name"
                    ],
                    cgpa,
                )

                st.success(
                    "Your CGPA up to 3rd semester "
                    "has been submitted successfully."
                )

                st.balloons()

                st.rerun()

    # =====================================================
    # 4TH SEMESTER RESULT
    # =====================================================

    st.divider()

    st.subheader(
        "📊 4th Semester Result"
    )

    if (
        fourth_gpa is None
        or pd.isna(fourth_gpa)
    ):

        st.info(
            "Your 4th Semester GPA has not been "
            "updated by the administrator yet."
        )

        st.write(
            "Once the administrator enters your "
            "4th Semester GPA, your CGPA up to "
            "4th semester will be calculated automatically."
        )

    else:

        # =================================================
        # 4TH SEMESTER DETAILS
        # =================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Previous CGPA",
                f"{float(previous_cgpa):.2f}",
            )

        with col2:

            st.metric(
                "4th Semester GPA",
                f"{float(fourth_gpa):.2f}",
            )

        with col3:

            st.metric(
                "CGPA up to 4th",
                f"{float(fourth_cgpa):.2f}",
            )

        st.divider()

        # =================================================
        # CREDIT DETAILS
        # =================================================

        st.write(
            "### Credit Details"
        )

        credit_table = pd.DataFrame(
            [
                {
                    "Particular":
                        "Previous Credits",

                    "Credits":
                        PREVIOUS_CREDITS,
                },
                {
                    "Particular":
                        "4th Semester Credits",

                    "Credits":
                        FOURTH_SEMESTER_CREDITS,
                },
                {
                    "Particular":
                        "Total Credits",

                    "Credits":
                        TOTAL_CREDITS,
                },
            ]
        )

        st.table(
            credit_table
        )

        # =================================================
        # CALCULATION
        # =================================================

        st.divider()

        st.write(
            "### 🧮 How Your CGPA up to 4th Semester Was Calculated"
        )

        st.write(
            "Your previous CGPA is weighted using the "
            "credits completed up to the 3rd semester. "
            "Your 4th Semester GPA is then weighted using "
            "the 4th semester credits."
        )

        # -------------------------------------------------
        # Formula
        # -------------------------------------------------

        st.latex(
            rf"""
            CGPA_{{4th}}
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
            {TOTAL_CREDITS}
            }}
            """
        )

        # -------------------------------------------------
        # Calculate individual contributions
        # -------------------------------------------------

        previous_contribution = (
            float(previous_cgpa)
            * PREVIOUS_CREDITS
        )

        fourth_contribution = (
            float(fourth_gpa)
            * FOURTH_SEMESTER_CREDITS
        )

        total_weighted_points = (
            previous_contribution
            + fourth_contribution
        )

        # -------------------------------------------------
        # Detailed calculation
        # -------------------------------------------------

        st.write(
            f"**Previous CGPA contribution:** "
            f"{float(previous_cgpa):.2f} × "
            f"{PREVIOUS_CREDITS} = "
            f"{previous_contribution:.2f}"
        )

        st.write(
            f"**4th Semester GPA contribution:** "
            f"{float(fourth_gpa):.2f} × "
            f"{FOURTH_SEMESTER_CREDITS} = "
            f"{fourth_contribution:.2f}"
        )

        st.write(
            f"**Total weighted points:** "
            f"{total_weighted_points:.2f}"
        )

        st.write(
            f"**Total credits:** "
            f"{TOTAL_CREDITS}"
        )

        st.latex(
            rf"""
            CGPA_{{4th}}
            =
            \frac{{{total_weighted_points:.2f}}}
            {{{TOTAL_CREDITS}}}
            =
            \mathbf{{{float(fourth_cgpa):.2f}}}
            """
        )

        # =================================================
        # FINAL RESULT
        # =================================================

        st.success(
            f"🎓 Your CGPA up to 4th Semester is "
            f"**{float(fourth_cgpa):.2f}**"
        )

        # =================================================
        # SUMMARY TABLE
        # =================================================

        st.write(
            "### Academic Summary"
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
                        str(TOTAL_CREDITS),
                },
                {
                    "Particular":
                        "CGPA up to 4th Semester",

                    "Value":
                        f"{float(fourth_cgpa):.2f}",
                },
            ]
        )

        st.table(
            summary
        )

    # =====================================================
    # SEARCH ANOTHER STUDENT
    # =====================================================

    st.divider()

    if st.button(
        "Search Another Registration Number",
        use_container_width=True,
    ):

        reset_student_lookup()

        st.rerun()


# =========================================================
# ADMIN PORTAL
# =========================================================

def render_admin_portal() -> None:

    st.header(
        "🔐 Admin Access"
    )

    st.write(
        "Authorized staff can manage 4th Semester GPA "
        "records without changing students' submitted "
        "3rd-semester CGPA."
    )

    # =====================================================
    # ADMIN WARNING
    # =====================================================

    if not st.session_state.get(
        "admin_warning_acknowledged",
        False,
    ):

        st.warning(
            "Are you an authorized admin? "
            "This area contains confidential student "
            "academic records."
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
                "Sign in as Admin",
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
        [4, 1]
    )

    with top_left:

        st.subheader(
            "Student Academic Records"
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
    # SECTION 1:
    # EXISTING 3RD SEMESTER RECORDS
    # =====================================================

    st.divider()

    st.subheader(
        "📚 Existing Student Submissions"
    )

    st.write(
        "These are the CGPA records already submitted "
        "by the students up to the 3rd semester."
    )

    st.info(
        "The 3rd-semester CGPA is locked here. "
        "Admin does not need to re-enter it."
    )

    # =====================================================
    # SEARCH
    # =====================================================

    search = st.text_input(
        "Search by Registration Number or Student Name",
        placeholder="Type registration number or student name",
        key="admin_search",
    ).strip().lower()

    visible = submissions.copy()

    if search:

        visible = visible[
            visible[
                "registration_number"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search,
                na=False,
            )
            |
            visible[
                "student_name"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search,
                na=False,
            )
        ]

    # =====================================================
    # EXISTING RECORD TABLE
    # =====================================================

    display_existing = visible[
        [
            "registration_number",
            "student_name",
            "cgpa_third_semester",
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

            "submitted_at":
                "Student Submitted At",
        }
    )

    st.dataframe(
        display_existing,
        hide_index=True,
        use_container_width=True,
        column_config={
            "CGPA up to 3rd Semester":
                st.column_config.NumberColumn(
                    format="%.2f"
                ),
        },
    )

    # =====================================================
    # SECTION 2:
    # 4TH SEMESTER GPA UPDATE
    # =====================================================

    st.divider()

    st.subheader(
        "📊 4th Semester GPA Update"
    )

    st.write(
        "Enter the 4th Semester GPA for students below. "
        "This is an Excel-like editable table."
    )

    st.info(
        f"Only the **4th Semester GPA** is editable. "
        f"Previous Credits = {PREVIOUS_CREDITS}, "
        f"4th Semester Credits = {FOURTH_SEMESTER_CREDITS}."
    )

    # =====================================================
    # CREATE ADMIN EDIT TABLE
    # =====================================================
    # We use the latest record for each registration number
    # in the editing table, while the underlying old CSV
    # records are not deleted just by loading the page.
    # =====================================================

    admin_table = (
        submissions
        .drop_duplicates(
            subset=["registration_number"],
            keep="last",
        )
        .copy()
    )

    # Sort by registration number
    admin_table = admin_table.sort_values(
        by="registration_number",
        kind="stable",
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # Calculate current CGPA values
    # -----------------------------------------------------

    calculated_values = []

    for _, row in admin_table.iterrows():

        third_cgpa = row[
            "cgpa_third_semester"
        ]

        fourth_gpa = row[
            "fourth_semester_gpa"
        ]

        if (
            pd.notna(third_cgpa)
            and pd.notna(fourth_gpa)
        ):

            calculated = (
                calculate_fourth_semester_cgpa(
                    float(third_cgpa),
                    float(fourth_gpa),
                )
            )

        else:

            calculated = pd.NA

        calculated_values.append(
            calculated
        )

    admin_table[
        "calculated_cgpa_fourth"
    ] = calculated_values

    # -----------------------------------------------------
    # Prepare editable table
    # -----------------------------------------------------

    editor_df = admin_table[
        [
            "registration_number",
            "student_name",
            "cgpa_third_semester",
            "fourth_semester_gpa",
            "calculated_cgpa_fourth",
        ]
    ].copy()

    editor_df = editor_df.rename(
        columns={
            "registration_number":
                "Registration Number",

            "student_name":
                "Student Name",

            "cgpa_third_semester":
                "CGPA up to 3rd Semester",

            "fourth_semester_gpa":
                "4th Semester GPA",

            "calculated_cgpa_fourth":
                "CGPA up to 4th Semester",
        }
    )

    # -----------------------------------------------------
    # Excel-like editor
    # -----------------------------------------------------

    edited_df = st.data_editor(
        editor_df,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        column_config={

            "Registration Number":
                st.column_config.TextColumn(
                    disabled=True,
                ),

            "Student Name":
                st.column_config.TextColumn(
                    disabled=True,
                ),

            "CGPA up to 3rd Semester":
                st.column_config.NumberColumn(
                    disabled=True,
                    format="%.2f",
                ),

            "4th Semester GPA":
                st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=10.0,
                    step=0.01,
                    format="%.2f",
                    help=(
                        "Admin enters the student's "
                        "4th Semester GPA here."
                    ),
                ),

            "CGPA up to 4th Semester":
                st.column_config.NumberColumn(
                    disabled=True,
                    format="%.2f",
                ),
        },
        key="fourth_semester_editor",
    )

    # =====================================================
    # LIVE CALCULATION PREVIEW
    # =====================================================

    st.write(
        "### Calculation Preview"
    )

    preview_table = edited_df.copy()

    preview_cgpas = []

    for _, row in preview_table.iterrows():

        third = row[
            "CGPA up to 3rd Semester"
        ]

        fourth = row[
            "4th Semester GPA"
        ]

        if (
            pd.notna(third)
            and pd.notna(fourth)
        ):

            preview = (
                calculate_fourth_semester_cgpa(
                    float(third),
                    float(fourth),
                )
            )

        else:

            preview = pd.NA

        preview_cgpas.append(
            preview
        )

    preview_table[
        "CGPA up to 4th Semester"
    ] = preview_cgpas

    st.dataframe(
        preview_table[
            [
                "Registration Number",
                "Student Name",
                "CGPA up to 3rd Semester",
                "4th Semester GPA",
                "CGPA up to 4th Semester",
            ]
        ],
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

    # =====================================================
    # SAVE ALL 4TH SEMESTER GPA
    # =====================================================

    if st.button(
        "💾 Save 4th Semester GPA",
        type="primary",
        use_container_width=True,
    ):

        updated_submissions = submissions.copy()

        validation_error = False

        # -------------------------------------------------
        # Process each edited row
        # -------------------------------------------------

        for _, edited_row in edited_df.iterrows():

            registration_number = str(
                edited_row[
                    "Registration Number"
                ]
            ).strip()

            third_cgpa = edited_row[
                "CGPA up to 3rd Semester"
            ]

            fourth_gpa = edited_row[
                "4th Semester GPA"
            ]

            # -------------------------------------------------
            # Skip blank GPA
            # -------------------------------------------------

            if pd.isna(fourth_gpa):

                continue

            # -------------------------------------------------
            # Validate GPA
            # -------------------------------------------------

            try:

                fourth_gpa = float(
                    fourth_gpa
                )

            except (
                ValueError,
                TypeError,
            ):

                st.error(
                    f"Invalid 4th Semester GPA for "
                    f"{registration_number}."
                )

                validation_error = True

                break

            if (
                fourth_gpa < 0
                or fourth_gpa > 10
            ):

                st.error(
                    f"4th Semester GPA for "
                    f"{registration_number} must be "
                    f"between 0 and 10."
                )

                validation_error = True

                break

            if pd.isna(third_cgpa):

                st.error(
                    f"3rd semester CGPA is missing for "
                    f"{registration_number}."
                )

                validation_error = True

                break

            # -------------------------------------------------
            # Calculate new CGPA
            # -------------------------------------------------

            new_cgpa_fourth = (
                calculate_fourth_semester_cgpa(
                    float(third_cgpa),
                    fourth_gpa,
                )
            )

            # -------------------------------------------------
            # Find ALL existing records for this student
            # -------------------------------------------------

            matching_indices = (
                updated_submissions[
                    updated_submissions[
                        "registration_number"
                    ]
                    == registration_number
                ]
                .index
                .tolist()
            )

            if matching_indices:

                # Update the latest record
                latest_index = matching_indices[-1]

                updated_submissions.loc[
                    latest_index,
                    "fourth_semester_gpa"
                ] = round(
                    fourth_gpa,
                    2,
                )

                updated_submissions.loc[
                    latest_index,
                    "cgpa_fourth_semester"
                ] = new_cgpa_fourth

                updated_submissions.loc[
                    latest_index,
                    "submitted_at"
                ] = datetime.now().strftime(
                    "%d %b %Y, %I:%M:%S %p"
                )

            else:

                # This should rarely happen because the table
                # comes from submissions, but it is kept as
                # a safety measure.
                new_row = {
                    "entry_id":
                        str(uuid.uuid4()),

                    "registration_number":
                        registration_number,

                    "student_name":
                        str(
                            edited_row[
                                "Student Name"
                            ]
                        ),

                    "cgpa_third_semester":
                        round(
                            float(third_cgpa),
                            2,
                        ),

                    "submitted_at":
                        datetime.now().strftime(
                            "%d %b %Y, %I:%M:%S %p"
                        ),

                    "fourth_semester_gpa":
                        round(
                            fourth_gpa,
                            2,
                        ),

                    "cgpa_fourth_semester":
                        new_cgpa_fourth,
                }

                updated_submissions = pd.concat(
                    [
                        updated_submissions,
                        pd.DataFrame(
                            [new_row]
                        ),
                    ],
                    ignore_index=True,
                )

        # -------------------------------------------------
        # Save only if no validation error
        # -------------------------------------------------

        if not validation_error:

            save_submissions(
                updated_submissions
            )

            st.success(
                "All 4th Semester GPA entries "
                "have been saved successfully."
            )

            st.rerun()

    # =====================================================
    # SECTION 3:
    # ADMIN SUMMARY TABLE
    # =====================================================

    st.divider()

    st.subheader(
        "📋 Current 4th Semester Records"
    )

    current_submissions = load_submissions()

    current_table = (
        current_submissions
        .drop_duplicates(
            subset=["registration_number"],
            keep="last",
        )
        .copy()
    )

    current_table[
        "cgpa_fourth_semester"
    ] = current_table.apply(
        lambda row:
            calculate_fourth_semester_cgpa(
                float(
                    row["cgpa_third_semester"]
                ),
                float(
                    row["fourth_semester_gpa"]
                ),
            )
            if (
                pd.notna(
                    row["cgpa_third_semester"]
                )
                and pd.notna(
                    row["fourth_semester_gpa"]
                )
            )
            else pd.NA,
        axis=1,
    )

    display_current = current_table[
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
        display_current,
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

    # =====================================================
    # METRICS
    # =====================================================

    st.divider()

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Students",
        len(current_table),
    )

    fourth_gpa_values = current_table[
        "fourth_semester_gpa"
    ].dropna()

    fourth_cgpa_values = current_table[
        "cgpa_fourth_semester"
    ].dropna()

    metric2.metric(
        "4th GPA Updated",
        len(fourth_gpa_values),
    )

    if not fourth_gpa_values.empty:

        metric3.metric(
            "Average 4th GPA",
            f"{fourth_gpa_values.mean():.2f}",
        )

    else:

        metric3.metric(
            "Average 4th GPA",
            "N/A",
        )

    if not fourth_cgpa_values.empty:

        metric4.metric(
            "Average CGPA",
            f"{fourth_cgpa_values.mean():.2f}",
        )

    else:

        metric4.metric(
            "Average CGPA",
            "N/A",
        )

    # =====================================================
    # DELETE RECORD
    # =====================================================

    st.divider()

    st.subheader(
        "🗑️ Delete Student Record"
    )

    st.caption(
        "Deleting a record removes the student's "
        "CGPA record from the active database."
    )

    delete_table = (
        current_submissions
        .drop_duplicates(
            subset=["registration_number"],
            keep="last",
        )
        .copy()
    )

    delete_ids = delete_table[
        "entry_id"
    ].tolist()

    if delete_ids:

        def delete_label(
            entry_id: str,
        ) -> str:

            row = delete_table[
                delete_table["entry_id"]
                == entry_id
            ].iloc[0]

            third = row[
                "cgpa_third_semester"
            ]

            fourth = row[
                "fourth_semester_gpa"
            ]

            if pd.notna(third):

                third_text = (
                    f"{float(third):.2f}"
                )

            else:

                third_text = "N/A"

            if pd.notna(fourth):

                fourth_text = (
                    f"{float(fourth):.2f}"
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
            "Select student to delete",
            options=delete_ids,
            format_func=delete_label,
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

            remaining = current_submissions[
                current_submissions[
                    "entry_id"
                ]
                != selected_delete_id
            ]

            save_submissions(
                remaining
            )

            st.success(
                "Student record deleted successfully."
            )

            st.rerun()

    # =====================================================
    # DOWNLOAD CSV
    # =====================================================

    st.divider()

    st.subheader(
        "📥 Download Records"
    )

    final_csv = current_submissions.to_csv(
        index=False
    ).encode(
        "utf-8"
    )

    st.download_button(
        "Download Complete CGPA Records",
        data=final_csv,
        file_name="cgpa_submissions.csv",
        mime="text/csv",
        use_container_width=True,
    )


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
