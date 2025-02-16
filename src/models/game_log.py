from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

class GameEventType(Enum):
    # 游戏流程事件
    GAME_START = "game_start"
    GAME_END = "game_end"
    ROUND_START = "round_start"
    
    # 夜晚阶段事件
    NIGHT_START = "night_start"
    NIGHT_ACTION = "night_action"  # 统一记录夜晚行动
    NIGHT_END = "night_end"
    
    # 白天阶段事件
    DAY_START = "day_start"
    DEATH_ANNOUNCE = "death_announce"
    PLAYER_SPEAK = "player_speak"
    VOTE_START = "vote_start"
    VOTE_RESULT = "vote_result"
    DAY_END = "day_end"
    
    # 特殊事件
    HUNTER_SHOT = "hunter_shot"
    LAST_WORDS = "last_words"

class GameEvent:
    def __init__(self, event_type: GameEventType, details: Dict[str, Any], public: bool = True, visible_to: List[int] = None):
        self.event_type = event_type
        self.details = details
        self.timestamp = datetime.now()
        self.public = public
        self.visible_to = visible_to or []
    
    def to_dict(self) -> Dict:
        return {
            "type": self.event_type.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "public": self.public,
            "visible_to": self.visible_to
        }

class GameLog:
    def __init__(self):
        self._events: List[GameEvent] = []
        self._output_file = None
        self._log_dir = None
        
    def initialize(self, log_dir: str):
        """初始化日志系统
        
        Args:
            log_dir: 日志文件目录
        """
        self._log_dir = os.path.abspath(log_dir)
        os.makedirs(self._log_dir, exist_ok=True)
        
        # 创建新的日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(self._log_dir, f"game_log_{timestamp}.txt")
        self._output_file = open(log_path, "w", encoding="utf-8")
    
    def add_event(self, event: GameEvent):
        """添加游戏事件并写入日志"""
        self._events.append(event)
        self._write_event(event)
    
    def get_all_events(self) -> List[Dict]:
        """获取所有事件（上帝视角）"""
        return [event.to_dict() for event in self._events]
    
    def format_event(self, event: Dict) -> str:
        """格式化事件为可读文本"""
        details = event.get('details', {})
        event_type = GameEventType(event.get('type'))
        
        # 游戏流程事件
        if event_type == GameEventType.GAME_START:
            players_str = ", ".join([f"{p['name']} ({p['role']})" for p in details.get('players', [])])
            return f"游戏开始！共有{details.get('player_count', 0)}名玩家参与。\n玩家列表：{players_str}"
        
        elif event_type == GameEventType.GAME_END:
            return f"游戏结束！{details.get('winning_team', '')}获胜，共进行了{details.get('rounds', 0)}个回合。"
        
        elif event_type == GameEventType.ROUND_START:
            return f"第{details.get('round_number', 0)}回合开始。"
        
        # 夜晚阶段事件
        elif event_type == GameEventType.NIGHT_START:
            return f"第{details.get('round_number', 0)}个夜晚开始了。"
        
        elif event_type == GameEventType.NIGHT_ACTION:
            actions = []
            if details.get('werewolf_kill'):
                actions.append(f"狼人选择击杀了{details['werewolf_kill']}")
            if details.get('witch_save'):
                actions.append("女巫使用了解药")
            if details.get('witch_poison'):
                actions.append(f"女巫使用了毒药")
            if details.get('seer_check'):
                target = details['seer_check'].get('target', '')
                result = "是" if details['seer_check'].get('is_werewolf') else "不是"
                actions.append(f"预言家查验了{target}，发现他{result}狼人")
            return "。".join(actions) + "。" if actions else "这是一个平静的夜晚。"
        
        elif event_type == GameEventType.NIGHT_END:
            return f"第{details.get('round_number', 0)}个夜晚结束了。"
        
        # 白天阶段事件
        elif event_type == GameEventType.DAY_START:
            return f"第{details.get('round_number', 0)}天开始了。"
        
        elif event_type == GameEventType.DEATH_ANNOUNCE:
            deaths = details.get("deaths", [])
            if not deaths:
                return "昨晚是平安夜。"
            
            death_reasons = {
                "werewolf": "被狼人杀死",
                "poison": "被女巫毒死",
                "voted": "被投票处决",
                "hunter_shot": "被猎人射杀"
            }
            
            messages = []
            for death in deaths:
                name = death.get("player_name", "某玩家")
                role = f"({death.get('role', '')})"
                reason = death_reasons.get(death.get("reason", ""), death.get("reason", ""))
                messages.append(f"{name}{role}{reason}")
            return "昨晚" + "，".join(messages) + "。"
        
        elif event_type == GameEventType.PLAYER_SPEAK:
            return f"{details.get('player_name', '')}: {details.get('message', '')}"
        
        elif event_type == GameEventType.VOTE_START:
            return "开始投票。"
        
        elif event_type == GameEventType.VOTE_RESULT:
            if details.get("is_tie"):
                return "投票结果为平票，没有玩家被放逐。"
            voted_name = details.get('voted_name', '某玩家')
            role = details.get('role', '')
            return f"投票结果：{voted_name} ({role}) 被放逐。"
        
        elif event_type == GameEventType.DAY_END:
            return f"第{details.get('round_number', 0)}天结束了。"
        
        # 特殊事件
        elif event_type == GameEventType.HUNTER_SHOT:
            hunter_name = details.get('hunter_name', '猎人')
            if "target_name" in details:
                target_name = details.get('target_name', '某玩家')
                target_role = details.get('target_role', '')
                return f"猎人{hunter_name}开枪带走了{target_name} ({target_role})。"
            return f"猎人{hunter_name}可以开枪。"
        
        elif event_type == GameEventType.LAST_WORDS:
            return f"[遗言] {details.get('player_name', '')}: {details.get('message', '')}"
        
        return str(details)  # 如果没有匹配的事件类型，返回原始详情
        
    def write_phase_header(self, phase_name: str):
        """写入阶段标题
        
        Args:
            phase_name: 阶段名称
        """
        if self._output_file:
            self._output_file.write(f"\n=== {phase_name} ===\n")
            self._output_file.flush()
            
    def write_game_summary(self, alive_players: List[Dict], dead_players: List[Dict]):
        """写入游戏总结
        
        Args:
            alive_players: 存活玩家列表，每个玩家包含 name 和 role
            dead_players: 死亡玩家列表，每个玩家包含 name、role 和 death_reason
        """
        if not self._output_file:
            return
            
        self._output_file.write("\n存活玩家：\n")
        for player in alive_players:
            self._output_file.write(f"{player['name']} ({player['role']})\n")
            
        self._output_file.write("\n死亡玩家：\n")
        death_reasons = {
            "werewolf": "被狼人杀死",
            "poison": "被女巫毒死",
            "voted": "被投票处决",
            "hunter_shot": "被猎人射杀"
        }
        for player in dead_players:
            reason = death_reasons.get(player['death_reason'], player['death_reason'])
            self._output_file.write(f"{player['name']} ({player['role']}) - 死因: {reason}\n")
        self._output_file.flush()
    
    def _write_event(self, event: GameEvent):
        """写入单个事件到日志文件"""
        if not self._output_file:
            return
            
        formatted = self.format_event(event.to_dict())
        if formatted:
            self._output_file.write(formatted + "\n")
            self._output_file.flush()
    
    def close(self):
        """关闭日志文件"""
        if self._output_file:
            self._output_file.close()
            self._output_file = None

    def write_to_log(self, message: str):
        """直接写入消息到日志文件
        
        Args:
            message: 要写入的消息
        """
        if self._output_file:
            self._output_file.write(message + "\n")
            self._output_file.flush() 