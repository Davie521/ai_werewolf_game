from typing import Dict, Any, List, Optional, Tuple
from .base_phase_controller import BasePhaseController
from ...models.game_state import GameState, GamePhase
from ...models.game_log import GameLog
from ...models.roles.base_role import RoleType
from ...models.player import Player

class DayPhaseController(BasePhaseController):
    async def execute(self) -> None:
        """执行白天阶段的逻辑"""
        # 死亡报告
        if self.game_state.current_phase == GamePhase.DEATH_REPORT:
            await self._handle_death_report()
            
        # 猎人开枪
        elif self.game_state.current_phase == GamePhase.HUNTER_SHOT:
            await self._handle_hunter_shot()
            
        # 讨论阶段
        elif self.game_state.current_phase == GamePhase.DISCUSSION:
            await self._handle_discussion()
            
        # 投票阶段
        elif self.game_state.current_phase == GamePhase.VOTE:
            await self._handle_vote()
            
        # 放逐阶段
        elif self.game_state.current_phase == GamePhase.EXILE:
            await self._handle_exile()
            
        # 放逐后的猎人开枪阶段
        elif self.game_state.current_phase == GamePhase.EXILE_HUNTER_SHOT:
            await self._handle_exile_hunter_shot()
            
    async def _handle_exile_hunter_shot(self) -> None:
        """处理放逐后的猎人开枪"""
        # 检查被放逐的玩家是否是猎人
        if self.game_state.voted_out:
            exiled_player = self.game_state.get_player_by_id(self.game_state.voted_out)
            if exiled_player and exiled_player.role.role_type == RoleType.HUNTER:
                # 使用猎人控制器处理开枪行为
                hunter_controller = self.game_state.role_controllers[RoleType.HUNTER]
                shot_result = await hunter_controller.handle_death(exiled_player.id)
                if shot_result:
                    # 处理开枪结果
                    target_id = shot_result["hunter_shot"]["target_id"]
                    target = self.game_state.get_player_by_id(target_id)
                    if target:
                        target.is_alive = False
                        target.death_reason = "hunter_shot"
            
    def _process_vote_result(self) -> Tuple[Optional[Player], bool]:
        """处理投票结果"""
        votes = self.game_state.current_round.day_votes
        if not votes:
            return None, False
            
        # 统计票数
        vote_count: Dict[int, int] = {}
        for target_id in votes.values():
            vote_count[target_id] = vote_count.get(target_id, 0) + 1
            
        # 找出最高票数的玩家
        max_votes = max(vote_count.values())
        most_voted = [pid for pid, count in vote_count.items() if count == max_votes]
        
        if len(most_voted) > 1:
            return None, True
            
        voted_player = self.game_state.get_player_by_id(most_voted[0])
        if voted_player:
            voted_player.is_alive = False
            voted_player.death_reason = "voted"
            self.game_state.current_round.exiled_player = voted_player.id
            
        return voted_player, False
    
    # ... 各个阶段的具体处理方法 ... 