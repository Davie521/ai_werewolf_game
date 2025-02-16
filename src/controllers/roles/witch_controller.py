from typing import Dict, Any, Optional
from .base_role_controller import BaseRoleController
from ...models.game_log import GameEvent, GameEventType

class WitchController(BaseRoleController):
    async def handle_night_action(self, player_id: int) -> Dict[str, Any]:
        """处理女巫的用药行动"""
        player = self.game_state.get_player_by_id(player_id)
        if not player or not player.is_alive:
            return {}
            
        action = await self.api_controller.generate_night_action(player, self.game_state)
        result = {}
        
        # 处理解药使用
        if "witch_save" in action:
            if action["witch_save"]["used"]:
                killed_player = self.game_state.get_killed_player(player_id)
                if killed_player:
                    if player.role.use_potion("save"):
                        result["witch_save"] = {"target_id": killed_player.id}
                        self.game_log.add_event(GameEvent(
                            GameEventType.WITCH_SAVE,
                            {
                                "player_id": player_id,
                                "target_id": killed_player.id,
                                "target_name": killed_player.name,
                                "message": f"你使用解药救活了 {killed_player.name}"
                            },
                            public=False
                        ))
        
        # 处理毒药使用
        if "witch_poison" in action and action["witch_poison"]["target_id"] is not None:
            target_id = action["witch_poison"]["target_id"]
            target = self.game_state.get_player_by_id(target_id)
            if target and target.is_alive and player.role.use_potion("poison"):
                result["witch_poison"] = {"target_id": target_id}
                self.game_log.add_event(GameEvent(
                    GameEventType.WITCH_POISON,
                    {
                        "player_id": player_id,
                        "target_id": target_id,
                        "target_name": target.name,
                        "message": f"你使用毒药毒死了 {target.name}"
                    },
                    public=False
                ))
                
        return result 