# streamlit_app.py
import streamlit as st
import pandas as pd
from models import (
    get_all_faculty, add_faculty, update_faculty, delete_faculty, get_faculty,
    get_all_subjects, add_subject, update_subject, delete_subject, get_subject,
    get_all_schedules, add_schedule, update_schedule, delete_schedule
)
from db_init import init_db
from pathlib import Path
import io

DB_PATH = Path("qwert.db")

st.set_page_config(page_title="Timetable Manager", layout="wide")

# Ensure DB exists
if not DB_PATH.exists():
    init_db(seed=True)

st.title("📚 Timetable Manager (Streamlit)")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Manage Faculty", "Manage Subjects", "Manage Schedule", "Export / Import"])

# Utility display
def df_from_rows(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame([])

### Dashboard ###
if page == "Dashboard":
    st.header("Overview")
    faculty = get_all_faculty()
    subjects = get_all_subjects()
    schedules = get_all_schedules()

    c1, c2, c3 = st.columns(3)
    c1.metric("Faculty", len(faculty))
    c2.metric("Subjects", len(subjects))
    c3.metric("Scheduled classes", len(schedules))

    st.subheader("Upcoming Timetable (by day/time)")
    df_schedules = df_from_rows(schedules)
    if not df_schedules.empty:
        st.dataframe(df_schedules[["id","day_of_week","start_time","end_time","subject_name","faculty_name","room","semester"]].rename(columns={
            "id":"Schedule ID","day_of_week":"Day","start_time":"Start","end_time":"End","subject_name":"Subject","faculty_name":"Faculty"
        }))
    else:
        st.info("No scheduled classes yet. Add schedules from 'Manage Schedule'.")

### Manage Faculty ###
if page == "Manage Faculty":
    st.header("Faculty")
    rows = get_all_faculty()
    df = df_from_rows(rows)
    st.subheader("All Faculty")
    st.dataframe(df)

    st.subheader("Add new faculty")
    with st.form("add_faculty_form", clear_on_submit=True):
        name = st.text_input("Name", "")
        email = st.text_input("Email", "")
        department = st.text_input("Department", "")
        phone = st.text_input("Phone", "")
        submitted = st.form_submit_button("Add Faculty")
    if submitted:
        if not name.strip():
            st.error("Name is required.")
        else:
            fid = add_faculty(name.strip(), email.strip(), department.strip(), phone.strip())
            st.success(f"Added faculty with id {fid}.")
            st.experimental_rerun()

    st.subheader("Edit / Delete faculty")
    col1, col2 = st.columns([2,1])
    with col1:
        fac_list = {f"{r['id']} - {r['name']}": r['id'] for r in rows}
        selected = st.selectbox("Choose faculty", options=list(fac_list.keys()) if fac_list else ["No faculty"], format_func=lambda x:x)
    if rows:
        sel_id = fac_list[selected]
        fac = get_faculty(sel_id)
        with st.form("edit_fac_form"):
            new_name = st.text_input("Name", fac["name"])
            new_email = st.text_input("Email", fac["email"] or "")
            new_dept = st.text_input("Department", fac["department"] or "")
            new_phone = st.text_input("Phone", fac["phone"] or "")
            save = st.form_submit_button("Save changes")
            delete = st.form_submit_button("Delete faculty")
        if save:
            update_faculty(sel_id, new_name, new_email, new_dept, new_phone)
            st.success("Updated faculty.")
            st.experimental_rerun()
        if delete:
            delete_faculty(sel_id)
            st.success("Deleted faculty.")
            st.experimental_rerun()
    else:
        st.info("No faculty records yet.")

### Manage Subjects ###
if page == "Manage Subjects":
    st.header("Subjects")
    rows = get_all_subjects()
    df = df_from_rows(rows)
    st.subheader("All Subjects")
    st.dataframe(df)

    st.subheader("Add new subject")
    with st.form("add_subject_form", clear_on_submit=True):
        name = st.text_input("Subject name", "")
        code = st.text_input("Code", "")
        credits = st.number_input("Credits", min_value=0, max_value=10, value=3, step=1)
        submitted = st.form_submit_button("Add Subject")
    if submitted:
        if not name.strip():
            st.error("Subject name is required.")
        else:
            sid = add_subject(name.strip(), code.strip(), int(credits))
            st.success(f"Added subject with id {sid}.")
            st.experimental_rerun()

    st.subheader("Edit / Delete subject")
    col1, col2 = st.columns([2,1])
    with col1:
        subj_list = {f"{r['id']} - {r['name']}": r['id'] for r in rows}
        selected = st.selectbox("Choose subject", options=list(subj_list.keys()) if subj_list else ["No subjects"])
    if rows:
        sel_id = subj_list[selected]
        subj = get_subject(sel_id)
        with st.form("edit_subj_form"):
            new_name = st.text_input("Name", subj["name"])
            new_code = st.text_input("Code", subj["code"] or "")
            new_credits = st.number_input("Credits", min_value=0, max_value=10, value=int(subj["credits"] or 3))
            save = st.form_submit_button("Save changes")
            delete = st.form_submit_button("Delete subject")
        if save:
            update_subject(sel_id, new_name, new_code, int(new_credits))
            st.success("Updated subject.")
            st.experimental_rerun()
        if delete:
            delete_subject(sel_id)
            st.success("Deleted subject.")
            st.experimental_rerun()
    else:
        st.info("No subjects yet.")

### Manage Schedule ###
if page == "Manage Schedule":
    st.header("Class Schedule")
    schedules = get_all_schedules()
    st.subheader("All scheduled classes")
    df_schedules = df_from_rows(schedules)
    if not df_schedules.empty:
        st.dataframe(df_schedules[["id","day_of_week","start_time","end_time","subject_name","faculty_name","room","semester"]])
    else:
        st.info("No schedules yet.")

    st.subheader("Add schedule")
    subjects = get_all_subjects()
    faculty = get_all_faculty()
    subj_map = {f"{s['id']} - {s['name']}": s['id'] for s in subjects}
    fac_map = {f"{f['id']} - {f['name']}": f['id'] for f in faculty}

    with st.form("add_schedule_form", clear_on_submit=True):
        if subjects and faculty:
            subj_sel = st.selectbox("Subject", options=list(subj_map.keys()))
            fac_sel = st.selectbox("Faculty", options=list(fac_map.keys()))
            day = st.selectbox("Day of week", options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
            start = st.time_input("Start time")
            end = st.time_input("End time")
            room = st.text_input("Room", "")
            sem = st.text_input("Semester", "")
            submitted = st.form_submit_button("Add Schedule")
        else:
            st.warning("You need at least one subject and one faculty to add a schedule.")
            submitted = False

    if submitted:
        sid = subj_map[subj_sel]
        fid = fac_map[fac_sel]
        start_str = start.strftime("%H:%M")
        end_str = end.strftime("%H:%M")
        add_schedule(sid, fid, day, start_str, end_str, room.strip(), sem.strip())
        st.success("Schedule added.")
        st.experimental_rerun()

    st.subheader("Edit / Delete schedule")
    if schedules:
        sched_map = {f"{r['id']} - {r['day_of_week']} {r['start_time']}-{r['end_time']} : {r['subject_name']}": r['id'] for r in schedules}
        sel = st.selectbox("Choose schedule", options=list(sched_map.keys()))
        sel_id = sched_map[sel]
        s = next(r for r in schedules if r["id"] == sel_id)
        with st.form("edit_schedule_form"):
            subj_opt = {f"{s['subject_id']} - {s['subject_name']}": s['subject_id'] for s in subjects}
            subj_choice = st.selectbox("Subject", options=list(subj_map.keys()), index=0)
            fac_choice = st.selectbox("Faculty", options=list(fac_map.keys()), index=0)
            day = st.selectbox("Day of week", options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], index=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(s["day_of_week"]))
            st_start = st.text_input("Start time (HH:MM)", s["start_time"])
            st_end = st.text_input("End time (HH:MM)", s["end_time"])
            room = st.text_input("Room", s.get("room","") or "")
            sem = st.text_input("Semester", s.get("semester","") or "")
            save = st.form_submit_button("Save changes")
            delete = st.form_submit_button("Delete schedule")
        if save:
            sid = subj_map[subj_choice]
            fid = fac_map[fac_choice]
            update_schedule(sel_id, sid, fid, day, st_start, st_end, room.strip(), sem.strip())
            st.success("Schedule updated.")
            st.experimental_rerun()
        if delete:
            delete_schedule(sel_id)
            st.success("Schedule deleted.")
            st.experimental_rerun()
    else:
        st.info("No schedules to edit.")

### Export / Import ###
if page == "Export / Import":
    st.header("Export / Import data")
    st.subheader("Export CSVs")
    faculty = get_all_faculty()
    subjects = get_all_subjects()
    schedules = get_all_schedules()

    def to_csv_bytes(rows):
        df = pd.DataFrame(rows)
        b = io.BytesIO()
        df.to_csv(b, index=False)
        b.seek(0)
        return b

    col1, col2, col3 = st.columns(3)
    with col1:
        if faculty:
            st.download_button("Download faculty.csv", data=to_csv_bytes(faculty), file_name="faculty.csv", mime="text/csv")
        else:
            st.write("No faculty")
    with col2:
        if subjects:
            st.download_button("Download subjects.csv", data=to_csv_bytes(subjects), file_name="subjects.csv", mime="text/csv")
        else:
            st.write("No subjects")
    with col3:
        if schedules:
            st.download_button("Download schedules.csv", data=to_csv_bytes(schedules), file_name="schedules.csv", mime="text/csv")
        else:
            st.write("No schedules")

    st.subheader("Import CSV (simple)")
    st.info("CSV must contain column names matching table fields. Importing will insert rows and may create duplicates.")
    uploaded = st.file_uploader("Upload a CSV (faculty/subjects/schedules)", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.write("Preview:")
        st.dataframe(df.head())
        if st.button("Import rows"):
            # best-effort import: guess table by columns
            cols = set(df.columns.str.lower())
            imported=0
            if {"name","email","department"}.issubset(cols) or "phone" in cols:
                # faculty
                for _, r in df.iterrows():
                    add_faculty(str(r.get("name","")), str(r.get("email","")), str(r.get("department","")), str(r.get("phone","")))
                    imported += 1
            elif {"name","code"}.issubset(cols) or "credits" in cols:
                for _, r in df.iterrows():
                    add_subject(str(r.get("name","")), str(r.get("code","")), int(r.get("credits",3)))
                    imported += 1
            elif {"subject_id","faculty_id","day_of_week"}.issubset(cols) or {"subject_name","faculty_name","day_of_week"}.issubset(cols):
                # For schedules: attempt to map by names -> ids (best effort)
                subj_map = {s["name"]: s["id"] for s in subjects}
                fac_map = {f["name"]: f["id"] for f in faculty}
                for _, r in df.iterrows():
                    sib = r.get("subject_id") or subj_map.get(r.get("subject_name"))
                    fib = r.get("faculty_id") or fac_map.get(r.get("faculty_name"))
                    if pd.isna(sib) or pd.isna(fib):
                        continue
                    add_schedule(int(sib), int(fib), str(r.get("day_of_week")), str(r.get("start_time")), str(r.get("end_time")), str(r.get("room","")), str(r.get("semester","")))
                    imported += 1
            else:
                st.warning("Couldn't auto-detect table type from CSV columns. Make sure headers match fields.")
            st.success(f"Imported ~{imported} rows. Refresh pages to see new data.")
