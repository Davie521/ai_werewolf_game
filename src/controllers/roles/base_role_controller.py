from typing import Optional, Dict, Any
from ...models.game_state import GameState
from ...models.game_log import GameLog
from ..api_controller import APIController

class BaseRoleController:
    def __init__(self, game_state: GameState, game_log: GameLog, api_controller: APIController):
        self.game_state = game_state
        self.game_log = game_log
        self.api_controller = api_controller
        
    async def handle_night_action(self, player_id: int) -> Dict[str, Any]:
        """处理角色的夜晚行动"""
        raise NotImplementedError
        
    def handle_death(self, player_id: int) -> None:
        """处理角色死亡时的特殊效果"""
        pass 