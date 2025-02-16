from typing import List, Optional
from ..models.game_state import GameState, GamePhase
from ..models.game_log import GameLog, GameEvent, GameEventType
from .api_controller import APIController
from .game_phase_manager import GamePhaseManager
from datetime import datetime
from ..models.roles.base_role import RoleType
from ..models.player import Player
import os

class GameController:
    def __init__(self, game_state: Optional[GameState] = None, api_controller: Optional[APIController] = None):
        self.game_state = game_state or GameState()
        self.game_log = GameLog()
        self.api_controller = api_controller or APIController()
        self.phase_manager = GamePhaseManager(self.game_state, self.game_log, self.api_controller)
        self.game_output_file = None
        
        # 设置日志目录
        self.log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'game_logs'))
        self.game_log.initialize(self.log_dir)
        
    async def initialize_game(self, player_names: List[str], preset_players: List[Player] = None):
        """初始化游戏
        - 分配角色
        - 创建日志
        - 记录初始状态
        
        Args:
            player_names: 玩家名字列表
            preset_players: 预设的玩家列表（用于测试）
        """
        # 重置游戏状态
        self.game_state.reset()
        
        # 创建游戏日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"game_log_{timestamp}.txt")
        self.game_output_file = open(log_file, "w", encoding="utf-8")
        
        if preset_players:
            # 使用预设的玩家列表
            for player in preset_players:
                self.game_state.add_player(player)
        else:
            # 分配角色
            roles = self._generate_roles(len(player_names))
            for i, name in enumerate(player_names):
                player = self._create_player(i + 1, name, roles[i])
                self.game_state.add_player(player)
            
        # 记录游戏开始事件
        self._log_game_start(player_names)
        
        # 不再在初始化时创建第一个回合
        # self.game_state.start_new_round()
        
    async def run_game(self):
        """运行游戏主循环"""
        while True:
            # 执行当前阶段
            await self.phase_manager.execute_current_phase()
            
            # 写入当前阶段的事件到日志文件
            self.game_log.write_phase_header(self.game_state.current_phase.value)
            
            # 进入下一阶段
            next_phase = self.phase_manager.next_phase()
            if not next_phase:  # 游戏结束
                self._log_game_end()
                break
                
    async def next_phase(self):
        """执行下一个游戏阶段"""
        # 执行当前阶段
        await self.phase_manager.execute_current_phase()
        
        # 写入当前阶段的事件到日志文件
        self.game_log.write_phase_header(self.game_state.current_phase.value)
        
        # 检查游戏是否结束
        game_over, _ = self.game_state.check_game_over()
        if game_over:
            self._log_game_end()
            return True
            
        # 进入下一阶段
        next_phase = self.phase_manager.next_phase()
        if not next_phase:  # 游戏结束
            self._log_game_end()
            return True
            
        # 如果进入第0晚，创建第一个回合
        if next_phase == GamePhase.NIGHT_START_0 and self.game_state.current_round is None:
            self.game_state.start_new_round()
            
        return False

    def get_player_events(self, player_id: int) -> List[str]:
        """获取指定玩家可见的事件"""
        events = [event for event in self.game_log.get_all_events() 
                 if event['public'] or player_id in event.get('visible_to', [])]
        return [self.game_log.format_event(event) for event in events]
        
    def get_public_events(self, limit: int = -1) -> List[str]:
        """获取公开事件
        
        Args:
            limit: 返回的最大事件数量，-1 表示返回所有事件
            
        Returns:
            List[str]: 格式化的公开事件列表
        """
        events = [event for event in self.game_log.get_all_events() if event['public']]
        if limit > 0:
            events = events[-limit:]  # 只返回最近的 N 个事件
        return [self.game_log.format_event(event) for event in events]
                
    def _log_game_start(self, player_names: List[str]):
        """记录游戏开始"""
        self.game_log.write_phase_header("游戏开始")
        
        # 记录玩家和角色信息
        players_info = []
        for player in self.game_state.players:
            players_info.append({
                "id": player.id,
                "name": player.name,
                "role": player.role.name
            })
        
        self.game_log.add_event(GameEvent(
            GameEventType.GAME_START,
            {
                "player_count": len(player_names),
                "players": players_info
            }
        ))
        
        # 记录每个玩家的角色（上帝视角）
        self.game_log.write_phase_header("玩家角色")
        for player in self.game_state.players:
            self.game_log.write_to_log(f"{player.name}: {player.role.name}")
        self.game_log.write_to_log("")  # 添加空行分隔
        
    def _log_game_end(self):
        """记录游戏结束"""
        result = self.game_state.get_game_result()
        self.game_log.write_phase_header("游戏结束")
        self.game_log.add_event(GameEvent(
            GameEventType.GAME_END,
            result
        ))
        
        # 写入游戏总结
        alive_players = [
            {"name": p.name, "role": p.role.role_type.value}
            for p in self.game_state.get_alive_players()
        ]
        dead_players = [
            {
                "name": p.name,
                "role": p.role.role_type.value,
                "death_reason": p.death_reason
            }
            for p in self.game_state.players if not p.is_alive
        ]
        self.game_log.write_game_summary(alive_players, dead_players)
        self.game_log.close()
            
    def cleanup(self):
        """清理资源"""
        if self.game_output_file:
            self.game_output_file.close()
            self.game_output_file = None
        self.game_log.close()
            
    def _generate_roles(self, player_count: int) -> List[RoleType]:
        """根据玩家数量生成角色列表
        固定生成:
        - 3个狼人
        - 3个平民
        - 1个预言家
        - 1个女巫
        - 1个猎人
        """
        if player_count != 9:
            raise ValueError("当前游戏必须为9名玩家")
            
        roles = []
        # 特殊角色
        roles.extend([RoleType.WEREWOLF] * 3)  # 3个狼人
        roles.append(RoleType.SEER)  # 预言家
        roles.append(RoleType.WITCH)  # 女巫
        roles.append(RoleType.HUNTER)  # 猎人
        roles.extend([RoleType.VILLAGER] * 3)  # 3个平民
        
        # 随机打乱角色顺序
        import random
        random.shuffle(roles)
        return roles
        
    def _create_player(self, player_id: int, name: str, role_type: RoleType) -> 'Player':
        """创建玩家对象"""
        from ..models.player import Player
        from ..models.roles.base_role import create_role
        
        role = create_role(role_type)  # 直接传递RoleType枚举
        return Player(player_id, name, role) 
        
    def write_to_log(self, message: str):
        """写入消息到日志文件
        
        Args:
            message: 要写入的消息
        """
        if self.game_output_file:
            self.game_output_file.write(message + "\n")
            self.game_output_file.flush()
        