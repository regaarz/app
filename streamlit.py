import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
import hashlib
import json
import os

# ===============================
# KONFIGURASI
# ===============================
DATABASE_URL = "https://tongsampah-fb84c-default-rtdb.firebaseio.com/"
BUCKETS = ["Tongsampah1", "Tongsampah2", "Tongsampah3"]
PAGE_SIZE = 10
REFRESH_SEC = 10

# ===============================
# FIREBASE INIT DARI ENV
# ===============================
if not firebase_admin._apps:
    cred_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL
    })

# ===============================
# BACA DATA DARI FIREBASE
# ===============================
def read_current_data():
    rows = []

    for bucket in BUCKETS:
        v = db.reference(bucket).get()
        if not isinstance(v, dict):
            continue

        def to_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        rows.append({
            "tong_id": v.get("tong_id"),
            "organik": to_int(v.get("organik")),
            "anorganik": to_int(v.get("anorganik")),
            "b3": to_int(v.get("b3")),
            "waktu": v.get("waktu"),
            "source": bucket
        })
    return rows

# ===============================
# HASH UNTUK DETEKSI PERUBAHAN
# ===============================
def row_hash(row):
    s = f"{row['tong_id']}-{row['organik']}-{row['anorganik']}-{row['b3']}-{row['waktu']}"
    return hashlib.md5(s.encode()).hexdigest()

# ===============================
# STREAMLIT UI
# ===============================
st.set_page_config(page_title="Monitoring Tong Sampah", layout="wide")
st.title("📊 Monitoring Tong Sampah (Append Row Mode)")

# ===============================
# SESSION STATE INIT
# ===============================
if "table" not in st.session_state:
    st.session_state.table = pd.DataFrame(
        columns=["tong_id", "organik", "anorganik", "b3", "waktu", "source"]
    )

if "last_hashes" not in st.session_state:
    st.session_state.last_hashes = {}

if "page" not in st.session_state:
    st.session_state.page = 0

# ===============================
# BACA DATA BARU
# ===============================
new_rows = read_current_data()

for row in new_rows:
    h = row_hash(row)
    key = row["source"]
    if st.session_state.last_hashes.get(key) != h:
        st.session_state.table = pd.concat(
            [st.session_state.table, pd.DataFrame([row])],
            ignore_index=True
        )
        st.session_state.last_hashes[key] = h

# ===============================
# TAMPILKAN TABEL DENGAN % DAN HEADER CENTER
# ===============================
df = st.session_state.table
total_pages = max((len(df) - 1) // PAGE_SIZE + 1, 1)
start = st.session_state.page * PAGE_SIZE
end = start + PAGE_SIZE

df_display = df.iloc[start:end][["tong_id", "organik", "anorganik", "b3", "waktu"]].copy()

for col in ["organik", "anorganik", "b3"]:
    df_display[col] = df_display[col].astype(str) + "%"

st.markdown(
    """
    <style>
    th {text-align:center !important;}
    td {text-align:center !important;}
    </style>
    """, unsafe_allow_html=True
)

st.table(df_display)

# ===============================
# NAVIGASI PAGINATION
# ===============================
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅ Previous", disabled=st.session_state.page == 0):
        st.session_state.page -= 1
        st.experimental_rerun()

with col3:
    if st.button("Next ➡", disabled=st.session_state.page >= total_pages - 1):
        st.session_state.page += 1
        st.experimental_rerun()

with col2:
    st.markdown(
        f"<p style='text-align:center'>Page {st.session_state.page + 1} of {total_pages}</p>",
        unsafe_allow_html=True
    )

# ===============================
# AUTO REFRESH (tanpa time.sleep)
# ===============================
st.experimental_set_query_params(dummy=st.experimental_get_query_params())
st_autorefresh = st.experimental_rerun
