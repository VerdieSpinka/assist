# server/services/tool_service.py

import traceback
from typing import Dict
from langchain_core.tools import BaseTool
from models.tool_model import ToolInfo
from tools.write_plan import write_plan_tool
from tools.generate_image_by_gpt_image_1_jaaz import generate_image_by_gpt_image_1_jaaz
from tools.generate_image_by_imagen_4_jaaz import generate_image_by_imagen_4_jaaz
from tools.generate_image_by_imagen_4_replicate import (
    generate_image_by_imagen_4_replicate,
)
from tools.generate_image_by_ideogram3_bal_jaaz import (
    generate_image_by_ideogram3_bal_jaaz,
)
from tools.generate_image_by_flux_kontext_pro_jaaz import (
    generate_image_by_flux_kontext_pro_jaaz,
)
from tools.generate_image_by_flux_kontext_pro_replicate import (
    generate_image_by_flux_kontext_pro_replicate,
)
from tools.generate_image_by_flux_kontext_max_jaaz import (
    generate_image_by_flux_kontext_max,
)
from tools.generate_image_by_flux_kontext_max_replicate import (
    generate_image_by_flux_kontext_max_replicate,
)
from tools.generate_image_by_doubao_seedream_3_jaaz import (
    generate_image_by_doubao_seedream_3_jaaz,
)
from tools.generate_image_by_doubao_seedream_3_volces import (
    generate_image_by_doubao_seedream_3_volces,
)
from tools.generate_image_by_doubao_seededit_3_volces import (
    edit_image_by_doubao_seededit_3_volces,
)
from tools.generate_video_by_seedance_v1_jaaz import generate_video_by_seedance_v1_jaaz
from tools.generate_video_by_seedance_v1_pro_volces import (
    generate_video_by_seedance_v1_pro_volces,
)
from tools.generate_video_by_seedance_v1_lite_volces import (
    generate_video_by_seedance_v1_lite_t2v,
    generate_video_by_seedance_v1_lite_i2v,
)
from tools.generate_video_by_kling_v2_jaaz import generate_video_by_kling_v2_jaaz
from tools.generate_image_by_recraft_v3_jaaz import generate_image_by_recraft_v3_jaaz
from tools.generate_image_by_recraft_v3_replicate import (
    generate_image_by_recraft_v3_replicate,
)
from tools.generate_video_by_hailuo_02_jaaz import generate_video_by_hailuo_02_jaaz
from tools.generate_video_by_veo3_fast_jaaz import generate_video_by_veo3_fast_jaaz
from tools.generate_image_by_midjourney_jaaz import generate_image_by_midjourney_jaaz
from services.config_service import config_service
from services.db_service import db_service

# ... (TOOL_MAPPING tetap sama, tidak perlu diubah)
TOOL_MAPPING: Dict[str, ToolInfo] = {
    # ... (isi TOOL_MAPPING di sini)
}

class ToolService:
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self._register_required_tools()

    def _register_required_tools(self):
        try:
            self.tools["write_plan"] = {
                "provider": "system",
                "tool_function": write_plan_tool,
            }
        except ImportError as e:
            print(f"❌ 注册必须工具失败 write_plan: {e}")

    def register_tool(self, tool_id: str, tool_info: ToolInfo):
        if tool_id in self.tools:
            # print(f"🔄 TOOL ALREADY REGISTERED: {tool_id}")
            return
        self.tools[tool_id] = tool_info

    async def initialize(self, user_id: int = None):
        self.clear_tools()
        try:
            if user_id:
                user_configs = await db_service.get_user_api_keys(user_id)
            else:
                user_configs = config_service.app_config

            for provider_name, provider_config in user_configs.items():
                if provider_config.get("api_key", ""):
                    for tool_id, tool_info in TOOL_MAPPING.items():
                        if tool_info.get("provider") == provider_name:
                            self.register_tool(tool_id, tool_info)

        except Exception as e:
            print(f"❌ Failed to initialize tool service: {e}")
            traceback.print_stack()

    def get_tool(self, tool_name: str) -> BaseTool | None:
        tool_info = self.tools.get(tool_name)
        return tool_info.get("tool_function") if tool_info else None

    def remove_tool(self, tool_id: str):
        self.tools.pop(tool_id)

    def get_all_tools(self) -> Dict[str, ToolInfo]:
        return self.tools.copy()

    def clear_tools(self):
        self.tools.clear()
        self._register_required_tools()


tool_service = ToolService()