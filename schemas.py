from pydantic import BaseModel

class RegisterForm(BaseModel):
    username : str
    email : str
    password : str
    department : str

class LoginForm(BaseModel):
    email: str
    password: str
    