from typing import Dict, Any, List
from .base_phase_controller import BasePhaseController
from ...models.game_state import GamePhase
from ...models.game_log import GameEvent, GameEventType

class NightPhaseController(BasePhaseController):
    async def execute(self) -> None:
        """执行夜晚阶段的逻辑"""
        if self.game_state.current_phase == GamePhase.NIGHT_START:
            self.game_state.start_new_round()
            
        elif self.game_state.current_phase == GamePhase.WEREWOLF_TURN:
            await self._handle_werewolf_turn()
            
        elif self.game_state.current_phase == GamePhase.SEER_TURN:
            await self._handle_seer_turn()
            
        elif self.game_state.current_phase == GamePhase.WITCH_TURN:
            await self._handle_witch_turn()
            
        elif self.game_state.current_phase == GamePhase.NIGHT_END:
            self._process_night_actions()
    
    def _process_night_actions(self):
        """处理夜晚行动的结果"""
        night_action = self.game_state.current_round.night_action
        
        # 处理死亡
        if night_action.werewolf_kill and not night_action.witch_save:
            player = self.game_state.get_player_by_id(night_action.werewolf_kill)
            if player:
                player.is_alive = False
                player.death_reason = "werewolf"
                self.game_state.current_round.deaths.append({
                    "player_id": player.id,
                    "reason": "werewolf"
                })
                
        if night_action.witch_poison:
            player = self.game_state.get_player_by_id(night_action.witch_poison)
            if player:
                player.is_alive = False
                player.death_reason = "poison"
                self.game_state.current_round.deaths.append({
                    "player_id": player.id,
                    "reason": "poison"
                })
    
    async def _handle_werewolf_turn(self) -> None:
        """处理狼人回合"""
        werewolves = [p for p in self.game_state.get_alive_players() 
                      if p.role.role_type == RoleType.WEREWOLF]
        
        if werewolves:
            votes = {}
            for wolf in werewolves:
                action = await self.game_state.role_controllers[RoleType.WEREWOLF].handle_night_action(wolf.id)
                if "werewolf_kill" in action:
                    votes[wolf.id] = action["werewolf_kill"]["target_id"]
                    
            # 处理投票结果
            final_target = self.game_state.role_controllers[RoleType.WEREWOLF].process_kill_votes(votes)
            if final_target:
                self.game_state._last_night_killed = final_target
                
    # ... 其他回合的处理方法 ... 