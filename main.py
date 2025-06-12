from fastapi import FastAPI, Depends, HTTPException, status, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, User
from models import hash_password, verify_password
import os
import shutil
from pathlib import Path
from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Add session middleware using starlette-session
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "your-secret-key"),  # Use env var or default
    backend_type=BackendType.cookie,  # Store sessions in cookies
    cookie_name="session_cookie",  # Name of the session cookie
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to authenticate user
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Initialize admin user on startup
def initialize_admin_user(db: Session):
    admin_username = "admin"
    admin_password = os.getenv("ADMIN_PASSWORD", "admin_password")  # Use env var or default

    admin_user = db.query(User).filter(User.username == admin_username).first()
    if not admin_user:
        hashed_pwd = hash_password(admin_password)
        admin_user = User(username=admin_username, hashed_password=hashed_pwd, is_admin=True)
        db.add(admin_user)
        db.commit()
        print(f"Admin user '{admin_username}' created successfully.")
    else:
        print(f"Admin user '{admin_username}' already exists.")

# Startup event to initialize admin user
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    initialize_admin_user(db)
    db.close()

# Get base path from environment variable or use default
BASE_PATH = Path(os.getenv("BASE_PATH", r"E:\vit dump\VIT Downloads"))  # Use env var or default
if not BASE_PATH.exists():
    raise FileNotFoundError(f"Base path does not exist: {BASE_PATH}")

# Utility function to validate and resolve paths
def validate_and_resolve_path(base_path: Path, path: str) -> Path:
    """Validate and resolve a path within the base path."""
    full_path = base_path / path.lstrip("/")
    try:
        full_path.resolve().relative_to(base_path.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    return full_path

# Home route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login route
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Set session
    request.session["user_id"] = user.id
    request.session["is_admin"] = user.is_admin
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# Admin-only user registration
# GET route to render the registration form
@app.get("/register", response_class=HTMLResponse)
async def get_register_form(request: Request):
    # Only allow admins to access the registration form
    user_id = request.session.get("user_id")
    if not user_id or not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admins can access the registration form")
    
    return templates.TemplateResponse("register.html", {"request": request})

# POST route to handle form submission
@app.post("/register", response_class=HTMLResponse)
async def register_user(username: str = Form(...), password: str = Form(...), is_admin: bool = Form(False), db: Session = Depends(get_db), request: Request = None):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admins can register users")
    
    # Check for duplicate username
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pwd = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_pwd, is_admin=is_admin)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# Dashboard route
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, path: str = "/"):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Validate and resolve path
    full_path = validate_and_resolve_path(BASE_PATH, path)

    if not full_path.exists():
        files_and_dirs = None
        return templates.TemplateResponse("dashboard.html", {"request": request, "path": path, "files": files_and_dirs})

    if full_path.is_dir():
        files_and_dirs = [{"name": f.name, "is_dir": f.is_dir()} for f in full_path.iterdir()]
        return templates.TemplateResponse("dashboard.html", {"request": request, "path": path, "files": files_and_dirs})
    else:
        return FileResponse(full_path, filename=full_path.name)

# Upload file route
@app.post("/upload/")
async def upload_file(path: str = Form(...), file: UploadFile = File(...), request: Request = None):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate and resolve path
    full_path = validate_and_resolve_path(BASE_PATH, path)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    file_location = full_path / file.filename
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    # Redirect back to the same directory
    return RedirectResponse(url=f"/dashboard?path={path}", status_code=status.HTTP_303_SEE_OTHER)

# Delete file or directory route
@app.post("/delete/{path:path}")
async def delete_file_or_directory(path: str, request: Request = None):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate and resolve path
    full_path = validate_and_resolve_path(BASE_PATH, path)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File or directory not found")

    if full_path.is_file():
        full_path.unlink()  # Delete file
    elif full_path.is_dir():
        shutil.rmtree(full_path)  # Recursively delete directory

    # Redirect back to the parent directory
    parent_path = "/".join(path.split("/")[:-1]) or "/"
    return RedirectResponse(url=f"/dashboard?path={parent_path}", status_code=status.HTTP_303_SEE_OTHER)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
