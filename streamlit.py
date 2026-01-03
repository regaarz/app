from flask import Flask, render_template_string, request
import firebase_admin
from firebase_admin import credentials, db
import sqlite3
import threading
import time
import os
import math

# ======================
# APP INIT
# ======================
app = Flask(__name__)

# ======================
# PATH DATABASE
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tongsampah.db")

# ======================
# FIREBASE INIT
# ======================
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tongsampah-fb84c-default-rtdb.firebaseio.com/"
})

# ======================
# SQLITE INIT
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS data_tongsampah (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tong_id INTEGER,
            organik INTEGER,
            anorganik INTEGER,
            b3 INTEGER,
            timestamp INTEGER,
            waktu TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ======================
# MAP TONG → ID
# ======================
TONG_MAP = {
    "Tongsampah1": 1,
    "Tongsampah2": 2,
    "Tongsampah3": 3
}

# ======================
# KONVERSI % → INT
# ======================
def persen_ke_int(value):
    try:
        if value is None:
            return 0
        if isinstance(value, str):
            return int(value.replace("%", "").strip())
        return int(value)
    except:
        return 0

# ======================
# SIMPAN KE SQLITE
# ======================
def simpan_ke_db(tong_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    organik = persen_ke_int(data.get("organik"))
    anorganik = persen_ke_int(data.get("anorganik"))
    b3 = persen_ke_int(data.get("b3"))

    c.execute("""
        INSERT INTO data_tongsampah
        (tong_id, organik, anorganik, b3, timestamp, waktu)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        tong_id,
        organik,
        anorganik,
        b3,
        data.get("timestamp"),
        data.get("waktu")
    ))

    conn.commit()
    conn.close()

    print(f"✅ LOG | Tong {tong_id} | O:{organik}% A:{anorganik}% B3:{b3}%")

# ======================
# LOGGER 10 DETIK
# ======================
def logger_10_detik():
    print("🚀 LOGGER AKTIF (10 DETIK)")
    while True:
        for tong, tong_id in TONG_MAP.items():
            data = db.reference(tong).get()
            if data:
                simpan_ke_db(tong_id, data)
        time.sleep(60)

# ======================
# DASHBOARD
# ======================
@app.route("/")
def index():
    per_page = 10
    page = int(request.args.get("page", 1))
    offset = (page - 1) * per_page

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM data_tongsampah")
    total_data = c.fetchone()[0]
    total_pages = max(1, math.ceil(total_data / per_page))

    c.execute("""
        SELECT * FROM data_tongsampah
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    rows = c.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Log Tongsampah</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f1f8f4;
                margin: 0;
                padding: 0;
            }

            .container {
                display: flex;
                justify-content: center;
                margin-top: 40px;
            }

            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                width: 90%;
                max-width: 1100px;
            }

            h2 {
                text-align: center;
                color: #1b5e20;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }

            th {
                background-color: #2e7d32;
                color: white;
                padding: 10px;
            }

            td {
                padding: 8px;
                text-align: center;
                border-bottom: 1px solid #c8e6c9;
            }

            tr:nth-child(even) {
                background-color: #e8f5e9;
            }

            tr:hover {
                background-color: #c8e6c9;
            }

            .pagination {
                text-align: center;
                margin-top: 15px;
            }

            .pagination a {
                padding: 6px 14px;
                margin: 0 5px;
                background-color: #2e7d32;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }

            .pagination a:hover {
                background-color: #1b5e20;
            }
        </style>

        <script>
            setTimeout(() => {
                location.reload();
            }, 5000);
        </script>
    </head>

    <body>
        <div class="container">
            <div class="card">
                <h2>LOG HISTORY TONG SAMPAH</h2>
                <p style="text-align:center;">
                </p>

                <table>
                    <tr>
                        <th>ID</th>
                        <th>Tong</th>
                        <th>Organik (%)</th>
                        <th>Anorganik (%)</th>
                        <th>B3 (%)</th>
                        <th>Timestamp</th>
                        <th>Waktu</th>
                    </tr>
                    {% for r in rows %}
                    <tr>
                        <td>{{ r.id }}</td>
                        <td>{{ r.tong_id }}</td>
                        <td>{{ r.organik }}%</td>
                        <td>{{ r.anorganik }}%</td>
                        <td>{{ r.b3 }}%</td>
                        <td>{{ r.timestamp }}</td>
                        <td>{{ r.waktu }}</td>
                    </tr>
                    {% endfor %}
                </table>

                <div class="pagination">
                    {% if page > 1 %}
                        <a href="/?page={{ page - 1 }}">⬅ Prev</a>
                    {% endif %}

                    Page {{ page }} / {{ total_pages }}

                    {% if page < total_pages %}
                        <a href="/?page={{ page + 1 }}">Next ➡</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html,
        rows=rows,
        page=page,
        total_pages=total_pages
    )

# ======================
# START APP
# ======================
if __name__ == "__main__":
    threading.Thread(target=logger_10_detik, daemon=True).start()
    app.run(debug=False, use_reloader=False)
