"""
Image generation core module
Contains the main orchestration logic for image generation across different providers
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException # Tambahkan impor ini
from common import DEFAULT_PORT
from tools.utils.image_utils import process_input_image
from ..image_providers.image_base_provider import ImageProviderBase
from services.db_service import db_service # Tambahkan impor ini

# 导入所有提供商以确保自动注册 (不要删除这些导入)
from ..image_providers.jaaz_provider import JaazImageProvider
from ..image_providers.openai_provider import OpenAIImageProvider
from ..image_providers.replicate_provider import ReplicateImageProvider
from ..image_providers.volces_provider import VolcesProvider
from ..image_providers.wavespeed_provider import WavespeedProvider

# from ..image_providers.comfyui_provider import ComfyUIProvider
from .image_canvas_utils import (
    save_image_to_canvas,
)
import time

IMAGE_PROVIDERS: dict[str, ImageProviderBase] = {
    "jaaz": JaazImageProvider(),
    "openai": OpenAIImageProvider(),
    "replicate": ReplicateImageProvider(),
    "volces": VolcesProvider(),
    "wavespeed": WavespeedProvider(),
}


async def generate_image_with_provider(
    canvas_id: str,
    session_id: str,
    provider: str,
    model: str,
    prompt: str,
    aspect_ratio: str = "1:1",
    input_images: Optional[list[str]] = None,
    user_id: Optional[int] = None # Tambahkan user_id
) -> str:
    """
    Fungsi pembuatan gambar universal...
    """

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required for image generation.")

    # --- PENERAPAN PEMERIKSAAN KREDIT ---
    can_generate = await db_service.check_and_update_credits(user_id)
    if not can_generate:
        raise HTTPException(status_code=429, detail="Batas pembuatan gambar harian telah tercapai.")
    # --- AKHIR PEMERIKSAAN ---

    provider_instance = IMAGE_PROVIDERS.get(provider)
    if not provider_instance:
        raise ValueError(f"Unknown provider: {provider}")

    # Process input images for the provider
    processed_input_images: list[str] | None = None
    if input_images:
        processed_input_images = []
        for image_path in input_images:
            processed_image = await process_input_image(image_path)
            if processed_image:
                processed_input_images.append(processed_image)

        print(f"Using {len(processed_input_images)} input images for generation")

    # Prepare metadata with all generation parameters
    metadata: Dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "provider": provider,
        "aspect_ratio": aspect_ratio,
        "input_images": input_images or [],
    }

    # Generate image using the selected provider
    mime_type, width, height, filename = await provider_instance.generate(
        prompt=prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        input_images=processed_input_images,
        metadata=metadata,
    )

    # Save image to canvas
    image_url = await save_image_to_canvas(
        session_id, canvas_id, filename, mime_type, width, height
    )

    return f"image generated successfully ![image_id: {filename}](http://localhost:{DEFAULT_PORT}{image_url})"
