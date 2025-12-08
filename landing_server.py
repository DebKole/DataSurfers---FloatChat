from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
os.makedirs("landing/static", exist_ok=True)

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="landing/static"), name="static")

# Serve the main landing page
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        return FileResponse("landing/index.html")
    except FileNotFoundError:
        return HTMLResponse("""
            <h1>Error: Landing page not found</h1>
            <p>Make sure the landing page files are in the 'landing' directory.</p>
        """, status_code=500)

# Route handlers for navigation buttons
@app.get("/chat")
async def chat_redirect():
    # Redirect to your chat application
    # Update the URL to match your chat application's URL
    return {"message": "Redirecting to chat..."}
    # In production, you might want to use:
    # from fastapi.responses import RedirectResponse
    # return RedirectResponse(url="http://localhost:8000/chat")

@app.get("/dashboard")
async def dashboard_redirect():
    # Redirect to your dashboard
    return {"message": "Redirecting to dashboard..."}
    # return RedirectResponse(url="http://localhost:8000/dashboard")

@app.get("/maps")
async def maps_redirect():
    # Redirect to your maps
    return {"message": "Redirecting to maps..."}
    # return RedirectResponse(url="http://localhost:8000/maps")

# Serve static files directly
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    static_file = Path(f"landing/static/{file_path}")
    if not static_file.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(static_file)

# Serve the GLB file from root directory
@app.get("/Argo.glb")
async def serve_glb():
    glb_path = Path("Argo.glb")
    if not glb_path.exists():
        raise HTTPException(status_code=404, detail="GLB file not found")
    return FileResponse(glb_path, media_type="model/gltf-binary")

if __name__ == "__main__":
    PORT = 3001  # Changed from 3000 to 3001
    print("🚀 Starting Ocean Data Explorer Landing Page...")
    print(f"🌐 Server running on http://localhost:{PORT}")
    print("Press Ctrl+C to stop")
    
    try:
        uvicorn.run("landing_server:app", host="127.0.0.1", port=PORT, reload=True)
    except Exception as e:
        print(f"Error: {e}")
        print(f"Please make sure port {PORT} is available or specify a different port.")
