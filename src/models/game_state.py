from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
from .player import Player
from .role import RoleType

class GamePhase(Enum):
    NIGHT = "night"
    DAY = "day"
    VOTE = "vote"
    GAME_OVER = "game_over"

class WinningTeam(Enum):
    VILLAGERS = "villagers"
    WEREWOLVES = "werewolves"
    NONE = "none"

class GameState:
    def __init__(self):
        self.players: List[Player] = []
        self.current_phase = GamePhase.NIGHT
        self.round_number = 0
        self.votes: Dict[int, int] = {}  # voter_id -> target_id
        self._night_actions: Dict[str, Dict] = {}  # role -> action details
        
        # 特殊状态记录
        self._checked_players: Dict[int, Set[int]] = {}  # 预言家ID -> 已查验的玩家ID集合
        self._check_results: Dict[int, Dict] = {}  # 预言家ID -> 查验结果
        self._witch_potions: Dict[int, Dict[str, bool]] = {}  # 女巫ID -> 药水状态
        self._last_night_killed: Optional[int] = None  # 昨晚被狼人杀害的玩家ID
        self._last_night_saved: bool = False  # 昨晚是否被女巫救活
        self._last_night_poisoned: Optional[int] = None  # 昨晚被女巫毒死的玩家ID
        self._hunter_shot_target: Optional[int] = None  # 猎人开枪带走的玩家ID
        self._werewolves: Set[int] = set()  # 狼人玩家ID集合
        self._game_over = False  # 游戏是否结束
        self._winning_team = WinningTeam.NONE  # 获胜阵营
    
    def reset(self):
        """重置游戏状态"""
        self.players = []
        self.current_phase = GamePhase.NIGHT
        self.round_number = 0
        self.votes = {}
        self._night_actions = {}
        self._checked_players = {}
        self._check_results = {}  # 重置查验结果
        self._witch_potions = {}
        self._last_night_killed = None
        self._last_night_saved = False
        self._last_night_poisoned = None
        self._hunter_shot_target = None
        self._werewolves = set()
        self._game_over = False
        self._winning_team = WinningTeam.NONE
    
    def add_player(self, player: Player):
        """添加玩家到游戏"""
        # 重置玩家状态
        player.is_alive = True
        player.death_reason = None
        player.chat_history = []
        
        # 添加玩家
        self.players.append(player)
        
        # 初始化特殊角色的状态记录
        if player.role.role_type == RoleType.SEER:
            self._checked_players[player.id] = set()
        elif player.role.role_type == RoleType.WITCH:
            self._witch_potions[player.id] = {"save": True, "poison": True}
            player.role.has_antidote = True
            player.role.has_poison = True
        elif player.role.role_type == RoleType.WEREWOLF:
            self._werewolves.add(player.id)
    
    def get_alive_players(self) -> List[Player]:
        """获取存活玩家列表"""
        return [p for p in self.players if p.is_alive]
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        return next((p for p in self.players if p.id == player_id), None)
    
    def get_checked_players(self, seer_id: int) -> List[str]:
        """获取预言家已查验的玩家名单（仅对应预言家可见）"""
        if seer_id not in self._checked_players:
            return []
        return [p.name for p in self.players if p.id in self._checked_players[seer_id]]
    
    def get_killed_player(self, witch_id: int) -> Optional[Player]:
        """获取当晚被狼人杀害的玩家（仅女巫可见）"""
        if self.current_phase != GamePhase.NIGHT or "werewolf_kill" not in self._night_actions:
            return None
        # 确保是女巫在查看
        witch = self.get_player_by_id(witch_id)
        if not witch or witch.role.role_type != RoleType.WITCH:
            return None
        target_id = self._night_actions["werewolf_kill"]["target_id"]
        return self.get_player_by_id(target_id)
    
    def get_witch_potions(self, witch_id: int) -> Optional[Dict[str, bool]]:
        """获取女巫药水状态（仅对应女巫可见）"""
        return self._witch_potions.get(witch_id, {"save": False, "poison": False}).copy()
    
    def get_last_night_dead_players(self) -> List[Player]:
        """获取昨晚死亡的玩家列表（所有人可见）"""
        dead_players = []
        if self._last_night_killed and not self._last_night_saved:
            killed_player = self.get_player_by_id(self._last_night_killed)
            if killed_player:
                dead_players.append(killed_player)
        if self._last_night_poisoned:
            poisoned_player = self.get_player_by_id(self._last_night_poisoned)
            if poisoned_player:
                dead_players.append(poisoned_player)
        return dead_players
    
    def get_last_check_result(self, seer_id: int) -> Optional[Dict]:
        """获取预言家的最后一次查验结果（仅对应预言家可见）"""
        if seer_id not in self._checked_players:
            return None
        if "seer_check" not in self._night_actions:
            return None
            
        target_id = self._night_actions["seer_check"]["target_id"]
        target = self.get_player_by_id(target_id)
        if target:
            return {
                "player": target,
                "role": "狼人" if target.role.role_type == RoleType.WEREWOLF else "好人"
            }
        return None
    
    def get_werewolf_teammates(self, werewolf_id: int) -> List[Player]:
        """获取其他狼人队友（仅对应狼人可见）"""
        if werewolf_id not in self._werewolves:
            return []
        return [p for p in self.get_alive_players() 
                if p.id in self._werewolves and p.id != werewolf_id]
    
    def record_night_action(self, action_type: str, details: Dict):
        """记录夜晚行动"""
        self._night_actions[action_type] = details
    
    def process_night_actions(self):
        """处理所有夜晚行动"""
        # 记录狼人击杀
        if "werewolf_kill" in self._night_actions:
            self._last_night_killed = self._night_actions["werewolf_kill"]["target_id"]
        
        # 记录预言家查验
        if "seer_check" in self._night_actions:
            seer_id = next((p.id for p in self.players if p.role.role_type == RoleType.SEER), None)
            if seer_id:
                self._checked_players[seer_id].add(self._night_actions["seer_check"]["target_id"])
        
        # 处理女巫行动
        if "witch_save" in self._night_actions:
            witch_id = next((p.id for p in self.players if p.role.role_type == RoleType.WITCH), None)
            if witch_id and self._night_actions["witch_save"]["used"]:
                self._last_night_saved = True
                self._witch_potions[witch_id]["save"] = False
        
        if "witch_poison" in self._night_actions:
            witch_id = next((p.id for p in self.players if p.role.role_type == RoleType.WITCH), None)
            target_id = self._night_actions["witch_poison"]["target_id"]
            if witch_id and target_id is not None:
                self._last_night_poisoned = target_id
                self._witch_potions[witch_id]["poison"] = False
        
        # 清空夜晚行动记录
        self._night_actions = {}
    
    def record_vote(self, voter_id: int, target_id: int):
        """记录投票"""
        self.votes[voter_id] = target_id
    
    def process_hunter_shot(self, hunter_id: int, target_id: int) -> bool:
        """处理猎人开枪带人
        
        Args:
            hunter_id: 猎人ID
            target_id: 目标玩家ID
            
        Returns:
            bool: 是否成功处理猎人开枪
        """
        hunter = self.get_player_by_id(hunter_id)
        target = self.get_player_by_id(target_id)
        
        # 验证猎人身份和状态
        if not hunter or hunter.role.role_type != RoleType.HUNTER:
            return False
        if hunter.is_alive:  # 猎人必须是刚死亡的状态
            return False
        if self._hunter_shot_target is not None:  # 已经开过枪了
            return False
            
        # 验证目标是否有效
        if not target or not target.is_alive:
            return False
            
        # 记录并执行猎人开枪
        self._hunter_shot_target = target_id
        target.is_alive = False  # 直接标记目标死亡
        return True
    
    def process_vote(self) -> Tuple[Optional[Player], bool]:
        """处理投票结果
        
        Returns:
            Tuple[Optional[Player], bool]: (被投出的玩家，是否平票)
        """
        if not self.votes:
            return None, False
            
        # 统计投票
        vote_count: Dict[int, int] = {}
        for target_id in self.votes.values():
            vote_count[target_id] = vote_count.get(target_id, 0) + 1
            
        # 找出票数最多的玩家
        max_votes = max(vote_count.values())
        most_voted = [pid for pid, count in vote_count.items() if count == max_votes]
        
        # 如果有平票
        if len(most_voted) > 1:
            return None, True
            
        voted_player = self.get_player_by_id(most_voted[0])
        if voted_player:
            voted_player.kill()
            # 如果是猎人被投出，给他开枪的机会
            if voted_player.role.role_type == RoleType.HUNTER:
                return voted_player, False
                
        return voted_player, False
    
    def check_game_over(self) -> Tuple[bool, Optional[WinningTeam]]:
        """检查游戏是否结束，并返回获胜阵营
        
        Returns:
            Tuple[bool, Optional[WinningTeam]]: (游戏是否结束，获胜阵营)
        """
        if self._game_over:
            return True, self._winning_team
            
        alive_players = self.get_alive_players()
        werewolves = [p for p in alive_players if p.id in self._werewolves]
        villagers = [p for p in alive_players if p.id not in self._werewolves]
        
        # 狼人数量大于等于好人数量
        if len(werewolves) >= len(villagers):
            self._game_over = True
            self._winning_team = WinningTeam.WEREWOLVES
            return True, WinningTeam.WEREWOLVES
            
        # 狼人全部死亡
        if len(werewolves) == 0:
            self._game_over = True
            self._winning_team = WinningTeam.VILLAGERS
            return True, WinningTeam.VILLAGERS
            
        return False, None
    
    def get_game_result(self) -> Dict:
        """获取游戏结果（仅在游戏结束时有效）
        
        Returns:
            Dict: 包含游戏结果的详细信息
        """
        if not self._game_over:
            return {
                "game_over": False,
                "winning_team": None,
                "rounds": self.round_number
            }
            
        alive_players = self.get_alive_players()
        dead_players = [p for p in self.players if not p.is_alive]
        
        return {
            "game_over": True,
            "winning_team": self._winning_team.value,
            "rounds": self.round_number,
            "alive_players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "role": p.role.role_type.value
                } for p in alive_players
            ],
            "dead_players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "role": p.role.role_type.value
                } for p in dead_players
            ]
        }
    
    def next_phase(self):
        """进入下一个游戏阶段"""
        # 检查游戏是否结束
        game_over, _ = self.check_game_over()
        if game_over:
            self.current_phase = GamePhase.GAME_OVER
            return
            
        if self.current_phase == GamePhase.NIGHT:
            self.process_night_actions()
            self.current_phase = GamePhase.DAY
        elif self.current_phase == GamePhase.DAY:
            self.current_phase = GamePhase.VOTE
        elif self.current_phase == GamePhase.VOTE:
            # 处理投票结果
            voted_player, is_tie = self.process_vote()
            if is_tie:
                # 如果平票，直接进入下一晚
                self.current_phase = GamePhase.NIGHT
                self.round_number += 1
            else:
                # 如果有人被投出，检查是否游戏结束
                game_over, _ = self.check_game_over()
                if game_over:
                    self.current_phase = GamePhase.GAME_OVER
                else:
                    self.current_phase = GamePhase.NIGHT
                    self.round_number += 1
            
            # 重置状态
            self.votes = {}
            self._last_night_killed = None
            self._last_night_saved = False
            self._last_night_poisoned = None
            self._hunter_shot_target = None
    
    def mark_player_as_killed(self, player_id: int):
        """标记玩家为被狼人杀害状态
        
        Args:
            player_id: 被杀害玩家的ID
        """
        self._last_night_killed = player_id 