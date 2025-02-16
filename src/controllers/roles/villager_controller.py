from typing import Dict, Any
from .base_role_controller import BaseRoleController

class VillagerController(BaseRoleController):
    async def handle_night_action(self, player_id: int) -> Dict[str, Any]:
        """平民没有夜晚行动"""
        return {} 