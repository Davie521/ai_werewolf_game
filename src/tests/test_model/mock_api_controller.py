from ...controllers.api_controller import APIController
from ...models.game_state import GameState
from ...models.player import Player

class MockAPIController(APIController):
    """简化版的Mock API控制器，用于单元测试"""
    async def generate_night_action(self, player: Player, game_state: GameState) -> dict:
        """模拟夜晚行动"""
        return {}
        
    async def generate_discussion(self, player: Player, game_state: GameState) -> str:
        """模拟发言"""
        return f"{player.name}的测试发言"
        
    async def generate_vote(self, player: Player, game_state: GameState) -> dict:
        """模拟投票"""
        return {"type": "vote", "target_id": None}
        
    async def _handle_werewolf_discussion(self, werewolves, game_state):
        return [f"{wolf.name}: 测试狼人讨论" for wolf in werewolves] 