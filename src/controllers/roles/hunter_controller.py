from typing import Dict, Any, Optional
from .base_role_controller import BaseRoleController
from ...models.game_log import GameEvent, GameEventType

class HunterController(BaseRoleController):
    async def handle_death(self, player_id: int) -> Optional[Dict[str, Any]]:
        """处理猎人死亡时的开枪行动"""
        player = self.game_state.get_player_by_id(player_id)
        if not player or player.role.has_shot or not player.role.can_shoot:
            return None
            
        action = await self.api_controller.generate_night_action(player, self.game_state)
        if "hunter_shot" in action and action["hunter_shot"]["target_id"] is not None:
            target_id = action["hunter_shot"]["target_id"]
            target = self.game_state.get_player_by_id(target_id)
            
            if target and target.is_alive and player.role.shoot():
                self.game_log.add_event(GameEvent(
                    GameEventType.HUNTER_SHOT,
                    {
                        "player_id": player_id,
                        "target_id": target_id,
                        "target_name": target.name,
                        "message": f"猎人开枪带走了 {target.name}"
                    }
                ))
                return {"hunter_shot": {"target_id": target_id}}
        return None 