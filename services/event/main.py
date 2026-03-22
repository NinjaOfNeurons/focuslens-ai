from kafka import KafkaConsumer
import psycopg2
import json
import datetime

DB = dict(host="localhost", port=5432,
          dbname="focuslens", user="fl_user", password="fl_pass")

def get_conn():
    return psycopg2.connect(**DB)

def insert_event(cur, data):
    ts = datetime.datetime.fromtimestamp(data["ts"] / 1000,
                                         tz=datetime.timezone.utc)
    cur.execute("""
        INSERT INTO focus_events (
            session_id, frame_id, ts,
            ear_left, ear_right, ear_avg, blink,
            yaw, pitch, roll,
            gaze_zone, iris_left_x, iris_left_y,
            focused, focus_score
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s
        )
    """, (
        data["session_id"],
        data["frame_id"],
        ts,
        data["eye"]["ear_left"],
        data["eye"]["ear_right"],
        data["eye"]["ear_avg"],
        data["eye"]["blink_detected"],
        data["head_pose"]["yaw"],
        data["head_pose"]["pitch"],
        data["head_pose"]["roll"],
        data["gaze"]["gaze_zone"],
        data["gaze"]["iris_left_x"],
        data["gaze"]["iris_left_y"],
        data["focus"]["rule_based"],
        data["focus"]["score"],
    ))

def run():
    conn = get_conn()
    cur  = conn.cursor()
    print("[event] Connecting to Redpanda...")

    consumer = KafkaConsumer(
        "focus-raw",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="event-service"
    )

    print("[event] Listening for focus events...")
    for msg in consumer:
        data = msg.value
        try:
            insert_event(cur, data)
            conn.commit()
            print(f"[event] Saved frame {data['frame_id']} "
                  f"session {data['session_id'][:8]} "
                  f"focused={data['focus']['rule_based']}")
        except Exception as e:
            conn.rollback()
            print(f"[event] Error: {e}")

if __name__ == "__main__":
    run()