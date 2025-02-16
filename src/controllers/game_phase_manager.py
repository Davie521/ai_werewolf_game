from typing import Dict, Optional, Tuple, List
from ..models.game_state import GameState, GamePhase, WinningTeam
from ..models.game_log import GameLog, GameEvent, GameEventType
from ..models.roles.base_role import RoleType
from .api_controller import APIController
from .phases.night_phase_controller import NightPhaseController
from .phases.day_phase_controller import DayPhaseController

class GamePhaseManager:
    def __init__(self, game_state: GameState, game_log: GameLog, api_controller: APIController):
        self.game_state = game_state
        self.game_log = game_log
        self.api_controller = api_controller
        
        # 初始化阶段控制器
        self.night_controller = NightPhaseController(game_state, game_log, api_controller)
        self.day_controller = DayPhaseController(game_state, game_log, api_controller)
        
    def get_next_phase(self, current_phase: GamePhase) -> Optional[GamePhase]:
        """根据当前阶段和游戏状态获取下一个阶段"""
        # 游戏开始阶段
        if current_phase == GamePhase.INIT:
            return GamePhase.ROLE_ASSIGNMENT
        elif current_phase == GamePhase.ROLE_ASSIGNMENT:
            return GamePhase.NIGHT_START_0
            
        # 第0晚
        elif current_phase == GamePhase.NIGHT_START_0:
            return GamePhase.WEREWOLF_TURN_0
        elif current_phase == GamePhase.WEREWOLF_TURN_0:
            return GamePhase.SEER_TURN_0
        elif current_phase == GamePhase.SEER_TURN_0:
            return GamePhase.WITCH_TURN_0
        elif current_phase == GamePhase.WITCH_TURN_0:
            return GamePhase.NIGHT_END_0
        elif current_phase == GamePhase.NIGHT_END_0:
            return GamePhase.DAY_START
            
        # 白天阶段
        elif current_phase == GamePhase.DAY_START:
            return GamePhase.DEATH_REPORT
        elif current_phase == GamePhase.DEATH_REPORT:
            # 如果有玩家死亡且是猎人，进入猎人开枪阶段
            if self._has_hunter_died_this_round():
                return GamePhase.FIRST_HUNTER_SHOT
            return GamePhase.DISCUSSION
        elif current_phase == GamePhase.FIRST_HUNTER_SHOT:
            return GamePhase.DISCUSSION
        elif current_phase == GamePhase.DISCUSSION:
            return GamePhase.VOTE
        elif current_phase == GamePhase.VOTE:
            return GamePhase.EXILE
        elif current_phase == GamePhase.EXILE:
            # 如果放逐的是猎人，进入猎人开枪阶段
            if self._is_exiled_player_hunter():
                return GamePhase.EXILE_HUNTER_SHOT
            return GamePhase.DAY_END
        elif current_phase == GamePhase.EXILE_HUNTER_SHOT:
            return GamePhase.DAY_END
        elif current_phase == GamePhase.DAY_END:
            return GamePhase.NIGHT_START
            
        # 正常夜晚阶段
        elif current_phase == GamePhase.NIGHT_START:
            return GamePhase.WEREWOLF_TURN
        elif current_phase == GamePhase.WEREWOLF_TURN:
            return GamePhase.SEER_TURN
        elif current_phase == GamePhase.SEER_TURN:
            return GamePhase.WITCH_TURN
        elif current_phase == GamePhase.WITCH_TURN:
            return GamePhase.NIGHT_END
        elif current_phase == GamePhase.NIGHT_END:
            return GamePhase.DAY_START
            
        return None
    
    def next_phase(self) -> Optional[GamePhase]:
        """进入下一个阶段"""
        # 检查游戏是否结束
        game_over, winning_team = self.check_game_over()
        if game_over:
            self.game_state.current_phase = GamePhase.GAME_OVER
            return None
            
        # 获取下一个阶段
        next_phase = self.get_next_phase(self.game_state.current_phase)
        if next_phase:
            self.game_state.current_phase = next_phase
            
            # 只在新回合开始时记录事件
            if next_phase == GamePhase.NIGHT_START:
                self.game_log.add_event(GameEvent(
                    GameEventType.ROUND_START,
                    {
                        "round_number": self.game_state.round_number + 1  # +1 因为新回合还未开始
                    }
                ))
                # 开始新的回合
                self.game_state.start_new_round()
            
        return next_phase
    
    def _has_hunter_died_this_round(self) -> bool:
        """检查本回合是否有猎人死亡"""
        if not self.game_state.current_round:
            return False
            
        for death in self.game_state.current_round.deaths:
            if death["time"] == "night":  # 只检查夜晚死亡
                player = self.game_state.get_player_by_id(death["player_id"])
                if player and player.role.role_type == RoleType.HUNTER:
                    return True
        return False
    
    def _is_exiled_player_hunter(self) -> bool:
        """检查被放逐的玩家是否是猎人"""
        if not self.game_state.current_round:
            return False
            
        exiled_id = self.game_state.current_round.exiled_player
        if exiled_id:
            player = self.game_state.get_player_by_id(exiled_id)
            return player and player.role.role_type == RoleType.HUNTER
            
        return False
    
    async def execute_current_phase(self) -> None:
        """执行当前阶段"""
        current_phase = self.game_state.current_phase
        
        # 第0晚的特殊处理
        if current_phase in {
            GamePhase.NIGHT_START_0, 
            GamePhase.WEREWOLF_TURN_0,
            GamePhase.SEER_TURN_0, 
            GamePhase.WITCH_TURN_0,
            GamePhase.NIGHT_END_0
        }:
            await self.night_controller.execute()
            
        # 正常夜晚阶段
        elif current_phase in {
            GamePhase.NIGHT_START,
            GamePhase.WEREWOLF_TURN,
            GamePhase.SEER_TURN,
            GamePhase.WITCH_TURN,
            GamePhase.NIGHT_END
        }:
            await self.night_controller.execute()
            
        # 白天阶段
        elif current_phase in {
            GamePhase.DAY_START,
            GamePhase.DEATH_REPORT,
            GamePhase.FIRST_HUNTER_SHOT,
            GamePhase.DISCUSSION,
            GamePhase.VOTE,
            GamePhase.EXILE,
            GamePhase.EXILE_HUNTER_SHOT,
            GamePhase.DAY_END
        }:
            await self.day_controller.execute()
    
    def check_game_over(self) -> Tuple[bool, Optional[WinningTeam]]:
        """检查游戏是否结束"""
        alive_players = self.game_state.get_alive_players()
        werewolves = [p for p in alive_players if p.id in self.game_state._werewolves]
        villagers = [p for p in alive_players if p.id not in self.game_state._werewolves]
        
        # 狼人数量大于等于好人数量
        if len(werewolves) >= len(villagers):
            return True, WinningTeam.WEREWOLF
            
        # 狼人全部死亡
        if not werewolves:
            return True, WinningTeam.VILLAGER
            
        return False, None 