import hashlib
from app.db.connection import get_connection
from app.model.user_model import UserModel
from app.model.project_model import SetMemberModel, SetManagerModel
from psycopg2 import sql

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_email(email: str) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False
    
    try:
        check_query = sql.SQL("SELECT 1 FROM users WHERE email = %s")
        cur.execute(check_query, (email,))
        exists = cur.fetchone()

        if exists:
            return False

    except Exception as e:
        print("SELECT error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
        
def set_user(model: UserModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            INSERT INTO users (code, name, surname, email, password, phone_number, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """)

        cur.execute(query, (
            model.code,
            model.name,
            model.surname,
            model.email,
            model.password,
            model.phone_number,
            False
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Insert error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def check_user(email: str, password: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        check_query = sql.SQL("""
            SELECT code FROM users WHERE email = %s AND password = %s
        """)
        cur.execute(check_query, (email, password))
        result = cur.fetchone()
        if result:
            user_code = result[0]
            return user_code
        else:
            return False

    except Exception as e:
        print("Check error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def set_member(model: SetMemberModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            INSERT INTO members (project_code, user_code, project_role)
            VALUES (%s, %s, %s)
        """)

        cur.execute(query, (
            model.project_code,
            model.user_code,
            model.project_role
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Insert error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def set_manager(model: SetManagerModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        
        update_query = sql.SQL("""
            UPDATE projects
            SET manager_code = %s
            WHERE code = %s
        """)

        cur.execute(update_query, (model.user_code, model.project_code))

        conn.commit()
        return True

    except Exception as e:
        print("UPDATE error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


from psycopg2 import sql

def check_user_main(code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        check_query = sql.SQL("SELECT is_admin, is_active FROM users WHERE code = %s")
        cur.execute(check_query, (code,))
        user = cur.fetchone()
        if not user:
            return False

        is_admin, is_active = user

        if is_active == False:
            return False
        if is_admin:
            return {"exists": True, "role": "admin"}

        manager_query = sql.SQL("SELECT 1 FROM projects WHERE manager_code = %s LIMIT 1")
        cur.execute(manager_query, (code,))
        manager_match = cur.fetchone()

        if manager_match:
            return {"exists": True, "role": "project_manager"}

        return {"exists": True, "role": "member"}

    except Exception as e:
        print("SELECT error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
