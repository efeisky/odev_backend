from typing import Any, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from datetime import date
from app.controllers.log_controller import log_message
from app.controllers.task_controller import get_details_for_task_edit, set_task, set_task_detail, set_task_attachment, get_projects_for_task, get_tasks, set_main_task_status, set_sub_task_status, get_project_tasks, update_task
from app.model.task_model import EditTaskFullModel

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/getProjectsForTask")
async def getProjectsForTask(user_code: str = Query(...)):
    log_message(user_code=user_code, message="Görevler için projeler çekildi.")
    result = get_projects_for_task(user_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch projects"}
    
    return {
        "status": True, 
        "data": {
            "projects": result
        }
    }

class AttachmentModel(BaseModel):
    name: str
    data: Any
class SubtaskModel(BaseModel):
    id: int
    title: str
    assignedUserIds: List[str]
class UserModel(BaseModel):
    id: str
    name: str
class SetTaskRequest(BaseModel):
    project_code: str = Field(..., alias="project_code")
    created_by: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    status_definition: Optional[str] = ""
    priority_definition: Optional[str] = ""
    type_definition: Optional[str] = ""
    attachments: List[AttachmentModel] = []
    subtasks: List[SubtaskModel] = []
    users: List[UserModel] = []
@router.post("/setTask")
async def setTask(data: SetTaskRequest):
    log_message(
        user_code=data.created_by,
        message=f"{data.project_code} için {data.title} adlı görev oluşturdu."
    )
    result = set_task(data.model_dump())
    return {"status": result}


class SetTaskDetailRequest(BaseModel):
    project_code: str
    task_id: int
    description: str
    status_definition: str
    created_by: str

@router.post("/setTaskDetail")
async def setTaskDetail(data: SetTaskDetailRequest):
    log_message(
        user_code=data.created_by,
        message=f"{data.task_id} için {data.description} adlı alt görev oluşturuldu."
    )
    result = set_task_detail(data.model_dump())
    return {"status": result}

class SetTaskAttachment(BaseModel):
    task_id: str
    user_id: str
    attachments: List[AttachmentModel] = []
@router.post("/setTaskAttachment")
async def setTaskAttachment(data: SetTaskAttachment):
    log_message(
        user_code=data.user_id,
        message=f"{data.task_id} için dosya eklendi."
    )
    result = set_task_attachment(data.model_dump())

    return {"status": result}


@router.get("/getTasks")
async def getTasks(user_code: str = Query(...)):
    log_message(
        user_code=user_code,
        message=f"Görev listesini çekti."
    )
    result = get_tasks(user_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch projects"}
    
    return {
        "status": True, 
        "data": {
            "tasks": result
        }
    }


class SetMainTaskStatusRequest(BaseModel):
    task_id: int
    new_status: str

@router.put("/setMainTaskStatus")
async def setMainTaskStatus(data: SetMainTaskStatusRequest):
    result = set_main_task_status(new_status=data.new_status, task_id=data.task_id)
    return {"status": result}


class SetSubTaskStatusRequest(BaseModel):
    task_id: int
    sub_id: int
    new_status: str

@router.put("/setSubTaskStatus")
async def setSubTaskStatus(data: SetSubTaskStatusRequest):
    result = set_sub_task_status(new_status=data.new_status, task_id=data.task_id, sub_id=data.sub_id)
    return {"status": result}

@router.get("/getProjectTasks")
async def getProjectTasks(user_code: str, project_code: str = Query(...)):
    log_message(
        user_code=user_code,
        message=f"{project_code} için görev listesini çekti."
    )
    result = get_project_tasks(user_code, project_code)
    
    if result is False:
        return {"status": False, "message": "Unable to fetch projects"}
    
    return {
        "status": True, 
        "data": {
            "tasks": result
        }
    }

@router.get("/getDetailsForTaskEdit")
async def getDetailsForTaskEdit(user_code: str, task_id: str = Query(...)):
    log_message(
        user_code=user_code,
        message=f"{task_id} için düzenleme amaçlı görev detayı çekti."
    )
    result = get_details_for_task_edit(task_id)

    if result is False:
        return {"status": False, "message": "Unable to fetch task"}
    
    return {
        "status": True, 
        "data": result
    }

class EditUserModel(BaseModel):
    name: str
    code: str
class EditAttachmentModel(BaseModel):
    name: str
    data: Any
    size: int
class EditSubtaskModel(BaseModel):
    subtask_id: int
    description: str
    assigned_members: List[EditUserModel]
    unassigned_members: List[EditUserModel]
class TaskEditModel(BaseModel):
    project_code: str
    title: str
    description: str
    startDate: str
    endDate: str
    status_definition: str
    type_definition: str
    priority_definition: str
    all_status_definitions: List[str]
    all_type_definitions: List[str]
    all_priority_definitions: List[str]
    assigned_members: List[EditUserModel]
    unassigned_members: List[EditUserModel]
    attachments: List[EditAttachmentModel]
    subtasks_raw: List[EditSubtaskModel]
    edited_by: str
    task_id: str
@router.post("/completeEdit")
async def completeEdit(data: TaskEditModel):
    log_message(
        user_code=data.edited_by,
        message=f"{data.task_id} kodlu görev için düzenleme yaptı."
    )
    model = EditTaskFullModel(
        user_code=data.edited_by,
        project_code=data.project_code,
        assigned_members=data.assigned_members,
        attachments=data.attachments,
        description=data.description,
        endDate=data.endDate,
        priority_definition=data.priority_definition,
        startDate=data.startDate,
        status_definition=data.status_definition,
        subtasks_raw=data.subtasks_raw,
        task_id=data.task_id,
        title=data.title,
        type_definition=data.type_definition
    )
    result = update_task(model)

    if result is False:
        return {"status": False, "message": "Unable to update task"}
    
    return {
        "status": True, 
        "data": result
    }