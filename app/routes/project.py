from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.controllers.general_controller import get_all_users_for_project
from app.controllers.log_controller import log_message
from app.model.project_model import SetMemberModel, SetManagerModel, SetProjectModel, ChangeRoleModel, UnAuthorizeUserModel, EditProjectModel
from typing import List, Literal, Optional
from app.controllers.authentication_controller import set_member, set_manager
from app.controllers.project_controller import edit_project, get_project_constants, get_project_users, set_project, change_role, unauthorize_user, delete_project, get_members, change_status, get_projects, get_project_detail
from datetime import date

router = APIRouter(prefix="/project", tags=["Project"])

@router.get("/getProjects")
async def getProjects(user_code: str = Query(...)):
    log_message(
        user_code=user_code,
        message=f"Proje listesini çekti."
    )
    result = get_projects(user_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch projects"}
    
    return {
        "status": True, 
        "data": {
            "projects": result
        }
    }

class Item(BaseModel):
    code: Optional[int] = None
    name: str
class ExtraUser(BaseModel):
    code: str
    role: Optional[str] = None
class SetProjectRequest(BaseModel):
    manager_code: Optional[str]
    date_start: date
    date_end: date
    definition: str
    extra_users: List[ExtraUser] = Field(default_factory=list)
    statuses: List[Item] = Field(default_factory=list)
    priorities: List[Item] = Field(default_factory=list)
    types: List[Item] = Field(default_factory=list)
@router.post("/setProject")
async def setProject(data: SetProjectRequest):
    model = SetProjectModel(
        manager_code=data.manager_code,
        date_start=data.date_start,
        date_end=data.date_end,
        definition=data.definition,
        extra_users=data.extra_users,
        statuses=data.statuses,
        priorities=data.priorities,
        types=data.types
    )
    status = set_project(model=model)
    
    return {"status": status}

class AuthorizeUserRequest(BaseModel):
    user_code: str
    project_code: str
    role_type: Literal['project_member', 'project_manager']
    project_role: Literal['admin', 'viewer', 'editor'] | None
@router.put("/authorizeUser")
async def authorizeUser(data: AuthorizeUserRequest):
    log_message(
        user_code=data.user_code,
        message=f"Kullanıcı rolü güncelleme fonksiyonu çalıştırıldı."
    )
    if data.role_type == "project_member":
        model = SetMemberModel(project_code=data.project_code, user_code=data.user_code, project_role=data.project_role)
        status = set_member(model)
        
        return {"status": status}
    else:
        model = SetManagerModel(project_code= data.project_code, user_code= data.user_code)
        status = set_manager(model)
        return {"status": status}

class ChangeRoleRequest(BaseModel):
    user_code: str
    project_code: str
    project_role: Literal['admin', 'viewer', 'editor']
@router.put("/changeRole")
async def changeRole(data: ChangeRoleRequest):
    model = ChangeRoleModel(data.project_code, data.user_code, data.project_role)
    status = change_role(model)

    return {"status": status}

class ChangeStatusRequest(BaseModel):
    project_code: str
    project_status: Literal['reseraching', 'started', 'continue', 'finished', 'canceled']
@router.put("/changeProjectStatus")
async def changeStatus(data: ChangeStatusRequest):
    status = change_status(project_code=data.project_code, new_status=data.project_status)

    return {"status": status}

class UnAuthorizeUserRequest(BaseModel):
    user_code: str
    project_code: str
@router.delete("/unauthorizeUser")
async def unauthorizeUser(data: UnAuthorizeUserRequest):
    model = UnAuthorizeUserModel(data.project_code, data.user_code)
    status = unauthorize_user(model)

    return {"status": status}

class DeleteProjectRequest(BaseModel):
    project_code: str
@router.delete("/deleteProject")
async def deleteProject(data: DeleteProjectRequest):
    status = delete_project(data.project_code)

    return {"status": status}

@router.get("/getMembers")
async def getMembers(project_code: str = Query(...)):
    result = get_members(project_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch members"}
    
    return {
        "status": True, 
        "data": {
            "members": result
        }
    }

@router.get("/getProjectDetail")
async def getProjectDetail(project_code: str = Query(...)):
    result = get_project_detail(project_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch detail"}
    
    return {
        "status": True, 
        "data": result
    }

@router.get("/getProjectForEdit")
async def getProjectForEdit(project_code: str = Query(...)):
    users_result = get_all_users_for_project()
    if users_result is False:
        return {"status": False, "message": "Unable to fetch users"}
    
    detail_result = get_project_detail(project_code)
    
    if detail_result is False:
        return {"status": False, "message": "Unable to fetch detail"}
    
    return {
        "status": True, 
        "data": {
            "users": users_result,
            "details": detail_result
        }
    }

@router.get("/getProjectConstants")
async def getProjectConstants(project_code: str = Query(...)):
    result = get_project_constants(project_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch constants"}
    
    return {
        "status": True, 
        "data": result
    }

@router.get("/projectUsers")
async def getProjectUsers(project_code: str = Query(...)):
    result = get_project_users(project_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch users"}
    
    return {
        "status": True, 
        "data": {
            "users": result
        }
    }

class Item(BaseModel):
    id: int
    name: str
class ExtraUser(BaseModel):
    code: str
    full_name: str
    role: str
class UpdateProjectRequest(BaseModel):
    project_code: str
    edited_by: str
    definition: str
    startDate: str
    endDate: str
    managerId: str
    priorities: List[Item]
    statuses: List[Item]
    types: List[Item]
    extraUsers: List[ExtraUser]

@router.put("/editProject")
async def editProject(data: UpdateProjectRequest):
    log_message(
        user_code=data.edited_by,
        message=f"{data.project_code} projesi için düzenleme yaptı."
    )
    model = EditProjectModel(data.model_dump())
    result = edit_project(model)

    if result is False:
        return {"status": False, "message": "Unable to update task"}
    
    return {
        "status": True, 
        "data": result
    }