from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from config import BASE_URL, API_KEY, LLM_MODEL, PREDEFINED_ROLES
from tree import DecisionTreeGenerator
import asyncio
import threading
from typing import List

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting: {e}")

manager = ConnectionManager()

class GenerateRequest(BaseModel):
    role: str
    query: str
    mode: str = "recursive"  # "recursive" or "interactive"

class ExpandRequest(BaseModel):
    role: str
    query: str
    answer_id: str

# Global reference to the main event loop
main_loop = None
# Store the root of the current tree
current_tree_root = None

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()

def run_generation(role: str, query: str, mode: str):
    global current_tree_root
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    
    def callback(data):
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), main_loop)

    generator = DecisionTreeGenerator(client, LLM_MODEL, callback=callback)
    try:
        # Generate only root if interactive
        recursive = (mode == "recursive")
        root = generator.generate(role, query, recursive=recursive)
        current_tree_root = root
        
        # Notify completion if recursive (interactive is never "complete" in the same way)
        if recursive:
            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(manager.broadcast({"type": "complete"}), main_loop)
    except Exception as e:
        print(f"Error in generation: {e}")
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast({"type": "error", "message": str(e)}), main_loop)

def run_expansion(role: str, query: str, answer_id: str):
    global current_tree_root
    if not current_tree_root:
        return

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    
    def callback(data):
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), main_loop)

    generator = DecisionTreeGenerator(client, LLM_MODEL, callback=callback)
    
    try:
        # Find the answer node
        # Find the answer node
        node = current_tree_root.find_node_by_id(answer_id)
        if node and hasattr(node, 'potential_outcomes'): # Check if it's an AnswerNode
             new_node = generator.expand_node(role, query, node)
             if new_node is None:
                 # It's a leaf node, send conclusion
                 if main_loop and main_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast({
                            "type": "leaf", 
                            "parent_answer_id": answer_id,
                            "outcome": node.potential_outcomes[0] if node.potential_outcomes else "No outcome specified"
                        }), 
                        main_loop
                    )
    except Exception as e:
        print(f"Error in expansion: {e}")
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast({"type": "error", "message": str(e)}), main_loop)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/generate")
async def generate_tree(request: GenerateRequest):
    thread = threading.Thread(target=run_generation, args=(request.role, request.query, request.mode))
    thread.start()
    return {"status": "started"}

@app.post("/expand")
async def expand_node(request: ExpandRequest):
    thread = threading.Thread(target=run_expansion, args=(request.role, request.query, request.answer_id))
    thread.start()
    return {"status": "expanding"}

@app.get("/roles")
async def get_roles():
    return PREDEFINED_ROLES
