from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import User
from auth import hash_password, verify_password, create_token, decode_token
from RAG import ask_question         

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return decode_token(token)
    except Exception:
        return None


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login")

@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")   

@app.get("/register", include_in_schema=False)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.get("/chat", include_in_schema=False)      
def chat_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request, "chat.html", {
            "username": user.get("sub"),
            "department": user.get("dept")
        }
    )

#POST

@app.post("/register", include_in_schema=False)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    department: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            request, "register.html", {"error": "Email already registered"}
        )
    new_user = User(
        username=username,
        email=email,
        password=hash_password(password),
        department=department.lower().strip()   
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


@app.post("/login", include_in_schema=False)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Invalid email or password"}
        )
    token = create_token({
        "sub": user.email,
        "dept": user.department
    })
    response = RedirectResponse(url="/chat", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@app.post("/ask", include_in_schema=False)       
def ask(request: Request, query: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"answer": "Session expired. Please log in again."})

    department = user.get("dept")
    answer = ask_question(query, department)
    return JSONResponse({"answer": answer})