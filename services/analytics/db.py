import os
import psycopg2
import psycopg2.extras
import pandas as pd



DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fl_user:fl_pass@localhost:5432/focuslens")



DB = dict(
    host="localhost",
    port=5432,
    dbname="focuslens",
    user="fl_user",
    password="fl_pass"
)

# def get_conn():
#     return psycopg2.connect(**DB)

def get_conn():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)





def fetch_session(session_id: str):
    import pandas as pd
    conn = get_conn()
    query = """
        SELECT
            frame_id, ts,
            ear_avg, blink,
            yaw, pitch, roll,
            gaze_zone,
            focused
        FROM focus_events
        WHERE session_id = %s
        ORDER BY ts ASC
    """
    df = pd.read_sql(query, conn, params=(session_id,))
    conn.close()
    return df


def fetch_all_sessions():
    import psycopg2.extras
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            session_id,
            MIN(ts)    AS started_at,
            MAX(ts)    AS ended_at,
            COUNT(*)   AS total_frames
        FROM focus_events
        GROUP BY session_id
        ORDER BY MIN(ts) DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]














# def fetch_session(session_id: str) -> pd.DataFrame:
#     conn = get_conn()
#     query = """
#         SELECT
#             frame_id, ts,
#             ear_avg, blink,
#             yaw, pitch, roll,
#             gaze_zone,
#             focused
#         FROM focus_events
#         WHERE session_id = %s
#         ORDER BY ts ASC
#     """
#     df = pd.read_sql(query, conn, params=(session_id,))
#     conn.close()
#     return df

# def fetch_all_sessions() -> list:
#     conn = get_conn()
#     cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#     cur.execute("""
#         SELECT
#             session_id,
#             MIN(ts)    AS started_at,
#             MAX(ts)    AS ended_at,
#             COUNT(*)   AS total_frames
#         FROM focus_events
#         GROUP BY session_id
#         ORDER BY MIN(ts) DESC
#     """)
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return [dict(r) for r in rows]