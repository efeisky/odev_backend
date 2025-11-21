from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr
from app.controllers.authentication_controller import hash_password, set_user, check_email, check_user, check_user_main
from app.controllers.log_controller import log_message
from app.utils.generate_uuid import generate_uuid
from app.cache.connection import set_cache, get_cache
from app.model.user_model import UserModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class CreateUserRequest(BaseModel):
    email: EmailStr
    phone: str | None
    name: str
    surname: str
    password: str

@router.post("/createUser")
async def create_user(data: CreateUserRequest):
    email = data.email;

    email_check = check_email(email=email)
    if email_check == False:
        return {
            "status": False,
            "message": "User couldn't created thus email must be unique."
        }
    
    hashed_password = hash_password(password=data.password);
    user_uuid = generate_uuid();

    log_message(
        user_code=user_uuid,
        message=f"Kullanıcı sisteme kayıt edildi."
    )

    model = UserModel(
        code=user_uuid,
        name=data.name,
        surname=data.surname,
        email= email,
        password= hashed_password,
        phone_number= data.phone
    )

    db_response = set_user(model=model)
    
    if db_response:
        return {
            "status": True,
            "message": "User created successfully"
        }
    else:
        return {
            "status": False,
            "message": "User couldn't created."
        }

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def login_user(data: LoginUserRequest):
    email = data.email;
    hashed_password = hash_password(password=data.password);

    db_response = check_user(email=email, password= hashed_password);

    if db_response:
        log_message(
            user_code=db_response,
            message=f"Kullanıcı sisteme giriş yaptı."
        )
        cache_key = generate_uuid();
        set_cache(cache_key=cache_key, uuid= db_response)

        return {
            "status": True,
            "message": "User login successfully",
            "data": {
                "key": cache_key
            }
        }
    else:
        return {
            "status": False,
            "message": "Giriş işlemi yapılamadı."
        }


@router.get("/check")
async def check_user_route(key: str = Query(...), response: Response = None):
    cached_key = get_cache(key)
    if cached_key:
        db_response = check_user_main(cached_key)
        if db_response != False:
            response.set_cookie(
                key="user_code",
                value=cached_key,
                httponly=False,
                secure=False,
                samesite="lax"
            )
            response.set_cookie(
                key="user_role",
                value=db_response["role"],
                httponly=False,
                secure=False,
                samesite="lax"
            )
            return {
                "status": True,
                "data": {
                    "auth": "Authenticated."
                },
            }

    raise HTTPException(
        status_code=401,
        detail={
            "status": False,
            "data": {
                "auth": None
            },
        }
    )