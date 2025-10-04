from fastapi import APIRouter, Request, Depends
from services.config_service import config_service, DEFAULT_PROVIDERS_CONFIG
from services.tool_service import tool_service
from routers.auth_router import get_current_user # <-- Impor dependency
from typing import Dict, Any
from services.db_service import db_service

router = APIRouter(prefix="/api/config")

    # Endpoint ini tidak lagi diperlukan karena config sekarang per pengguna
    # @router.get("/exists")
    # async def config_exists():
    #     return {"exists": config_service.exists_config()}

@router.get("")
async def get_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user['id']
    user_configs = await db_service.get_user_api_keys(user_id)
        
        # Gabungkan dengan default config untuk memastikan semua provider ada
        # Ini penting agar frontend bisa menampilkan semua opsi provider
        # meskipun pengguna belum menyimpannya.
        
        # Mulai dengan salinan default config
    final_config = {k: v.copy() for k, v in DEFAULT_PROVIDERS_CONFIG.items()}
        
        # Timpa dengan konfigurasi pengguna
    for provider, config in user_configs.items():
        if provider in final_config:
            final_config[provider].update(config)
        else:
            final_config[provider] = config

        # Masking API keys sebelum mengirim ke frontend
    for provider in final_config:
        if final_config[provider].get('api_key'):
            final_config[provider]['api_key'] = '********'

    return final_config


@router.post("")
async def update_config(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user['id']
    new_config_from_frontend = await request.json()

        # Dapatkan config lama dari DB untuk mempertahankan kunci API yang tidak diubah
    existing_config = await db_service.get_user_api_keys(user_id)

        # Gabungkan perubahan dari frontend
    for provider, config in new_config_from_frontend.items():
        if provider not in existing_config:
            existing_config[provider] = {}
            
            # Jika api_key tidak diubah (masih '********'), gunakan yang lama dari DB.
        if config.get('api_key') == '********' and existing_config[provider].get('api_key'):
            config['api_key'] = existing_config[provider]['api_key']
            
        existing_config[provider].update(config)

    await db_service.update_user_api_keys(user_id, existing_config)

        # Perbarui config_service untuk sesi saat ini (opsional, tergantung implementasi tool)
        # config_service.app_config = await db_service.get_user_api_keys(user_id)

        # Selalu re-initialize tools setelah update config
    await tool_service.initialize(user_id)
        
    return {"status": "success", "message": "Configuration updated successfully"}