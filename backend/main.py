from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import random
from datetime import datetime

app = FastAPI()

class APIResponse(BaseModel):
    status: str
    response_time: float
    timestamp: str

class APICommand(BaseModel):
    command: str

responses: Dict[str, List[APIResponse]] = {}
api_commands: List[str] = []

@app.get("/api/status", response_model=Dict[str, List[APIResponse]])
def get_status():
    return responses

@app.post("/api/add", response_model=APICommand)
def add_api(api_command: APICommand):
    if api_command.command in api_commands:
        raise HTTPException(status_code=400, detail="API command already exists")
    api_commands.append(api_command.command)
    responses[api_command.command] = []
    return api_command

@app.post("/api/update_status")
def update_status():
    for command in api_commands:
        # Simulate API call results
        status = random.choice(["success", "failure"])
        response_time = round(random.uniform(0.1, 1.0), 2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = APIResponse(status=status, response_time=response_time, timestamp=timestamp)
        responses[command].append(response)
    return {"message": "Status updated"}
