from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Task API")


class Task(BaseModel):
    id: Optional[int] = None
    title: str
    completed: bool = False


tasks_db: List[Task] = []
next_id = 1


@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks_db


@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    global next_id
    task.id = next_id
    next_id += 1
    tasks_db.append(task)
    return task


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks_db:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, updated: Task):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            updated.id = task_id
            tasks_db[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            tasks_db.pop(index)
            return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")


# Run with: uvicorn main:app --reload
