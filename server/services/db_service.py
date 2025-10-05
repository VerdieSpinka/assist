# server/services/db_service.py

import os
import json
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from gotrue.errors import AuthApiError

# --- Konfigurasi Awal ---
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service class for managing all interactions with the Supabase database.
    This implementation exclusively uses the Supabase client, removing all local SQLite dependencies.
    """
    def __init__(self):
        """
        Initializes the Supabase client using environment variables.
        """
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY") # Menggunakan SUPABASE_KEY (service_role) untuk operasi backend

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment variables.")

        try:
            self.client: Client = create_client(url, key)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    # --- User & Authentication Methods ---
    def create_user(self, username: str, email: str, hashed_password: str, role: str = 'user') -> int:
        try:
            response = self.client.table('users').insert({
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "role": role
            }).execute()
            
            if response.data:
                return response.data[0]['id']
            raise Exception("User creation failed, no data returned.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during user creation: {e}")
            raise

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        response = self.client.table('users').select("*").eq('id', user_id).maybe_single().execute()
        return response.data if response.data else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        response = self.client.table('users').select("*").eq('username', username).maybe_single().execute()
        return response.data if response.data else None
        
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        response = self.client.table('users').select("*").eq('email', email).maybe_single().execute()
        return response.data if response.data else None

    def get_user_api_keys(self, user_id: int) -> Dict[str, Any]:
        response = self.client.table('user_api_keys').select("providers_config").eq('user_id', user_id).maybe_single().execute()
        return response.data.get('providers_config', {}) if response.data else {}

    def update_user_api_keys(self, user_id: int, configs: Dict[str, Any]):
        self.client.table('user_api_keys').upsert({
            "user_id": user_id,
            "providers_config": configs
        }, on_conflict="user_id").execute()

    # --- Canvas Methods ---
    def create_canvas(self, id: str, name: str):
        self.client.table('canvases').insert({"id": id, "name": name}).execute()

    def list_canvases(self) -> List[Dict[str, Any]]:
        response = self.client.table('canvases').select("*").order('updated_at', desc=True).execute()
        return response.data
            
    def get_canvas_data(self, id: str) -> Optional[Dict[str, Any]]:
        response = self.client.table('canvases').select("data, name").eq('id', id).maybe_single().execute()
        
        if not response.data:
            return None
        
        sessions = self.list_sessions(id)
        
        return {
            'data': response.data.get('data') or {},
            'name': response.data.get('name'),
            'sessions': sessions
        }

    def save_canvas_data(self, id: str, data: str, thumbnail: Optional[str] = None):
        try:
            canvas_data_obj = json.loads(data)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in canvas data for canvas ID {id}. Saving as empty object.")
            canvas_data_obj = {}

        self.client.table('canvases').update({
            "data": canvas_data_obj,
            "thumbnail": thumbnail,
            "updated_at": "now()"
        }).eq('id', id).execute()
            
    def rename_canvas(self, id: str, name: str):
        self.client.table('canvases').update({"name": name, "updated_at": "now()"}).eq('id', id).execute()

    def delete_canvas(self, id: str):
        self.client.table('canvases').delete().eq('id', id).execute()

    # --- Chat Methods ---
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        response = self.client.table('chat_messages').select("message").eq('session_id', session_id).order('id', desc=False).execute()
        return [row['message'] for row in response.data if row.get('message')]
        
    def list_sessions(self, canvas_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.client.table('chat_sessions').select("id, title, model, provider, created_at, updated_at")
        if canvas_id:
            query = query.eq('canvas_id', canvas_id)
        response = query.order('updated_at', desc=True).execute()
        return response.data

    def create_chat_session(self, session_id: str, model: str, provider: str, canvas_id: str, title: str):
        self.client.table('chat_sessions').insert({
            "id": session_id,
            "model": model,
            "provider": provider,
            "canvas_id": canvas_id,
            "title": title
        }).execute()

    def create_message(self, session_id: str, role: str, message: str):
        try:
            message_obj = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Message for session {session_id} is not a valid JSON string. Wrapping it in a content object.")
            message_obj = {"content": message}

        self.client.table('chat_messages').insert({
            "session_id": session_id,
            "role": role,
            "message": message_obj
        }).execute()
        
    # --- Comfy Workflows Methods ---
    def create_comfy_workflow(self, name: str, api_json: str, description: str, inputs: str, outputs: str):
        self.client.table('comfy_workflows').insert({
            "name": name,
            "api_json": json.loads(api_json),
            "description": description,
            "inputs": json.loads(inputs),
            "outputs": json.loads(outputs)
        }).execute()

    def list_comfy_workflows(self) -> List[Dict[str, Any]]:
        response = self.client.table('comfy_workflows').select("*").order('updated_at', desc=True).execute()
        return response.data

    def get_comfy_workflow(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        response = self.client.table('comfy_workflows').select("*").eq('id', workflow_id).maybe_single().execute()
        return response.data.get('api_json') if response.data else None

    def delete_comfy_workflow(self, workflow_id: int):
        self.client.table('comfy_workflows').delete().eq('id', workflow_id).execute()

# --- Singleton Instance ---
db_service = DatabaseService()