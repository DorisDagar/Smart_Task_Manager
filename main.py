from fastapi import FastAPI, Request, Depends,Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import LoginRequest, register, d_task, l_task
from database import session_x,engine
import base64
import database_models
import hashlib
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import date, timedelta
from starlette.middleware.sessions import SessionMiddleware

app=FastAPI()


database_models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    return user_id
def get_db():
    db=session_x()
    try:
        yield db
    finally:
        db.close()
def preprocess_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()
print(preprocess_password("hello"))

@app.get("/login")
def serve_login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
def serve_register_page(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@app.get("/dashboard")
def serve_dashboard_page(request: Request, user_id: int, db:Session = Depends(get_db)):
    
    user = db.query(database_models.login).filter(database_models.login.u_id == user_id).first()
    username = user.u_name if user else "User"

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username
    })

@app.get("/daily_tasks",response_class=HTMLResponse)
def serve_dashboard_page(request: Request):
    return templates.TemplateResponse("daily_tasks.html", {"request": request})

@app.get("/long_term_tasks",response_class=HTMLResponse)
def serve_dashboard_page(request: Request):
    return templates.TemplateResponse("long_term_tasks.html", {"request": request})

@app.get("/history", response_class=HTMLResponse)
def serve_history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/api/daily_tasks")
def get_tasks(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return []
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_tasks = (db.query(database_models.daily_tasks).filter(
        database_models.daily_tasks.u_id == user_id,
            database_models.daily_tasks.date == today).all())
    yesterday_pending = (db.query(database_models.daily_tasks).filter(
            database_models.daily_tasks.u_id == user_id,
            database_models.daily_tasks.date == yesterday,
            database_models.daily_tasks.is_done == False).all())
    return {
        "today": [{"t_id": t.t_id, "task": t.task, "date": str(t.date), "is_done": t.is_done} for t in today_tasks],
        "yesterday_pending": [{"t_id": t.t_id, "task": t.task, "date": str(t.date), "is_done": t.is_done} for t in yesterday_pending],
    }
@app.post("/api/daily_tasks")
def add_task(request: Request, task: d_task, db: Session = Depends(get_db)):
    # Get user_id directly from the session
    u_id = request.session.get("user_id")
 
    new_task = database_models.daily_tasks(
        u_id=u_id,
        t_id=str(uuid.uuid4()),      # auto-generate unique task id
        task=task.task,
        date=date.today()            # auto-fill current date
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "t_id": new_task.t_id,
        "task": new_task.task,
        "date": str(new_task.date)
    }
@app.post("/login")
def get_user(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(database_models.login).filter(database_models.login.u_id == req.u_id).first()

    if not user:
        return "User not found. Please create an account"
    
    # Pre-hash input password using the same method as during registration
    digest = preprocess_password(req.pwd)

    if not pwd_context.verify(digest, user.pwd_hash):
        return "Invalid Username or password"

    request.session["user_id"] = user.u_id
    return "Login Successful"

@app.post("/register")
def add_user(reg: register, db: Session = Depends(get_db)):
    
    # Pre-hash to 32 bytes
    digest = preprocess_password(reg.pwd) 

    hashed_pwd = pwd_context.hash(digest)

    new_user = database_models.login(
        u_id = reg.u_id,
        u_name = reg.u_name,
        pwd_hash = hashed_pwd,
        email = reg.email
    )

    db.add(new_user)
    db.commit()
    return "Account Created Successfully"

@app.delete("/daily_tasks/{t_id}")
def remove_task(t_id: str, request: Request, db: Session = Depends(get_db)):
    task = db.query(database_models.daily_tasks).filter(
        database_models.daily_tasks.t_id == t_id
    ).first()

    if not task:
        return {"detail": "Task not found"}

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

@app.patch("/daily_tasks/{t_id}")
def update_task_status(t_id: str,
    is_done: bool = Query(...),  # read from query string
    db: Session = Depends(get_db)):
    task = db.query(database_models.daily_tasks).filter(
        database_models.daily_tasks.t_id == t_id).first()
    if not task:
        return {"detail": "Task not found"}
    task.is_done = is_done

    if is_done:
        task.complete_date = date.today()
    else:
        # If marked undone, reset completion date
        task.complete_date = None

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated",
        "is_done": task.is_done,
        "complete_date": task.complete_date
    }
    db.commit()
    return {"message": "Task updated", "is_done": task.is_done}

@app.post("/api/long_term_tasks")
def add_task(request: Request, task: l_task, db: Session = Depends(get_db)):
    # Get user_id directly from the session
    u_id = request.session.get("user_id")
 
    new_task = database_models.long_term_tasks(
        u_id=u_id,
        t_id=str(uuid.uuid4()),      # auto-generate unique task id
        task=task.task,
        add_date=date.today(),       # auto-fill current date
        due_date= task.due_date,
        is_done= False,
        complete_date= None
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "t_id": new_task.t_id,
        "task": new_task.task,
        "add_date": str(new_task.add_date),
        "due_date": new_task.due_date,
        "is_done": new_task.is_done,
        "complete_date": new_task.complete_date
    }

@app.get("/api/long_term_tasks")
def get_all_tasks(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return []
    tasks = (db.query(database_models.long_term_tasks).filter(
        database_models.long_term_tasks.u_id == user_id).all())
    result = [
        {
            "t_id": t.t_id,
            "task": t.task,
            "add_date": str(t.add_date),
            "due_date": str(t.due_date),
            "is_done": t.is_done
            
        }
        for t in tasks
    ]

    return {"tasks": result}

@app.patch("/long_term_tasks/{t_id}")
def update_task_status(t_id: str,
    is_done: bool = Query(...),  # read from query string
    db: Session = Depends(get_db)):
    task = db.query(database_models.long_term_tasks).filter(
        database_models.long_term_tasks.t_id == t_id).first()
    if not task:
        return {"detail": "Task not found"}
    task.is_done = is_done
    #update/clear complete_date
    if is_done:
        task.complete_date = date.today()
    else:
        task.complete_date = None

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated",
        "is_done": task.is_done,
        "complete_date": task.complete_date
    }

@app.delete("/long_term_tasks/{t_id}")
def remove_task(t_id: str, request: Request, db: Session = Depends(get_db)):
    task = db.query(database_models.long_term_tasks).filter(
        database_models.long_term_tasks.t_id == t_id
    ).first()

    if not task:
        return {"detail": "Task not found"}

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@app.get("/api/task_history")
def get_task_history(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return []
    
    all_tasks = []

    # daily tasks
    for t in db.query(database_models.daily_tasks).filter(
        database_models.daily_tasks.u_id == user_id).all():

        all_tasks.append({
            "type": "Daily",
            "name": t.task,
            "added_on": t.date,
            "status": "Completed" if t.is_done else "Pending",
            "completed_on": t.complete_date
        })

    # long term tasks
    for t in db.query(database_models.long_term_tasks).filter(
        database_models.long_term_tasks.u_id == user_id).all():
        all_tasks.append({
            "type": "Long-Term",
            "name": t.task,
            "added_on": t.add_date,
            "status": "Completed" if t.is_done else "Pending",
            "completed_on": t.complete_date
        })

    return {"tasks": all_tasks}