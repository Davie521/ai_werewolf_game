from typing import Dict, Any, List, Optional, Tuple
from .base_phase_controller import BasePhaseController
from ...models.game_state import GameState, GamePhase
from ...models.game_log import GameLog, GameEvent, GameEventType
from ...models.roles.base_role import RoleType
from ...models.player import Player

class DayPhaseController(BasePhaseController):
    async def execute(self) -> None:
        """执行白天阶段的逻辑"""
        if self.game_state.current_phase == GamePhase.DAY_START:
            self._process_night_deaths()
            
        elif self.game_state.current_phase == GamePhase.VOTE:
            await self._handle_vote()
            
        elif self.game_state.current_phase == GamePhase.EXILE:
            self._process_vote_result()
            
    def _process_night_deaths(self):
        """处理夜晚的死亡情况"""
        deaths = self.game_state.current_round.deaths
        if deaths:
            death_details = []
            for death in deaths:
                player = self.game_state.get_player_by_id(death["player_id"])
                if player:
                    death_details.append({
                        "player_id": player.id,
                        "player_name": player.name,
                        "role": player.role.name,
                        "reason": death["reason"]
                    })
            
            self.game_log.add_event(GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {"deaths": death_details}
            ))
            
            # 检查是否有猎人死亡，如果是被毒死则不能开枪
            for death in deaths:
                player = self.game_state.get_player_by_id(death["player_id"])
                if (player and player.role.role_type == RoleType.HUNTER and 
                    death["reason"] == "poison"):
                    player.role.can_shoot = False
    
    async def _handle_vote(self):
        """处理投票阶段"""
        # 获取所有存活玩家
        alive_players = self.game_state.get_alive_players()
        
        # 记录每个玩家的投票
        for voter in alive_players:
            action = await self.api_controller.get_vote_action(voter.id)
            if action and "target_id" in action:
                self.game_state.record_vote(voter.id, action["target_id"])
    
    def _process_vote_result(self) -> Tuple[Optional[Player], bool]:
        """处理投票结果
        
        Returns:
            Tuple[Optional[Player], bool]: (被放逐的玩家, 是否平票)
        """
        # 统计票数
        vote_counts = {}
        for voter_id, target_id in self.game_state.current_round.day_votes.items():
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        # 找出票数最多的玩家
        if not vote_counts:
            return None, False
            
        max_votes = max(vote_counts.values())
        most_voted = [pid for pid, votes in vote_counts.items() if votes == max_votes]
        
        # 如果有平票，则没有人被放逐
        if len(most_voted) > 1:
            self.game_log.add_event(GameEvent(
                GameEventType.VOTE_RESULT,
                {"is_tie": True}
            ))
            return None, True
        
        # 处理放逐
        exiled_id = most_voted[0]
        exiled_player = self.game_state.get_player_by_id(exiled_id)
        if exiled_player:
            exiled_player.die("voted")
            self.game_state.record_exile(exiled_id)
            
            # 记录放逐事件
            self.game_log.add_event(GameEvent(
                GameEventType.VOTE_RESULT,
                {
                    "is_tie": False,
                    "voted_id": exiled_id,
                    "voted_name": exiled_player.name,
                    "role": exiled_player.role.name
                }
            ))
            
            # 如果是猎人被放逐，可以开枪（除非之前被毒死）
            if (exiled_player.role.role_type == RoleType.HUNTER and 
                exiled_player.role.can_shoot):
                # 记录猎人可以开枪的事件
                self.game_log.add_event(GameEvent(
                    GameEventType.HUNTER_SHOT,
                    {
                        "hunter_id": exiled_id,
                        "hunter_name": exiled_player.name,
                        "time": "exile"
                    }
                ))
            
        return exiled_player, False
            
    async def _handle_exile_hunter_shot(self) -> None:
        """处理放逐后的猎人开枪"""
        # 检查被放逐的玩家是否是猎人
        exiled_id = self.game_state.current_round.exiled_player
        if exiled_id:
            exiled_player = self.game_state.get_player_by_id(exiled_id)
            if (exiled_player and 
                exiled_player.role.role_type == RoleType.HUNTER and 
                exiled_player.role.can_shoot):
                # 使用猎人控制器处理开枪行为
                hunter_controller = self.game_state.role_controllers[RoleType.HUNTER]
                shot_result = await hunter_controller.handle_death(exiled_id)
                if shot_result and "target_id" in shot_result.get("hunter_shot", {}):
                    # 处理开枪结果
                    target_id = shot_result["hunter_shot"]["target_id"]
                    target = self.game_state.get_player_by_id(target_id)
                    if target:
                        target.die("hunter_shot")
                        # 记录猎人开枪事件
                        self.game_log.add_event(GameEvent(
                            GameEventType.HUNTER_SHOT,
                            {
                                "hunter_id": exiled_id,
                                "hunter_name": exiled_player.name,
                                "target_id": target_id,
                                "target_name": target.name,
                                "target_role": target.role.name,
                                "time": "exile"
                            }
                        ))
            
    # ... 各个阶段的具体处理方法 ... 