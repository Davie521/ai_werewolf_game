from typing import Dict, Any
from ...models.game_state import GameState
from ...models.game_log import GameLog
from ..api_controller import APIController

class BasePhaseController:
    def __init__(self, game_state: GameState, game_log: GameLog, api_controller: APIController):
        self.game_state = game_state
        self.game_log = game_log
        self.api_controller = api_controller
        
    async def execute(self) -> None:
        """执行该阶段的逻辑"""
        raise NotImplementedError 