from typing import List, Literal, Optional

from pydantic import BaseModel
from app.utils.generate_uuid import generate_uuid
from datetime import date

class SetMemberModel:
    project_code: str
    user_code: str
    project_role: Literal['admin', 'viewer', 'editor']

    def __init__(self, project_code: str, user_code: str, project_role:  Optional[Literal['admin', 'viewer', 'editor']] = None):
        self.project_code = project_code
        self.user_code = user_code
        self.project_role = project_role if project_role is not None else 'viewer'


class SetManagerModel:
    project_code: str
    user_code: str

    def __init__(self, project_code: str, user_code: str):
        self.project_code = project_code
        self.user_code = user_code


class Item(BaseModel):
    code: Optional[str] = None
    name: str

class ExtraUser(BaseModel):
    code: str
    role: Optional[str] = None

class SetProjectModel:
    project_code: str
    manager_code: str
    date_start: date
    date_end: date
    definition: str
    status: str = "reseraching"
    extra_users: List[ExtraUser]
    statuses: List[Item]
    priorities: List[Item]
    types: List[Item]

    def __init__(
        self,
        manager_code: str,
        date_start: date,
        date_end: date,
        definition: str,
        extra_users: Optional[List[ExtraUser]] = None,
        statuses: Optional[List[Item]] = None,
        priorities: Optional[List[Item]] = None,
        types: Optional[List[Item]] = None,
    ):
        self.project_code = generate_uuid()
        self.manager_code = manager_code
        self.date_start = date_start
        self.date_end = date_end
        self.definition = definition
        self.extra_users = extra_users or []
        self.statuses = statuses or []
        self.priorities = priorities or []
        self.types = types or []
        
class ChangeRoleModel:
    project_code: str
    user_code: str
    project_role: Literal['admin', 'viewer', 'editor']

    def __init__(self, project_code: str, user_code: str, project_role:  Literal['admin', 'viewer', 'editor']):
        self.project_code = project_code
        self.user_code = user_code
        self.project_role = project_role

        
class UnAuthorizeUserModel:
    project_code: str
    user_code: str

    def __init__(self, project_code: str, user_code: str):
        self.project_code = project_code
        self.user_code = user_code
