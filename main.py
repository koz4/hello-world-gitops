from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os
import time

# Konfiguracja bazy danych z zmiennych środowiskowych OpenShift
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "db-service")
DB_NAME = os.getenv("DB_NAME", "crud_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Czekanie na dostępność bazy danych przy starcie
def wait_for_db(url, retries=10):
    for i in range(retries):
        try:
            temp_engine = create_engine(url)
            temp_engine.connect()
            return temp_engine
        except Exception as e:
            print(f"Waiting for DB... {e} (attempt {i+1}/{retries})")
            time.sleep(5)
    return create_engine(url)

engine = wait_for_db(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model bazy danych
class TodoItem(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Modele Pydantic
class TodoCreate(BaseModel):
    title: str

class TodoUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None

class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    class Config:
        from_attributes = True

app = FastAPI(title="CRUD API OpenShift")

# Dependency dla sesji DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpointy CRUD
@app.get("/api/todos", response_model=list[TodoResponse])
def get_todos(db: Session = Depends(get_db)):
    return db.query(TodoItem).all()

@app.post("/api/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_item = TodoItem(title=todo.title)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/api/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    db_item = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Not found")
    if todo.title is not None:
        db_item.title = todo.title
    if todo.completed is not None:
        db_item.completed = todo.completed
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_item = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item)
    db.commit()
    return {"status": "ok"}

# Serwowanie frontendu
@app.get("/")
def read_index():
    return FileResponse("html/index.html")

app.mount("/html", StaticFiles(directory="html"), name="html")
