from app.model.project_model import EditProjectModel, SetProjectModel, ChangeRoleModel, UnAuthorizeUserModel
from app.db.connection import get_connection
from psycopg2 import sql

def set_project(model: SetProjectModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        insert_project_query = sql.SQL("""
            INSERT INTO projects (code, date_start, date_end, manager_code, definition, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """)
        cur.execute(
            insert_project_query,
            (
                model.project_code,
                model.date_start,
                model.date_end,
                model.manager_code,
                model.definition,
                model.status
            )
        )

        if model.extra_users:
            insert_member_query = sql.SQL("""
                INSERT INTO members (project_code, user_code, project_role)
                VALUES (%s, %s, %s)
            """)
            for member in model.extra_users:
                cur.execute(
                    insert_member_query,
                    (
                        model.project_code,
                        member.code,
                        member.role or "viewer"
                    )
                )

        if model.types:
            insert_type_query = sql.SQL("""
                INSERT INTO task_type (project_code, definition)
                VALUES (%s, %s)
            """)
            for t in model.types:
                cur.execute(insert_type_query, (model.project_code, t.name))

        if model.priorities:
            insert_priority_query = sql.SQL("""
                INSERT INTO task_priorities (project_code, definition)
                VALUES (%s, %s)
            """)
            for p in model.priorities:
                cur.execute(insert_priority_query, (model.project_code, p.name))

        if model.statuses:
            insert_status_query = sql.SQL("""
                INSERT INTO task_status (project_code, definition)
                VALUES (%s, %s)
            """)
            for s in model.statuses:
                cur.execute(insert_status_query, (model.project_code, s.name))

        conn.commit()
        return True

    except Exception as e:
        print("Insert error:", e)
        conn.rollback()
        return False

    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

def change_role(model: ChangeRoleModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            UPDATE members
            SET project_role = %s
            WHERE user_code = %s AND project_code = %s
        """)

        cur.execute(query, (
            model.project_role,
            model.user_code,
            model.project_code
        ))

        conn.commit()
        return True

    except Exception as e:
        print("UPDATE error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


def unauthorize_user(model: UnAuthorizeUserModel) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            DELETE FROM members
            WHERE user_code = %s AND project_code = %s
        """)

        cur.execute(query, (
            model.user_code,
            model.project_code
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Delete error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


def delete_project(project_code: str) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            DELETE FROM projects
            WHERE code = %s
        """)

        cur.execute(query, (project_code,))

        conn.commit()
        return True

    except Exception as e:
        print("Delete error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


def get_members(project_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            SELECT 
                u."name" || ' ' || u."surname" AS full_name,
                CASE 
                    WHEN u.code = (
                        SELECT p.manager_code
                        FROM PROJECTS p
                        WHERE p.code = %s
                    ) THEN 'manager'
                    ELSE m.project_role
                END AS role
            FROM USERS u
            LEFT JOIN MEMBERS m 
                ON u.code = m.user_code 
                AND m.project_code = %s
            WHERE u.code = (
                SELECT p.manager_code
                FROM PROJECTS p
                WHERE p.code = %s
            )
            OR u.code IN (
                SELECT m.user_code
                FROM MEMBERS m
                WHERE m.project_code = %s
            );
        """)

        cur.execute(query, (project_code, project_code, project_code, project_code))
        members = cur.fetchall()

        result = [{"full_name": row[0], "role": row[1]} for row in members]
        return result

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()


def change_status(project_code: str, new_status: str) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            UPDATE projects
            SET status = %s
            WHERE code = %s
        """)

        cur.execute(query, (
            new_status,
            project_code
        ))

        conn.commit()
        return True

    except Exception as e:
        print("UPDATE error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


def get_projects(user_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            SELECT DISTINCT 
                p.code,
                p.date_start,
                p.date_end,
                p.definition,
                p.status,
                u.name || ' ' || u.surname AS manager_name
            FROM public.projects p
            LEFT JOIN public.members m 
                ON m.project_code = p.code
            LEFT JOIN public.users u 
                ON u.code = p.manager_code
            WHERE p.manager_code = %s
            OR m.user_code = %s;
        """)
        
        cur.execute(query, (user_code, user_code))
        rows = cur.fetchall()

        result = [
            {
                "code": row[0],
                "date_start": row[1],
                "date_end": row[2],
                "definition": row[3],
                "status": row[4],
                "manager_name": row[5],
            }
            for row in rows
        ]

        return result

    except Exception as e:
        print("Query error:", e)
        return False

    finally:
        cur.close()
        conn.close()

def get_project_detail(project_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        cur.execute("""
            SELECT 
                p.definition AS name,
                p.date_start,
                p.date_end,
                p.status,
                CONCAT(u.name, ' ', u.surname) AS manager_name,
                COUNT(m.id)+1 AS member_count,
                COUNT(t.id) AS task_count
            FROM public.projects p
            LEFT JOIN public.users u ON u.code = p.manager_code
            LEFT JOIN public.members m ON m.project_code = p.code
            LEFT JOIN public.tasks t ON t.project_code = p.code
            WHERE p.code = %s
            GROUP BY 
                p.code, 
                p.definition, 
                p.date_start, 
                p.date_end, 
                p.status, 
                u.name, 
                u.surname
        """, (project_code,))
        row = cur.fetchone()
        project_detail = {
            "name": row[0],
            "date_start": row[1],
            "date_end": row[2],
            "status": row[3],
            "manager_name": row[4],
            "member_count": row[5],
            "task_count": row[6]
        } if row else {}

        cur.execute("""
            SELECT name, role
            FROM (
                SELECT
                    pm.name || ' ' || pm.surname AS name,
                    'manager' AS role,
                    0 AS sort_order
                FROM public.projects p
                LEFT JOIN public.users pm ON p.manager_code = pm.code
                WHERE p.code = %s
                UNION ALL
                SELECT
                    u.name || ' ' || u.surname AS name,
                    m.project_role AS role,
                    1 AS sort_order
                FROM public.members m
                LEFT JOIN public.users u ON m.user_code = u.code
                WHERE m.project_code = %s
            ) t
            ORDER BY sort_order, name
        """, (project_code, project_code))
        project_members = [{"name": r[0], "role": r[1]} for r in cur.fetchall()]

        cur.execute("""
            SELECT
                (SELECT array_agg(definition) 
                 FROM task_priorities 
                 WHERE project_code=%s) AS priorities,
                 
                (SELECT array_agg(definition) 
                 FROM task_status 
                 WHERE project_code=%s) AS statuses,
                 
                (SELECT array_agg(definition) 
                 FROM task_type 
                 WHERE project_code=%s) AS types
        """, (project_code, project_code, project_code))
        row = cur.fetchone()
        project_meta = {
            "priorities": row[0] or [],
            "statuses": row[1] or [],
            "types": row[2] or []
        } if row else {"priorities": [], "statuses": [], "types": []}

        return {
            "project_detail": project_detail,
            "project_members": project_members,
            "project_meta": project_meta
        }
        
    except Exception as e:
        print("Error:", e)
        return False

    finally:
        if conn:
            conn.close()


def get_project_constants(project_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        cur.execute("""
            SELECT
                (SELECT array_agg(definition) 
                 FROM task_priorities 
                 WHERE project_code=%s) AS priorities,
                 
                (SELECT array_agg(definition) 
                 FROM task_status 
                 WHERE project_code=%s) AS statuses,
                 
                (SELECT array_agg(definition) 
                 FROM task_type 
                 WHERE project_code=%s) AS types
        """, (project_code, project_code, project_code))
        row = cur.fetchone()
        project_meta = {
            "priorities": row[0] or [],
            "statuses": row[1] or [],
            "types": row[2] or []
        } if row else {"priorities": [], "statuses": [], "types": []}

        return project_meta;
        
    except Exception as e:
        print("Error:", e)
        return False

    finally:
        if conn:
            conn.close()


def get_project_users(project_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        cur.execute("""
            SELECT u.code AS id, u.name || ' ' || u.surname AS name
            FROM public.projects p
            LEFT JOIN public.users u ON u.code = p.manager_code
            WHERE p.code = %s
            UNION
            SELECT u.code AS id, u.name || ' ' || u.surname AS name
            FROM public.members m
            LEFT JOIN public.users u ON u.code = m.user_code
            WHERE m.project_code = %s
            ORDER BY name
        """, (project_code, project_code))

        rows = cur.fetchall()
        users_list = [{"id": row[0], "name": row[1]} for row in rows]

        return users_list

    except Exception as e:
        print("Error:", e)
        return False

    finally:
        if conn:
            conn.close()

def edit_project(model: EditProjectModel):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        # Transaction başlat
        conn.autocommit = False

        cur.execute("""
            UPDATE projects
            SET
                date_start = %s,
                date_end = %s,
                manager_code = %s,
                definition = %s
            WHERE code = %s
        """, (
            model.startDate,
            model.endDate,
            model.managerId,
            model.definition,
            model.project_code
        ))

        cur.execute("""
            SELECT user_code, project_role 
            FROM members
            WHERE project_code = %s
        """, (model.project_code,))
        
        rows = cur.fetchall()
        old_users = {r[0]: r[1] for r in rows}

        new_users_dict = {u["code"]: u["role"] for u in model.extra_users}

        to_insert = set(new_users_dict.keys()) - set(old_users.keys())

        for code in to_insert:
            cur.execute("""
                INSERT INTO members (project_code, user_code, project_role)
                VALUES (%s, %s, %s)
            """, (model.project_code, code, new_users_dict[code]))

        to_delete = set(old_users.keys()) - set(new_users_dict.keys())

        for code in to_delete:
            cur.execute("""
                DELETE FROM members
                WHERE project_code = %s AND user_code = %s
            """, (model.project_code, code))

        to_update = [
            code for code in new_users_dict
            if code in old_users and new_users_dict[code] != old_users[code]
        ]

        for code in to_update:
            cur.execute("""
                UPDATE members
                SET project_role = %s
                WHERE project_code = %s AND user_code = %s
            """, (new_users_dict[code], model.project_code, code))

        cur.execute("""
            SELECT definition
            FROM task_status
            WHERE project_code = %s
        """, (model.project_code,))
        
        rows = cur.fetchall()
        old_statuses = set(r[0] for r in rows)

        new_statuses = set(s["name"] for s in model.statuses)

        to_insert = new_statuses - old_statuses
        for definition in to_insert:
            cur.execute("""
                INSERT INTO task_status (project_code, definition)
                VALUES (%s, %s)
            """, (model.project_code, definition))

        to_delete = old_statuses - new_statuses
        for definition in to_delete:
            cur.execute("""
                DELETE FROM task_status
                WHERE project_code = %s AND definition = %s
            """, (model.project_code, definition))


        cur.execute("""
            SELECT definition
            FROM task_type
            WHERE project_code = %s
        """, (model.project_code,))
        
        rows = cur.fetchall()
        old_types = set(r[0] for r in rows)

        new_types = set(s["name"] for s in model.types)

        to_insert = new_types - old_types
        for definition in to_insert:
            cur.execute("""
                INSERT INTO task_type (project_code, definition)
                VALUES (%s, %s)
            """, (model.project_code, definition))

        to_delete = old_types - new_types
        for definition in to_delete:
            cur.execute("""
                DELETE FROM task_type
                WHERE project_code = %s AND definition = %s
            """, (model.project_code, definition))

        cur.execute("""
            SELECT definition
            FROM task_priorities
            WHERE project_code = %s
        """, (model.project_code,))
        
        rows = cur.fetchall()
        old_priorities = set(r[0] for r in rows)

        new_priorities = set(s["name"] for s in model.priorities)

        to_insert = new_priorities - old_priorities
        for definition in to_insert:
            cur.execute("""
                INSERT INTO task_priorities (project_code, definition)
                VALUES (%s, %s)
            """, (model.project_code, definition))

        to_delete = old_priorities - new_priorities
        for definition in to_delete:
            cur.execute("""
                DELETE FROM task_priorities
                WHERE project_code = %s AND definition = %s
            """, (model.project_code, definition))
        # Commit
        conn.commit()
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        print("Query error:", e)
        return False

    finally:
        if cur: cur.close()
        if conn: conn.close()
    