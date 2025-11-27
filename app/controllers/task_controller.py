from datetime import datetime
from app.model.task_model import EditTaskFullModel, SetTaskModel, SetTaskDetailModel
from app.db.connection import get_connection
from psycopg2 import sql

def get_projects_for_task(user_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = sql.SQL("""
            SELECT DISTINCT 
                p.code,
                p.definition
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
                "definition": row[1]
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

def set_task(data: dict) -> bool:
    conn, cur = get_connection()
    if conn is None:
        print("Connection error.")
        return False

    try:
        cur.execute("""
            SELECT id FROM task_status 
            WHERE project_code = %s AND definition = %s
        """, (data["project_code"], data["status_definition"]))
        row = cur.fetchone()
        if not row:
            raise ValueError("Status not found for given project/definition.")
        status_id = row[0]

        cur.execute("""
            SELECT id FROM task_priorities 
            WHERE project_code = %s AND definition = %s
        """, (data["project_code"], data["priority_definition"]))
        row = cur.fetchone()
        if not row:
            raise ValueError("Priority not found for given project/definition.")
        priority_id = row[0]

        cur.execute("""
            SELECT id FROM task_type 
            WHERE project_code = %s AND definition = %s
        """, (data["project_code"], data["type_definition"]))
        row = cur.fetchone()
        if not row:
            raise ValueError("Type not found for given project/definition.")
        type_id = row[0]

        model = SetTaskModel(
            p_code=data["project_code"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            last_status=status_id,
            type=type_id,
            created_by=data["created_by"],
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            priority=priority_id
        )

        cur.execute("""
            INSERT INTO tasks (
                project_code, title, description, last_status, type,
                created_time, created_by, start_date, end_date, priority
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            model.p_code,
            model.title,
            model.description,
            model.last_status,
            model.type,
            model.created_time,
            model.created_by,
            model.start_date,
            model.end_date,
            model.priority
        ))

        task_id = cur.fetchone()[0]

        for user in data.get("users", []):
            cur.execute("""
                INSERT INTO tasks_assignment (
                    task_id, user_code, assigned_at, assigned_by
                )
                VALUES (%s, %s, %s, %s)
            """, (
                task_id,
                user["id"],
                datetime.now(),
                data["created_by"]
            ))

        for subtask in data.get("subtasks", []):
            cur.execute("""
                INSERT INTO task_detail (
                    task_id, description, created_by, created_time
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                task_id,
                subtask["title"],
                data["created_by"],
                datetime.now()
            ))

            detail_task_id = cur.fetchone()[0]

            for user_code in subtask.get("assignedUserIds", []):
                cur.execute("""
                    INSERT INTO task_detail_assignment (
                        detail_task_id, assigned_user, timestamp
                    )
                    VALUES (%s, %s, %s)
                """, (
                    detail_task_id,
                    user_code,
                    datetime.now()
                ))
        
        
        for file in data.get("attachments", []):
            cur.execute("""
                INSERT INTO attachments (
                    task_id, file, uploaded_at, owner_code, file_name
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                task_id,
                bytes(file["data"]),
                datetime.now(),
                data["created_by"],
                file["name"]
            ))

        conn.commit()
        return True

    except Exception as e:
        print("Transaction error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def set_task_detail(data: dict) -> bool:
    conn, cur = get_connection()
    if conn is None:
        print("Connection error.")
        return False

    try:
        cur.execute("""
            INSERT INTO task_status (project_code, definition)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (data["project_code"], data["status_definition"]))
        status_id = cur.fetchone()[0]

        model = SetTaskDetailModel(
            created_by=data["created_by"],
            description=data["description"],
            status=status_id,
            task_id=data["task_id"],
        )
        cur.execute("""
            INSERT INTO task_detail (
                task_id, description, status, created_by, created_time
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            model.task_id,
            model.description,
            model.status,
            model.created_by,
            model.created_time,
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Transaction error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()
        
def set_task_attachment(data: dict) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        
        for file in data.get("attachments", []):
            cur.execute("""
                INSERT INTO attachments (
                    task_id, file, uploaded_at, owner_code, file_name
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data["task_id"],
                bytes(file["data"]),
                datetime.now(),
                data["user_id"],
                file["name"]
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

def get_tasks(user_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = """
            SELECT 
                t.id AS task_id,
                t.project_code,
                t.title,
                t.description,
                t.created_time,
                u_created.name || ' ' || u_created.surname AS created_by_name,
                t.start_date,
                t.end_date,
                ts.id AS status_id,
                ts.definition AS status_definition,
                tp.id AS priority_id,
                tp.definition AS priority_definition,
                tt.id AS type_id,
                tt.definition AS type_definition,
                ARRAY_AGG(u_assigned.name || ' ' || u_assigned.surname) 
                    FILTER (WHERE u_assigned.code IS NOT NULL) AS assigned_users
            FROM tasks t
            LEFT JOIN users u_created ON t.created_by = u_created.code
            LEFT JOIN task_status ts ON t.last_status = ts.id
            LEFT JOIN task_priorities tp ON t.priority = tp.id
            LEFT JOIN task_type tt ON t.type = tt.id
            LEFT JOIN tasks_assignment ta ON t.id = ta.task_id
            LEFT JOIN users u_assigned ON ta.user_code = u_assigned.code
            WHERE t.project_code IN (
                SELECT project_code
                FROM members
                WHERE user_code = %s
            )
            OR (t.created_by = %s OR ta.user_code = %s)
            GROUP BY 
                t.id, t.project_code, t.title, t.description, t.created_time, u_created.name, u_created.surname,
                t.start_date, t.end_date,
                ts.id, ts.definition,
                tp.id, tp.definition,
                tt.id, tt.definition
            ORDER BY t.created_time DESC;
        """

        cur.execute(query, (user_code, user_code, user_code))
        tasks_rows = cur.fetchall()

        tasks_result = []
        for row in tasks_rows:
            assigned_users = list(row[14]) if isinstance(row[14], list) else []
            task_id = row[0]

            # 🧩 Subtasks
            cur.execute("""
                SELECT 
                    td.id,
                    td.task_id,
                    td.description,
                    u_created.name || ' ' || u_created.surname AS created_by,
                    td.created_time,
                    ARRAY_AGG(u_assigned.name || ' ' || u_assigned.surname) 
                        FILTER (WHERE u_assigned.code IS NOT NULL) AS assigned_users
                FROM task_detail td
                LEFT JOIN users u_created ON td.created_by = u_created.code
                LEFT JOIN task_detail_assignment tda ON td.id = tda.detail_task_id
                LEFT JOIN users u_assigned ON tda.assigned_user = u_assigned.code
                WHERE td.task_id = %s
                GROUP BY td.id, td.task_id, td.description, u_created.name, u_created.surname, td.created_time
                ORDER BY td.created_time ASC;
            """, (task_id,))
            details_rows = cur.fetchall()

            sub_tasks = [
                {
                    "id": drow[0],
                    "task_id": drow[1],
                    "description": drow[2],
                    "created_by": drow[3],
                    "created_time": drow[4],
                    "assigned_users": drow[5]
                }
                for drow in details_rows
            ]

            cur.execute("""
                SELECT 
                    id,
                    file_name,
                    encode(file, 'base64') AS file_data
                FROM attachments
                WHERE task_id = %s
            """, (task_id,))
            attachments_rows = cur.fetchall()

            attachments = [
                {"id": a[0], "name": a[1], "data": a[2]}
                for a in attachments_rows
            ]

            tasks_result.append({
                "task_id": row[0],
                "project_code": row[1],
                "title": row[2],
                "description": row[3],
                "created_time": row[4],
                "created_by": row[5],
                "start_date": row[6],
                "end_date": row[7],
                "status_id": row[8],
                "status_definition": row[9],
                "priority_id": row[10],
                "priority_definition": row[11],
                "type_id": row[12],
                "type_definition": row[13],
                "assigned_users": assigned_users,
                "sub_tasks": sub_tasks,
                "attachments": attachments
            })

        return tasks_result

    except Exception as e:
        print("Query error:", e)
        return {"status": False, "error": str(e)}

    finally:
        cur.close()
        conn.close()

def set_main_task_status(task_id: int, new_status: str) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = """
            UPDATE task_status ts
            SET 
                category_id = %s,
                definition = CASE
                    WHEN %s = 'continue' THEN 'continue'
                    WHEN %s = 'finished' THEN 'finished'
                    ELSE definition
                END
            WHERE ts.id = (
                SELECT last_status
                FROM tasks
                WHERE id = %s
            )
        """

        cur.execute(query, (new_status, new_status, new_status, task_id))
        conn.commit()

        return True

    except Exception as e:
        print("UPDATE error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def set_sub_task_status(task_id: int, sub_id: int, new_status: str) -> bool:
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = """
            UPDATE task_status ts
            SET 
                category_id = %s,
                definition = CASE
                    WHEN %s = 'continue' THEN 'continue'
                    WHEN %s = 'finished' THEN 'finished'
                    ELSE definition
                END
            WHERE ts.id = (
                SELECT td.status
                FROM task_detail td
                WHERE td.task_id = %s AND td.id = %s
            )
        """

        cur.execute(query, (new_status, new_status, new_status, task_id, sub_id))
        conn.commit()
        
        return True

    except Exception as e:
        print("UPDATE error:", e)
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()

def get_project_tasks(user_code: str, project_code: str):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        query = """
            SELECT 
                t.id AS task_id,
                t.project_code,
                t.title,
                t.description,
                t.created_time,
                u_created.name || ' ' || u_created.surname AS created_by_name,
                t.start_date,
                t.end_date,
                ts.id AS status_id,
                ts.definition AS status_definition,
                ts.category_id AS status_category,
                tp.id AS priority_id,
                tp.definition AS priority_definition,
                tt.id AS type_id,
                tt.definition AS type_definition,
                ARRAY_AGG(u_assigned.name || ' ' || u_assigned.surname) FILTER (WHERE u_assigned.code IS NOT NULL) AS assigned_users
            FROM tasks t
            LEFT JOIN users u_created ON t.created_by = u_created.code
            LEFT JOIN task_status ts ON t.last_status = ts.id
            LEFT JOIN task_priorities tp ON t.priority = tp.id
            LEFT JOIN task_type tt ON t.type = tt.id
            LEFT JOIN tasks_assignment ta ON t.id = ta.task_id
            LEFT JOIN users u_assigned ON ta.user_code = u_assigned.code
            WHERE t.project_code IN (
                -- Kullanıcının üye olduğu projelerden gelmeli
                SELECT project_code
                FROM members
                WHERE user_code = %s
            )
            -- Sadece dışarıdan gelen proje koduna ait görevleri filtrele
            AND t.project_code = %s 
            -- Ek olarak, görev ya kullanıcı tarafından oluşturulmuş olmalı ya da kullanıcıya atanmış olmalı (mevcut mantığınızı koruyarak)
            AND (t.created_by = %s OR ta.user_code = %s) 
            GROUP BY 
                t.id, t.project_code, t.title, t.description, t.created_time, u_created.name, u_created.surname,
                t.start_date, t.end_date,
                ts.id, ts.definition, ts.category_id,
                tp.id, tp.definition,
                tt.id, tt.definition
            ORDER BY t.created_time DESC;
        """

        cur.execute(query, (user_code, project_code, user_code, user_code))
        tasks_rows = cur.fetchall()

        tasks_result = []
        for row in tasks_rows:
            assigned_users = row[15] or []
            if isinstance(assigned_users, str):
                assigned_users = [name.strip().strip('"') for name in assigned_users.strip("{}").split(",") if name.strip()]

            task_id = row[0]

            cur.execute("""
                SELECT 
                    td.id,
                    td.task_id,
                    td.description,
                    ts.category_id AS status_category, 
                    u.name || ' ' || u.surname AS created_by,
                    td.created_time
                FROM task_detail td
                LEFT JOIN task_status ts ON td.status = ts.id
                LEFT JOIN users u ON td.created_by = u.code
                WHERE td.task_id = %s
                ORDER BY td.created_time ASC;
            """, (task_id,))
            details_rows = cur.fetchall()

            sub_tasks = []
            for drow in details_rows:
                sub_tasks.append({
                    "id": drow[0],
                    "task_id": drow[1],
                    "description": drow[2],
                    "status": drow[3],
                    "created_by": drow[4],
                    "created_time": drow[5]
                })

            # Sonuç yapısı (Aynı Kalır)
            tasks_result.append({
                "task_id": row[0],
                "project_code": row[1],
                "title": row[2],
                "description": row[3],
                "created_time": row[4],
                "created_by": row[5],
                "start_date": row[6],
                "end_date": row[7],
                "status_id": row[8],
                "status_definition": row[9],
                "status_category": row[10],
                "priority_id": row[11],
                "priority_definition": row[12],
                "type_id": row[13],
                "type_definition": row[14],
                "assigned_users": assigned_users,
                "sub_tasks": sub_tasks
            })

        return tasks_result

    except Exception as e:
        print("Query error:", e)
        return {"status": False, "error": str(e)}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_details_for_task_edit(task_id: str):
    conn, cur = get_connection()
    if conn is None:
        return {"status": False, "error": "DB connection failed"}

    try:
        query_task = """
            SELECT 
                t.project_code, 
                t.title, 
                t.description, 
                t.start_date, 
                t.end_date, 
                ts.definition AS status_definition, 
                tt.definition AS type_definition, 
                tp.definition AS priority_definition, 
                (SELECT array_agg(s.definition ORDER BY s.id ASC) FROM public.task_status s WHERE t.project_code = s.project_code) AS all_status_definitions, 
                (SELECT array_agg(ty.definition ORDER BY ty.id ASC) FROM public.task_type ty WHERE t.project_code = ty.project_code) AS all_type_definitions, 
                (SELECT array_agg(p.definition ORDER BY p.id ASC) FROM public.task_priorities p WHERE t.project_code = p.project_code) AS all_priority_definitions
            FROM public.tasks t
            LEFT JOIN public.task_status ts ON t.last_status = ts.id
            LEFT JOIN public.task_type tt ON t.type = tt.id
            LEFT JOIN public.task_priorities tp ON t.priority = tp.id
            WHERE t.id = %s
            ORDER BY t.id ASC;
        """
        cur.execute(query_task, (task_id,))
        task_details = cur.fetchone()
        if not task_details:
            return {"status": False, "error": "Task not found"}

        # Attachments
        query_attachments = "SELECT encode(file, 'base64') AS file_data, file_name FROM public.attachments WHERE task_id = %s ORDER BY id ASC;"
        cur.execute(query_attachments, (task_id,))
        attachments_rows = cur.fetchall()
        attachments = [
            {"name": r[1], "data": r[0], "size":0}
            for r in attachments_rows
        ]

                    
        # Users
        query_users = """
            SELECT
                (SELECT json_agg(json_build_object('name', u.name || ' ' || u.surname, 'code', u.code) ORDER BY u.code ASC)
                 FROM public.tasks_assignment ta
                 JOIN public.users u ON ta.user_code = u.code
                 WHERE ta.task_id = %s) AS assigned_members,
                (SELECT json_agg(json_build_object('name', u.name || ' ' || u.surname, 'code', u.code) ORDER BY u.code ASC)
                 FROM public.users u
                 WHERE u.code NOT IN (
                     SELECT ta.user_code FROM public.tasks_assignment ta WHERE ta.task_id = %s
                 )
                 AND u.code <> (SELECT t.created_by FROM public.tasks t WHERE t.id = %s)
                ) AS unassigned_members;
        """
        cur.execute(query_users, (task_id, task_id, task_id))
        users_row = cur.fetchone()
        assigned_members = users_row[0] or []
        unassigned_members = users_row[1] or []

        # Subtasks
        query_subtasks = """
            SELECT
                td.id AS subtask_id,
                td.description AS subtask_description,
                (SELECT json_agg(json_build_object('name', u.name || ' ' || u.surname, 'code', u.code) ORDER BY u.code ASC)
                 FROM public.task_detail_assignment tda
                 JOIN public.users u ON tda.assigned_user = u.code
                 WHERE tda.detail_task_id = td.id) AS assigned_members,
                (SELECT json_agg(json_build_object('name', u.name || ' ' || u.surname, 'code', u.code) ORDER BY u.code ASC)
                 FROM public.users u
                 WHERE u.code NOT IN (
                     SELECT tda.assigned_user FROM public.task_detail_assignment tda WHERE tda.detail_task_id = td.id
                 )
                 AND u.code <> td.created_by
                ) AS unassigned_members
            FROM public.task_detail td
            WHERE td.task_id = %s
            ORDER BY td.id ASC;
        """
        cur.execute(query_subtasks, (task_id,))
        subtasks_rows = cur.fetchall()
        subtasks = [
            {
                "subtask_id": s[0],
                "description": s[1],
                "assigned_members": s[2] or [],
                "unassigned_members": s[3] or []
            }
            for s in subtasks_rows
        ]

        # Sonuç
        result = {
            "status": True,
            "task": {
                "project_code": task_details[0],
                "title": task_details[1],
                "description": task_details[2],
                "start_date": task_details[3],
                "end_date": task_details[4],
                "status_definition": task_details[5],
                "type_definition": task_details[6],
                "priority_definition": task_details[7],
                "all_status_definitions": task_details[8] or [],
                "all_type_definitions": task_details[9] or [],
                "all_priority_definitions": task_details[10] or []
            },
            "attachments": attachments,
            "users": {
                "assigned_members": assigned_members,
                "unassigned_members": unassigned_members
            },
            "subtasks": subtasks
        }

        return result

    except Exception as e:
        print("Query error:", e)
        return {"status": False, "error": str(e)}

    finally:
        if cur: cur.close()
        if conn: conn.close()

def update_task(model: EditTaskFullModel):
    conn, cur = get_connection()
    if conn is None:
        return False

    try:
        # Transaction başlat
        conn.autocommit = False

        # --- ATTACHMENTS ---
        cur.execute("""
            SELECT id, file_name
            FROM attachments
            WHERE task_id = %s
        """, (model.task_id,))
        attachments_rows = cur.fetchall()
        old_attachments = {a[1]: a[0] for a in attachments_rows}
        new_attachments = {a.name: a for a in model.attachments}

        for file_name, file_id in old_attachments.items():
            if file_name not in new_attachments:
                cur.execute("DELETE FROM attachments WHERE id = %s", (file_id,))

        for attachment in model.attachments:

            if attachment.size > 0:
                cur.execute("""
                    INSERT INTO attachments (
                        task_id, file, uploaded_at, owner_code, file_name
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    model.task_id,
                    bytes(attachment.data),
                    datetime.now(),
                    model.user_code,
                    attachment.name
                ))

        # --- TASKS ---
        cur.execute("""
            SELECT ts.id
            FROM task_status ts
            WHERE ts.project_code = %s AND ts.definition = %s
        """, (model.project_code, model.status_definition))
        status_id = cur.fetchone()[0]

        cur.execute("""
            SELECT tp.id
            FROM task_priorities tp
            WHERE tp.project_code = %s AND tp.definition = %s
        """, (model.project_code, model.priority_definition))
        priority_id = cur.fetchone()[0]

        cur.execute("""
            SELECT tt.id
            FROM task_type tt
            WHERE tt.project_code = %s AND tt.definition = %s
        """, (model.project_code, model.type_definition))
        type_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE tasks
            SET title = %s,
                description = %s,
                start_date = %s,
                end_date = %s,
                last_status = %s,
                priority = %s,
                type = %s
            WHERE id = %s
        """, (
            model.title,
            model.description,
            model.startDate,
            model.endDate,
            status_id,
            priority_id,
            type_id,
            int(model.task_id)
        ))

        # --- TASKS ASSIGNMENT ---
        cur.execute("""
            SELECT user_code
            FROM tasks_assignment
            WHERE task_id = %s
        """, (model.task_id,))
        current_members = set([row[0] for row in cur.fetchall()])
        new_members = set([m.code for m in model.assigned_members])

        to_delete = current_members - new_members
        to_insert = new_members - current_members

        if to_delete:
            cur.execute("""
                DELETE FROM tasks_assignment
                WHERE task_id = %s AND user_code = ANY(%s)
            """, (model.task_id, list(to_delete)))

        for member_code in to_insert:
            cur.execute("""
                INSERT INTO tasks_assignment (task_id, user_code, assigned_at, assigned_by)
                VALUES (%s, %s, NOW(), %s)
            """, (model.task_id, member_code, model.user_code))

        # --- SUBTASKS ---
        cur.execute("""
            SELECT id, description
            FROM task_detail
            WHERE task_id = %s
        """, (model.task_id,))
        existing_subtasks = {row[1]: row[0] for row in cur.fetchall()}
        new_subtasks = set([sub.description for sub in model.subtasks_raw])

        to_delete = set(existing_subtasks.keys()) - new_subtasks
        to_insert = new_subtasks - set(existing_subtasks.keys())
        still_exist = new_subtasks & set(existing_subtasks.keys())

        # Silme işlemleri
        for desc in to_delete:
            subtask_id = existing_subtasks[desc]
            cur.execute("""
                DELETE FROM task_detail_assignment
                WHERE detail_task_id = %s
            """, (subtask_id,))
            cur.execute("""
                DELETE FROM task_detail
                WHERE id = %s
            """, (subtask_id,))

        # Ekleme işlemleri
        for desc in to_insert:
            cur.execute("""
                INSERT INTO task_detail (task_id, description, created_by)
                VALUES (%s, %s, %s) RETURNING id
            """, (model.task_id, desc, model.user_code))
            subtask_id = cur.fetchone()[0]

            incoming_subtask = next(
                (s for s in model.subtasks_raw if s.subtask_id == subtask_id),
                None
            )

            if incoming_subtask is None:
                users = set()
            else:
                users = set(member.code for member in incoming_subtask.assigned_members)

            for member in users:
                cur.execute("""
                    INSERT INTO task_detail_assignment (detail_task_id, assigned_user, timestamp)
                    VALUES (%s, %s, NOW())
                """, (subtask_id, member.code))

        # Hâlâ olan subtasks için assignment güncelleme
        for desc in still_exist:
            subtask_id = existing_subtasks[desc]

            cur.execute("""
                SELECT assigned_user
                FROM task_detail_assignment
                WHERE detail_task_id = %s
            """, (subtask_id,))
            current_members = set(row[0] for row in cur.fetchall())

            incoming_subtask = next(
                (s for s in model.subtasks_raw if s.subtask_id == subtask_id),
                None
            )

            if incoming_subtask is None:
                new_members = set()
            else:
                new_members = set(member.code for member in incoming_subtask.assigned_members)

            for user_code in current_members:
                if user_code not in new_members:
                    cur.execute("""
                        DELETE FROM task_detail_assignment
                        WHERE detail_task_id = %s AND assigned_user = %s
                    """, (subtask_id, user_code))

            # Eklenmesi gerekenler
            for user_code in new_members:
                if user_code not in current_members:
                    cur.execute("""
                        INSERT INTO task_detail_assignment (detail_task_id, assigned_user, assigned_at)
                        VALUES (%s, %s, NOW())
                    """, (subtask_id, user_code))
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