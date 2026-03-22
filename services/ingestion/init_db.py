import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="focuslens",
    user="fl_user",
    password="fl_pass"
)
cur = conn.cursor()

# enable timescaledb
cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

# main events table
cur.execute("""
    CREATE TABLE IF NOT EXISTS focus_events (
        id          BIGSERIAL,
        session_id  TEXT        NOT NULL,
        frame_id    INTEGER     NOT NULL,
        ts          TIMESTAMPTZ NOT NULL,

        -- eye
        ear_left    FLOAT,
        ear_right   FLOAT,
        ear_avg     FLOAT,
        blink       BOOLEAN,

        -- head pose
        yaw         FLOAT,
        pitch       FLOAT,
        roll        FLOAT,

        -- gaze
        gaze_zone   TEXT,
        iris_left_x FLOAT,
        iris_left_y FLOAT,

        -- focus
        focused     BOOLEAN,
        focus_score FLOAT,

        PRIMARY KEY (id, ts)
    );
""")

# convert to timescaledb hypertable (partitions by time automatically)
cur.execute("""
    SELECT create_hypertable('focus_events', 'ts',
        if_not_exists => TRUE);
""")

# sessions table
cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id   TEXT PRIMARY KEY,
        started_at   TIMESTAMPTZ NOT NULL,
        ended_at     TIMESTAMPTZ,
        focus_score  FLOAT,
        total_frames INTEGER DEFAULT 0
    );
""")

conn.commit()
cur.close()
conn.close()
print("[db] Tables created successfully")