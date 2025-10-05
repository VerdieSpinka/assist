# server/main.py

import os
import sys
import io
import asyncio
from dotenv import load_dotenv

# Load environment variables from a .env file at the project root.
# This should be one of the first things done to ensure all modules have access to them.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Warning: .env file not found. Relying on system environment variables.")

# Pastikan stdout dan stderr menggunakan encoding utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# --- Impor Router dan Service ---
print('Importing websocket_router')
from routers.websocket_router import *
print('Importing routers')
from routers import (
    auth_router,
    config_router,
    image_router,
    root_router,
    workspace,
    canvas,
    ssl_test,
    chat_router,
    settings,
    tool_confirmation
)
# --- PERUBAHAN DI SINI ---
from fastapi import FastAPI, HTTPException # <-- Impor HTTPException dari fastapi
from fastapi.responses import FileResponse # <-- Impor FileResponse secara terpisah
# --- AKHIR PERUBAHAN ---
from fastapi.staticfiles import StaticFiles
import argparse
from contextlib import asynccontextmanager
from starlette.types import Scope
from starlette.responses import Response
import socketio # type: ignore

print('Importing websocket_state')
from services.websocket_state import sio
print('Importing websocket_service')
from services.websocket_service import broadcast_init_done
print('Importing config_service')
from services.config_service import config_service
print('Importing tool_service')
from services.tool_service import tool_service
from services.db_service import db_service

root_dir = os.path.dirname(__file__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fungsi yang dieksekusi saat startup dan shutdown server."""
    # --- ON STARTUP ---
    print('Initializing config_service')
    await config_service.initialize()
    print('Initializing tool_service (generic)')
    await tool_service.initialize()
    print('Initializing broadcast_init_done')
    await broadcast_init_done()
    
    yield
    
    # --- ON SHUTDOWN ---
    # (Tambahkan kode cleanup di sini jika perlu)

print('Creating FastAPI app')
app = FastAPI(lifespan=lifespan)

# --- Integrasi Router ---
#print('Including routers')
app.include_router(auth_router.router)
app.include_router(config_router.router)
app.include_router(settings.router)
app.include_router(root_router.router)
app.include_router(canvas.router)
app.include_router(workspace.router)
app.include_router(image_router.router)
app.include_router(ssl_test.router)
app.include_router(chat_router.router)
app.include_router(tool_confirmation.router)

# --- Penyajian File Statis (Frontend React) ---
react_build_dir = os.environ.get('UI_DIST_DIR', os.path.join(
    os.path.dirname(root_dir), "react", "dist"))

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

static_site_assets = os.path.join(react_build_dir, "assets")
if os.path.exists(static_site_assets):
    app.mount("/assets", NoCacheStaticFiles(directory=static_site_assets), name="assets")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_react_app(full_path: str):
    """Menyajikan aplikasi React, termasuk menangani routing di sisi klien."""
    file_path = os.path.join(react_build_dir, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    index_path = os.path.join(react_build_dir, "index.html")
    if os.path.exists(index_path):
        response = FileResponse(index_path)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    raise HTTPException(status_code=404, detail="React app not found.")

print('Creating socketio app')
# Menggabungkan aplikasi FastAPI dengan Socket.IO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path='/socket.io')

# --- Entry Point Aplikasi ---
if __name__ == "__main__":
    # Mengatasi masalah proxy untuk request ke localhost
    _bypass = {"127.0.0.1", "localhost", "::1"}
    current = set(os.environ.get("no_proxy", "").split(",")) | set(
        os.environ.get("NO_PROXY", "").split(","))
    os.environ["no_proxy"] = os.environ["NO_PROXY"] = ",".join(
        sorted(_bypass | current - {""}))

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=57988,
                        help='Port to run the server on')
    args = parser.parse_args()
    
    import uvicorn
    print("🌟Starting server, UI_DIST_DIR:", react_build_dir)
    
    # Fungsi untuk memeriksa dan memberikan notifikasi tentang pengguna root

    uvicorn.run(socket_app, host="127.0.0.1", port=args.port)
    
    
