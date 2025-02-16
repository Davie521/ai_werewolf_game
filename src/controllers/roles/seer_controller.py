from typing import Dict, Any, Optional
from .base_role_controller import BaseRoleController
from ...models.game_log import GameEvent, GameEventType
from ...models.roles.base_role import RoleType

class SeerController(BaseRoleController):
    async def handle_night_action(self, player_id: int) -> Dict[str, Any]:
        """处理预言家的查验行动"""
        player = self.game_state.get_player_by_id(player_id)
        if not player or not player.is_alive:
            return {}
            
        action = await self.api_controller.generate_night_action(player, self.game_state)
        if "seer_check" in action and action["seer_check"]["target_id"] is not None:
            target_id = action["seer_check"]["target_id"]
            target = self.game_state.get_player_by_id(target_id)
            
            if target:
                is_werewolf = target.role.role_type == RoleType.WEREWOLF
                check_result = "狼人" if is_werewolf else "好人"
                
                self.game_log.add_event(GameEvent(
                    GameEventType.SEER_CHECK,
                    {
                        "player_id": player_id,
                        "target_id": target_id,
                        "target_name": target.name,
                        "result": check_result,
                        "message": f"你查验了 {target.name}，Ta是{check_result}"
                    },
                    public=False
                ))
                
                return {"seer_check": {"target_id": target_id, "result": check_result}}
        return {} 