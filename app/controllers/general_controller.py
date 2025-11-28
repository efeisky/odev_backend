from app.controllers.authentication_controller import hash_password
from app.db.connection import get_connection
from psycopg2 import sql
from app.model.user_model import UpdateUserModel

def get_user_logs(user_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = """
            SELECT 
                l.id,
                l.message,
                u.name || ' ' || u.surname AS owner_name,
                l.created_at
            FROM logs l
            LEFT JOIN users u ON l.owner_code = u.code
            WHERE l.owner_code = %s
            ORDER BY l.created_at DESC
            LIMIT 100;
        """

        cur.execute(query, (user_code,))
        users = cur.fetchall()

        result = [
            {
                "id": row[0],
                "message": row[1],
                "owner_name": row[2],
                "created_at": row[3]
            }
            for row in users
        ]
        return result

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def get_all_users_for_project():
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            SELECT name || ' ' || surname AS full_name, code
            FROM public.users
        """)

        cur.execute(query, ())
        users = cur.fetchall()

        result = [{"full_name": row[0], "code": row[1]} for row in users]
        return result

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def get_all_users_for_admin():
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY name, surname) AS id,
                name,
                surname,
                email,
                phone_number,
                code,
                is_active
            FROM public.users;
        """)

        cur.execute(query, ())
        users = cur.fetchall()
        result = [
            {
                "id": row[0],
                "name": row[1],
                "surname": row[2],
                "email": row[3],
                "phone": row[4],
                "code": row[5],
                "active": row[6],
            }
            for row in users
        ]
        return result

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def delete_user(code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            DELETE FROM users
            WHERE code = %s
        """)

        cur.execute(query, (code,))
        conn.commit()

        return True

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def edit_activation_user(code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            UPDATE users
            SET is_active = NOT is_active
            WHERE code = %s
        """)

        cur.execute(query, (code,))
        conn.commit()

        return True

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def update_user(data: UpdateUserModel):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        fields = [
            sql.SQL("name = %s"),
            sql.SQL("surname = %s"),
            sql.SQL("email = %s"),
        ]
        values = [data.name, data.surname, data.email]

        if getattr(data, "password", None) is not None:
            fields.append(sql.SQL("password = %s"))
            values.append(hash_password(password=data.password));

        if getattr(data, "phone_number", None) is not None:
            fields.append(sql.SQL("phone_number = %s"))
            values.append(data.phone_number)

        if not fields:
            return False

        query = sql.SQL("UPDATE users SET ") + sql.SQL(", ").join(fields) + sql.SQL(" WHERE code = %s")
        values.append(data.code)

        cur.execute(query, values)
        conn.commit()

        return cur.rowcount > 0

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print("Query error:", e)
        return False

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

def get_dashboard(user_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        # Kullanıcı adı
        cur.execute("""
            SELECT name || ' ' || surname AS full_name
            FROM users
            WHERE code = %s
        """, (user_code,))
        user_row = cur.fetchone()
        full_name = user_row[0] if user_row else "Bilinmeyen Kullanıcı"

        # Son 5 log
        cur.execute("""
            SELECT message
            FROM logs
            WHERE owner_code = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (user_code,))
        logs_rows = cur.fetchall()
        logs = [row[0] for row in logs_rows]

        # Görev sayıları
        cur.execute("""
            WITH user_tasks AS (
                SELECT DISTINCT
                    t.id,
                    t.start_date,
                    t.end_date
                FROM tasks t
                LEFT JOIN tasks_assignment ta ON t.id = ta.task_id
                WHERE t.created_by = %s
                   OR ta.user_code = %s
            )
            SELECT
                'all_count' AS kategori,
                COUNT(*) AS sayi
            FROM user_tasks

            UNION ALL

            SELECT
                'finished_count' AS kategori,
                COUNT(*) AS sayi
            FROM user_tasks
            WHERE end_date < CURRENT_DATE

            UNION ALL

            SELECT
                'nearly_count' AS kategori,
                COUNT(*) AS sayi
            FROM user_tasks
            WHERE start_date > CURRENT_DATE
              AND start_date <= CURRENT_DATE + INTERVAL '7 days'

            UNION ALL

            SELECT
                'ongoing_count' AS kategori,
                COUNT(*) AS sayi
            FROM user_tasks
            WHERE start_date <= CURRENT_DATE
              AND end_date >= CURRENT_DATE;
        """, (user_code, user_code))
        tasks_rows = cur.fetchall()
        tasks_counts = {row[0]: row[1] for row in tasks_rows}

        # Tarihe göre görev listesi
        cur.execute("""
            WITH user_tasks AS (
                SELECT DISTINCT
                    t.id,
                    t.title,
                    t.start_date,
                    t.end_date
                FROM tasks t
                LEFT JOIN tasks_assignment ta ON t.id = ta.task_id
                WHERE t.created_by = %s
                   OR ta.user_code = %s
            ),
            events AS (
                SELECT DISTINCT start_date AS event_date, title || ' görevinin başlangıç tarihi' AS description
                FROM user_tasks
                WHERE start_date IS NOT NULL
                UNION ALL
                SELECT DISTINCT end_date AS event_date, title || ' görevinin bitiş tarihi' AS description
                FROM user_tasks
                WHERE end_date IS NOT NULL
            )
            SELECT
                event_date,
                ARRAY_AGG(description ORDER BY description) AS tasks
            FROM events
            GROUP BY event_date
            ORDER BY event_date;
        """, (user_code, user_code))
        tasks_by_date_rows = cur.fetchall()

        # Tarihe göre dict oluştur
        from collections import OrderedDict
        tasks_by_date = OrderedDict()
        for row in tasks_by_date_rows:
            date_str = row[0].strftime("%Y-%m-%d")
            tasks_by_date[date_str] = row[1]

        # Dashboard verisi
        dashboard_data = {
            "full_name": full_name,
            "logs": logs,
            "tasks_counts": tasks_counts,
            "tasks_by_date": tasks_by_date
        }

        return dashboard_data

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()