from datetime import date, datetime
from typing import Any, List, Optional

class SetTaskModel:
    p_code: str
    title: str
    description: str
    last_status: int
    type: int
    created_time: int
    created_by: str
    start_date: date
    end_date: date
    priority: int

    def __init__(
        self,
        p_code: str,
        title: str,
        description: str,
        last_status: int,
        type: int,
        created_by: str,
        start_date: date,
        end_date: date,
        priority: int
    ):
        self.p_code = p_code
        self.title = title
        self.description = description
        self.last_status = last_status
        self.type = type
        self.created_by = created_by
        self.start_date = start_date
        self.end_date = end_date
        self.priority = priority
        self.created_time = datetime.now()

        
class SetTaskDetailModel:
    task_id: int
    description: str
    status: int
    created_by: int
    created_time: int

    def __init__(
        self,
        task_id: int,
        description: str,
        status: int,
        created_by: int,
    ):
        self.task_id = task_id
        self.description = description
        self.status = status
        self.created_by = created_by
        self.created_time = datetime.now()

class EditUserModel:
    code: str

    def __init__(self, code: str):
        self.code = code


class EditAttachmentModel:
    name: str
    data: Any
    size: int

    def __init__(self, name: str, data: Any, size: int):
        self.name = name
        self.data = data
        self.size = size


class EditSubtaskModel:
    description: str
    assigned_members: List[EditUserModel]

    def __init__(self, description: str, assigned_members: Optional[List[EditUserModel]] = None):
        self.description = description
        self.assigned_members = assigned_members or []


class EditTaskFullModel:
    project_code: str
    task_id: str
    title: str
    description: str
    startDate: str
    endDate: str
    user_code: str
    status_definition: str
    type_definition: str
    priority_definition: str
    assigned_members: List[EditUserModel]
    attachments: List[EditAttachmentModel]
    subtasks_raw: List[EditSubtaskModel]

    def __init__(
        self,
        project_code: str,
        task_id: str,
        title: str,
        description: str,
        startDate: str,
        endDate: str,
        user_code: str,
        status_definition: str,
        type_definition: str,
        priority_definition: str,
        assigned_members: Optional[List[EditUserModel]] = None,
        attachments: Optional[List[EditAttachmentModel]] = None,
        subtasks_raw: Optional[List[EditSubtaskModel]] = None,
    ):
        self.project_code = project_code
        self.task_id = task_id
        self.title = title
        self.description = description
        self.startDate = startDate
        self.endDate = endDate
        self.status_definition = status_definition
        self.type_definition = type_definition
        self.priority_definition = priority_definition
        self.assigned_members = assigned_members or []
        self.attachments = attachments or []
        self.subtasks_raw = subtasks_raw or []
        self.user_code = user_code