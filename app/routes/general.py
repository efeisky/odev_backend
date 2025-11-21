from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.controllers.general_controller import get_all_users_for_project, get_all_users_for_admin, delete_user, edit_activation_user, get_user_logs, update_user
from app.model.user_model import UpdateUserModel
router = APIRouter(prefix="/general", tags=["General"])

@router.get("/getUsersForAdmin")
async def get_users_for_admin():
    result = get_all_users_for_admin()
    if result is False:
        return {"status": False, "message": "Unable to fetch users"}
    
    return {
        "status": True,
        "message": "Users List has got.",
        "data": {
            "users": result
        }
    }

class DeleteUserRequest(BaseModel):
    code: str
@router.delete("/deleteUser")
async def delete_user_route(data: DeleteUserRequest):
    status = delete_user(data.code)
    return {"status": status, "message": "Delete Process"}


class EditActivationUserRequest(BaseModel):
    code: str
@router.put("/setActivationForUser")
async def delete_user_route(data: EditActivationUserRequest):
    status = edit_activation_user(data.code)
    return {"status": status, "message": "Put Process"}


class UpdateUserRequest(BaseModel):
    code: str
    name: str
    surname: str
    email: str
    phone: str | None
    password: str | None
@router.put("/updateUser")
async def update_user_request(data: UpdateUserRequest):
    data = UpdateUserModel(data.code, data.name, data.surname, data.email, data.password, data.phone)
    status = update_user(data)
    return {"status": status, "message": "Put Process"}

@router.get("/getUsersForProject")
async def get_users_for_project():
    result = get_all_users_for_project()
    if result is False:
        return {"status": False, "message": "Unable to fetch users"}
    
    return {
        "status": True,
        "message": "Users List has got.",
        "data": {
            "users": result
        }
    }


@router.get("/getLogs")
async def get_logs(user_code: str = Query(...)):
    result = get_user_logs(user_code)
    if result is False:
        return {"status": False, "message": "Unable to fetch logs"}
    
    return {
        "status": True,
        "message": "Logs List has got.",
        "data": {
            "logs": result
        }
    }