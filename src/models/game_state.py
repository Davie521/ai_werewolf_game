from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
from .player import Player
from .roles.base_role import RoleType

class GamePhase(Enum):
    # 游戏准备阶段
    INIT = "init"              
    ROLE_ASSIGNMENT = "role_assignment"  
    
    # 第0晚(特殊夜晚)
    NIGHT_START_0 = "night_start_0"    # 第0晚开始
    WEREWOLF_TURN_0 = "werewolf_0"     # 第0晚狼人行动
    SEER_TURN_0 = "seer_0"             # 第0晚预言家行动
    WITCH_TURN_0 = "witch_0"           # 第0晚女巫行动
    NIGHT_END_0 = "night_end_0"        # 第0晚结束
    
    # 白天阶段
    DAY_START = "day_start"        
    DEATH_REPORT = "death_report"  
    FIRST_HUNTER_SHOT = "first_hunter_shot"  # 死亡后的猎人开枪时机
    DISCUSSION = "discussion"      
    VOTE = "vote"                  
    EXILE = "exile"                
    EXILE_HUNTER_SHOT = "exile_hunter_shot"  # 放逐后的猎人开枪时机
    DAY_END = "day_end"           
    
    # 夜晚阶段
    NIGHT_START = "night_start"    
    WEREWOLF_TURN = "werewolf"     
    SEER_TURN = "seer"             
    WITCH_TURN = "witch"           
    NIGHT_END = "night_end"        
    
    # 游戏结束
    GAME_OVER = "game_over"        

class WinningTeam(Enum):
    WEREWOLF = "狼人阵营"
    VILLAGER = "好人阵营"
    NONE = "游戏未结束"

class NightAction:
    """夜晚行动记录"""
    def __init__(self):
        self.werewolf_kill: Optional[int] = None  
        self.witch_save: bool = False  
        self.witch_poison: Optional[int] = None  
        self.seer_check: Optional[Dict] = None  

class RoundRecord:
    """每回合的记录"""
    def __init__(self, round_number: int):
        self.round_number = round_number
        self.night_action = NightAction()
        self.day_votes: Dict[int, int] = {}  
        self.exiled_player: Optional[int] = None  
        self.hunter_shots: List[Dict[str, int]] = []  # [{time: str, hunter_id: int, target_id: int}]
        self.deaths: List[Dict] = []  # [{player_id: int, reason: str, time: str}]

class GameState:
    def __init__(self):
        # 基础游戏状态
        self.players: List[Player] = []
        self.current_phase: GamePhase = GamePhase.INIT
        self.round_number: int = 0
        
        # 角色状态
        self._witch_potions: Dict[int, Dict[str, bool]] = {}  # player_id -> {"save": bool, "poison": bool}
        self._checked_players: Dict[int, Set[int]] = {}  # 预言家ID -> 已查验的玩家ID集合
        self._werewolves: Set[int] = set()  # 狼人玩家ID集合
        
        # 回合记录
        self.round_records: List[RoundRecord] = []
        self.current_round: Optional[RoundRecord] = None
        self.is_first_night = True  # 是否是第0晚
        
        # 游戏结果
        self._game_over = False
        self._winning_team = WinningTeam.NONE
    
    def reset(self):
        """重置游戏状态"""
        self.__init__()
    
    def add_player(self, player: Player):
        """添加玩家并初始化其状态"""
        self.players.append(player)
        
        # 初始化角色状态
        if player.role.role_type == RoleType.SEER:
            self._checked_players[player.id] = set()
        elif player.role.role_type == RoleType.WITCH:
            self._witch_potions[player.id] = {"save": True, "poison": True}
        elif player.role.role_type == RoleType.WEREWOLF:
            self._werewolves.add(player.id)
    
    def start_new_round(self):
        """开始新的回合"""
        self.round_number += 1
        self.current_round = RoundRecord(self.round_number)
        self.round_records.append(self.current_round)
    
    def get_alive_players(self) -> List[Player]:
        """获取存活玩家列表"""
        return [p for p in self.players if p.is_alive]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        return next((p for p in self.players if p.id == player_id), None)
    
    def get_checked_players(self, seer_id: int) -> List[str]:
        """获取预言家已查验的玩家名单"""
        if seer_id not in self._checked_players:
            return []
        return [p.name for p in self.players if p.id in self._checked_players[seer_id]]
    
    def update_witch_potion(self, witch_id: int, potion_type: str, value: bool):
        """更新女巫药水状态
        
        Args:
            witch_id: 女巫ID
            potion_type: 药水类型 ("save" 或 "poison")
            value: 是否还有药水
        """
        if witch_id in self._witch_potions:
            self._witch_potions[witch_id][potion_type] = value
            
    def get_witch_potions(self, witch_id: int) -> Optional[Dict[str, bool]]:
        """获取女巫药水状态
        
        Args:
            witch_id: 女巫ID
            
        Returns:
            Dict[str, bool]: 药水状态字典，包含 "save" 和 "poison" 两个布尔值
        """
        return self._witch_potions.get(witch_id, {"save": False, "poison": False}).copy()
    
    def get_werewolf_teammates(self, werewolf_id: int) -> List[Player]:
        """获取其他狼人队友"""
        if werewolf_id not in self._werewolves:
            return []
        return [p for p in self.get_alive_players() 
                if p.id in self._werewolves and p.id != werewolf_id]
    
    def get_current_night_action(self) -> Optional[NightAction]:
        """获取当前回合的夜晚行动"""
        return self.current_round.night_action if self.current_round else None
    
    def get_round_record(self, round_number: int) -> Optional[RoundRecord]:
        """获取指定回合的记录"""
        if 0 <= round_number < len(self.round_records):
            return self.round_records[round_number]
        return None
    
    def record_night_action(self, action_type: str, details: Dict):
        """记录夜晚行动"""
        if not self.current_round:
            return
            
        if action_type == "werewolf_kill":
            self.current_round.night_action.werewolf_kill = details["target_id"]
        elif action_type == "witch_save":
            self.current_round.night_action.witch_save = True
        elif action_type == "witch_poison":
            self.current_round.night_action.witch_poison = details["target_id"]
        elif action_type == "seer_check":
            self.current_round.night_action.seer_check = {
                "target_id": details["target_id"],
                "is_werewolf": details["is_werewolf"]
            }
            
    def record_death(self, player_id: int, reason: str, time: str = "night"):
        """记录玩家死亡
        
        Args:
            player_id: 死亡玩家ID
            reason: 死亡原因
            time: 死亡时间点 ("night", "day_start", "exile")
        """
        if not self.current_round:
            return
        self.current_round.deaths.append({
            "player_id": player_id,
            "reason": reason,
            "time": time
        })
    
    def record_vote(self, voter_id: int, target_id: int):
        """记录投票"""
        if not self.current_round:
            return
        self.current_round.day_votes[voter_id] = target_id
    
    def record_exile(self, player_id: int):
        """记录放逐"""
        if not self.current_round:
            return
        self.current_round.exiled_player = player_id
    
    def record_hunter_shot(self, hunter_id: int, target_id: int, time: str):
        """记录猎人开枪
        
        Args:
            hunter_id: 猎人ID
            target_id: 目标ID
            time: 开枪时间点 ("day_start", "exile")
        """
        if not self.current_round:
            return
        self.current_round.hunter_shots.append({
            "hunter_id": hunter_id,
            "target_id": target_id,
            "time": time
        })
    
    def get_game_result(self) -> Dict:
        """获取游戏结果
        
        Returns:
            Dict: 包含胜利阵营和游戏回合数的字典
        """
        if not self._game_over:
            return {"winning_team": WinningTeam.NONE.value, "rounds": self.round_number}
            
        return {
            "winning_team": self._winning_team.value,
            "rounds": self.round_number
        }
    
    def get_last_night_dead_players(self) -> List[Dict]:
        """获取昨晚死亡的玩家列表
        
        Returns:
            List[Dict]: 死亡玩家列表，每个玩家包含 id、name、role 和 death_reason
        """
        if not self.current_round:
            return []
            
        dead_players = []
        for death in self.current_round.deaths:
            if death["time"] == "night":  # 只返回夜晚死亡的玩家
                player = self.get_player_by_id(death["player_id"])
                if player:
                    dead_players.append({
                        "id": player.id,
                        "name": player.name,
                        "role": player.role.role_type.value,
                        "death_reason": death["reason"]
                    })
        return dead_players
    
    def check_game_over(self) -> Tuple[bool, Optional[WinningTeam]]:
        """检查游戏是否结束
        
        Returns:
            Tuple[bool, Optional[WinningTeam]]: (是否结束, 获胜阵营)
        """
        # 获取存活玩家
        alive_players = self.get_alive_players()
        
        # 统计存活的狼人和好人
        alive_werewolves = sum(1 for p in alive_players if p.role.role_type == RoleType.WEREWOLF)
        alive_villagers = len(alive_players) - alive_werewolves
        
        # 判断游戏是否结束
        if alive_werewolves == 0:
            # 狼人全部死亡，好人胜利
            self._game_over = True
            self._winning_team = WinningTeam.VILLAGER
            return True, WinningTeam.VILLAGER
        elif alive_werewolves >= alive_villagers:
            # 狼人数量大于等于好人数量，狼人胜利
            self._game_over = True
            self._winning_team = WinningTeam.WEREWOLF
            return True, WinningTeam.WEREWOLF
            
        # 游戏继续
        return False, None
    
    def get_last_check_result(self, seer_id: int) -> Optional[Dict]:
        """获取预言家的最后一次查验结果
        
        Args:
            seer_id: 预言家ID
            
        Returns:
            Optional[Dict]: 最后一次查验结果，包含 target_id 和 is_werewolf，如果没有查验结果则返回 None
        """
        if not self.current_round:
            return None
            
        return self.current_round.night_action.seer_check
    