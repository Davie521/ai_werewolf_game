from enum import Enum
from typing import List, Dict, Any
from datetime import datetime

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
    
    def add_event(self, event: GameEvent):
        """添加游戏事件"""
        self._events.append(event)
    
    def get_all_events(self) -> List[Dict]:
        """获取所有事件（上帝视角）"""
        return [event.to_dict() for event in self._events]
    
    def format_event(self, event: Dict) -> str:
        """格式化事件为可读文本"""
        details = event.get('details', {})
        event_type = GameEventType(event.get('type'))
        
        # 游戏流程事件
        if event_type == GameEventType.GAME_START:
            return f"游戏开始！共有{details['player_count']}名玩家参与。\n玩家列表：{', '.join(p['name'] for p in details['players'])}"
        
        elif event_type == GameEventType.GAME_END:
            return f"游戏结束！{details['winning_team']}获胜，共进行了{details['rounds']}个回合。"
        
        elif event_type == GameEventType.ROUND_START:
            return f"第{details['round_number']}回合开始。"
        
        # 夜晚阶段事件
        elif event_type == GameEventType.NIGHT_START:
            return f"第{details['round_number']}个夜晚开始了。"
        
        elif event_type == GameEventType.NIGHT_ACTION:
            actions = []
            if details.get('werewolf_kill'):
                actions.append(f"狼人选择击杀了 {details['werewolf_kill']}")
            if details.get('witch_save'):
                actions.append(f"女巫使用了解药")
            if details.get('witch_poison'):
                actions.append(f"女巫使用了毒药")
            if details.get('seer_check'):
                actions.append(f"预言家查验了 {details['seer_check']['target']}")
            return "。".join(actions) + "。"
        
        elif event_type == GameEventType.NIGHT_END:
            return f"第{details['round_number']}个夜晚结束了。"
        
        # 白天阶段事件
        elif event_type == GameEventType.DAY_START:
            return f"第{details['round_number']}天开始了。"
        
        elif event_type == GameEventType.DEATH_ANNOUNCE:
            if not details.get("deaths"):
                return "昨晚是平安夜。"
            deaths = details["deaths"]
            messages = []
            for death in deaths:
                name = death.get("player_name", "某玩家")
                role = f"({death['role']})"
                reason = death.get("reason", "")
                messages.append(f"玩家 {name}{role} {reason}死亡")
            return "昨晚" + "，".join(messages) + "。"
        
        elif event_type == GameEventType.PLAYER_SPEAK:
            return f"{details['player_name']}: {details['message']}"
        
        elif event_type == GameEventType.VOTE_START:
            return "开始投票。"
        
        elif event_type == GameEventType.VOTE_RESULT:
            if details.get("is_tie"):
                return "投票结果为平票，没有玩家被放逐。"
            return f"投票结果：{details['voted_name']} ({details['role']}) 被放逐。"
        
        elif event_type == GameEventType.DAY_END:
            return f"第{details['round_number']}天结束了。"
        
        # 特殊事件
        elif event_type == GameEventType.HUNTER_SHOT:
            return f"猎人 {details['hunter_name']} 开枪带走了 {details['target_name']} ({details['target_role']})。"
        
        elif event_type == GameEventType.LAST_WORDS:
            return f"[遗言] {details['player_name']}: {details['message']}"
        
        return str(details) 