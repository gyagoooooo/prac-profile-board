import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import aiofiles
import aiosqlite
import bcrypt
import jwt
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


SECRET_KEY = "super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "profile_users.db"
FRONTEND_DIR = BASE_DIR / "profile_frontend"
UPLOAD_DIR = BASE_DIR / "uploads" / "profile_images"
UPLOAD_URL_PREFIX = "/uploads/profile_images"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_profile_image(profile_image_json: Optional[str]) -> Optional[dict]:
    if not profile_image_json:
        return None

    try:
        return json.loads(profile_image_json)
    except json.JSONDecodeError:
        return None


def serialize_user(row: aiosqlite.Row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "profile_image": decode_profile_image(row["profile_image_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def model_dump_exclude_unset(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                profile_image_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await db.commit()
    yield


app = FastAPI(
    title="Profile Management API",
    description="FastAPI + JWT + bcrypt + aiofiles + aiosqlite profile backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")
# app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="profile_frontend")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def fetch_user_by_id(db: aiosqlite.Connection, user_id: int) -> Optional[aiosqlite.Row]:
    async with db.execute(
        """
        SELECT id, username, email, hashed_password, profile_image_json, created_at, updated_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ) as cursor:
        return await cursor.fetchone()


async def fetch_user_by_email(db: aiosqlite.Connection, email: str) -> Optional[aiosqlite.Row]:
    async with db.execute(
        """
        SELECT id, username, email, hashed_password, profile_image_json, created_at, updated_at
        FROM users
        WHERE email = ?
        """,
        (email,),
    ) as cursor:
        return await cursor.fetchone()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    user = await fetch_user_by_id(db, user_id_int)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return serialize_user(user)


@app.get("/")
async def root():
    return {
        "message": "Profile Management API",
        "docs": "/docs",
        "uploads": UPLOAD_URL_PREFIX,
    }


@app.post("/register", status_code=201)
async def register(payload: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.strip().lower()
    password = payload.password

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Username, email and password are required")

    if await fetch_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    timestamp = now_text()
    hashed_password = hash_password(password)

    cursor = await db.execute(
        """
        INSERT INTO users (
            username, email, hashed_password, profile_image_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (username, email, hashed_password, None, timestamp, timestamp),
    )
    await db.commit()

    user = await fetch_user_by_id(db, cursor.lastrowid)
    return serialize_user(user)


@app.post("/login", response_model=Token)
async def login(payload: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    email = payload.email.strip().lower()
    user = await fetch_user_by_email(db, email)

    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        {"sub": str(user["id"])},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me")
async def read_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/users")
async def list_users(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    async with db.execute(
        """
        SELECT id, username, email, profile_image_json, created_at, updated_at
        FROM users
        ORDER BY id DESC
        """
    ) as cursor:
        rows = await cursor.fetchall()

    return [serialize_user(row) for row in rows]


@app.get("/users/{user_id}")
async def read_user(
    user_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return serialize_user(user)


@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only modify your own account")

    user = await fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = model_dump_exclude_unset(payload)
    username = update_data.get("username", user["username"])
    email = update_data.get("email", user["email"])
    password = update_data.get("password")

    username = username.strip() if username else ""
    email = email.strip().lower() if email else ""

    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required")

    existing_email_user = await fetch_user_by_email(db, email)
    if existing_email_user and existing_email_user["id"] != user_id:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(password) if password else user["hashed_password"]

    await db.execute(
        """
        UPDATE users
        SET username = ?, email = ?, hashed_password = ?, updated_at = ?
        WHERE id = ?
        """,
        (username, email, hashed_password, now_text(), user_id),
    )
    await db.commit()

    updated_user = await fetch_user_by_id(db, user_id)
    return serialize_user(updated_user)


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    user = await fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await db.commit()

    return {"message": "User deleted", "user_id": user_id}


async def save_profile_image(user_id: int, file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image content type")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file is not allowed")

    saved_filename = f"user_{user_id}_{uuid.uuid4().hex}{extension}"
    saved_path = UPLOAD_DIR / saved_filename

    async with aiofiles.open(saved_path, "wb") as out_file:
        await out_file.write(content)

    return {
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "content_type": file.content_type,
        "size": len(content),
        "url": f"{UPLOAD_URL_PREFIX}/{saved_filename}",
        "uploaded_at": now_text(),
    }


@app.post("/users/{user_id}/profile-image")
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only upload your own profile image")

    user = await fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    image_metadata = await save_profile_image(user_id, file)
    image_metadata_json = json.dumps(image_metadata, ensure_ascii=False)

    await db.execute(
        """
        UPDATE users
        SET profile_image_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (image_metadata_json, now_text(), user_id),
    )
    await db.commit()

    return {
        "message": "Profile image uploaded",
        "user_id": user_id,
        "profile_image": image_metadata,
    }


@app.get("/users/{user_id}/profile-image")
async def read_profile_image_metadata(
    user_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await fetch_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_image = decode_profile_image(user["profile_image_json"])
    if not profile_image:
        raise HTTPException(status_code=404, detail="Profile image not found")

    return profile_image


@app.exception_handler(aiosqlite.IntegrityError)
async def sqlite_integrity_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
