from typing import Dict, Any, List, Optional
from .base_role_controller import BaseRoleController
from ...models.game_log import GameEvent, GameEventType

class WerewolfController(BaseRoleController):
    async def handle_night_action(self, player_id: int) -> Dict[str, Any]:
        """处理狼人夜晚击杀行动"""
        player = self.game_state.get_player_by_id(player_id)
        if not player or not player.is_alive:
            return {}
            
        action = await self.api_controller.generate_night_action(player, self.game_state)
        if "werewolf_kill" in action and action["werewolf_kill"]["target_id"] is not None:
            target_id = action["werewolf_kill"]["target_id"]
            target = self.game_state.get_player_by_id(target_id)
            if target:
                self.game_log.add_event(GameEvent(
                    GameEventType.WEREWOLF_KILL,
                    {
                        "player_id": player_id,
                        "target_id": target_id,
                        "target_name": target.name
                    },
                    public=False
                ))
                return {"werewolf_kill": {"target_id": target_id}}
        return {}
        
    def process_kill_votes(self, votes: Dict[int, int]) -> Optional[int]:
        """处理狼人击杀投票"""
        if not votes:
            return None
            
        # 统计票数
        vote_count = {}
        for target_id in votes.values():
            vote_count[target_id] = vote_count.get(target_id, 0) + 1
            
        # 找出最高票数的目标
        max_votes = max(vote_count.values())
        targets = [tid for tid, v in vote_count.items() if v == max_votes]
        
        return targets[0] if len(targets) == 1 else None 