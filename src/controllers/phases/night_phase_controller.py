from typing import Dict, Any, List
from .base_phase_controller import BasePhaseController
from ...models.game_state import GamePhase
from ...models.game_log import GameEvent, GameEventType
from ...models.roles.base_role import RoleType

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
        deaths = []  # 记录死亡情况
        
        # 获取女巫
        witch = next((p for p in self.game_state.players 
                     if p.role.role_type == RoleType.WITCH and p.is_alive), None)
        
        # 处理狼人击杀
        if night_action.werewolf_kill:
            player = self.game_state.get_player_by_id(night_action.werewolf_kill)
            if player and player.is_alive:
                # 检查女巫是否可以使用解药
                can_save = (witch and night_action.witch_save and 
                          witch.role.has_potion("save"))
                if can_save:
                    # 使用解药
                    witch.role.use_potion("save")
                    self.game_state.update_witch_potion(witch.id, "save", False)
                else:
                    player.die("werewolf")
                    deaths.append({
                        "player_id": player.id,
                        "reason": "werewolf"
                    })
        
        # 处理女巫毒人（如果这回合还没用过药）
        if (night_action.witch_poison and witch and 
            not night_action.witch_save and  # 没有使用过解药
            witch.role.has_potion("poison")):  # 还有毒药
            player = self.game_state.get_player_by_id(night_action.witch_poison)
            if player and player.is_alive:
                player.die("poison")
                deaths.append({
                    "player_id": player.id,
                    "reason": "poison"
                })
                witch.role.use_potion("poison")
                self.game_state.update_witch_potion(witch.id, "poison", False)
        
        # 记录死亡情况
        self.game_state.current_round.deaths.extend(deaths)
        
        # 记录事件
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
        else:
            self.game_log.add_event(GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {"deaths": []}
            ))
    
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
                self.game_state.current_round.night_action.werewolf_kill = final_target
    
    async def _handle_witch_turn(self) -> None:
        """处理女巫回合"""
        witch = next((p for p in self.game_state.get_alive_players() 
                     if p.role.role_type == RoleType.WITCH), None)
        
        if witch:
            action = await self.game_state.role_controllers[RoleType.WITCH].handle_night_action(witch.id)
            
            # 检查是否可以使用解药
            if "witch_save" in action and action["witch_save"]["used"]:
                if witch.role.has_potion("save"):
                    self.game_state.current_round.night_action.witch_save = True
            
            # 检查是否可以使用毒药（如果这回合还没用过解药）
            if "witch_poison" in action and not self.game_state.current_round.night_action.witch_save:
                target_id = action["witch_poison"]["target_id"]
                if target_id and witch.role.has_potion("poison"):
                    self.game_state.current_round.night_action.witch_poison = target_id
    
    # ... 其他回合的处理方法 ... 