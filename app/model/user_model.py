class UserModel:
    code: str
    name: str
    surname: str
    email: str
    password: str
    phone_number: str | None

    def __init__(self, code: str, name: str, surname: str, email: str, password: str, phone_number: str | None):
        self.code = code
        self.name = name
        self.surname = surname
        self.email = email
        self.password = password
        self.phone_number = phone_number


class UpdateUserModel:
    code: str
    name: str
    surname: str
    email: str
    phone: str | None
    password: str | None
    
    def __init__(self, code: str, name: str, surname: str, email: str, password: str | None, phone_number: str | None): 
        self.code = code
        self.name = name
        self.surname = surname
        self.email = email
        self.password = password
        self.phone_number = phone_number