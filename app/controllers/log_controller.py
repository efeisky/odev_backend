from app.db.connection import get_connection
from datetime import datetime
from psycopg2 import sql

def log_message(user_code: str, message: str):
    try:
        conn, cur = get_connection()
        if conn is None:
            return

        query = sql.SQL("""
            INSERT INTO logs (message, owner_code, created_at)
            VALUES (%s, %s, %s)
        """)
        cur.execute(query, (message, user_code, datetime.now()))
        conn.commit()

    except Exception as e:
        print("Log kaydı sırasında hata:", e)

    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
