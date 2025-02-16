from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime

class GameEventType(Enum):
    GAME_START = "game_start"
    GAME_END = "game_end"
    PHASE_CHANGE = "phase_change"
    PLAYER_DEATH = "player_death"
    WEREWOLF_KILL = "werewolf_kill"
    WITCH_SAVE = "witch_save"
    WITCH_POISON = "witch_poison"
    SEER_CHECK = "seer_check"
    HUNTER_SHOT = "hunter_shot"
    PLAYER_VOTE = "player_vote"
    VOTE_RESULT = "vote_result"
    PLAYER_SPEAK = "player_speak"

class GameEvent:
    def __init__(self, event_type: GameEventType, details: Dict, public: bool = True):
        self.event_type = event_type
        self.details = details
        self.timestamp = datetime.now()
        self.public = public  # 是否是公开信息
    
    def to_dict(self) -> Dict:
        return {
            "type": self.event_type.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "public": self.public
        }

class GameLog:
    def __init__(self):
        self._events: List[GameEvent] = []
    
    def add_event(self, event: GameEvent):
        """添加游戏事件"""
        self._events.append(event)
    
    def get_public_events(self, start_index: int = 0) -> List[Dict]:
        """获取公开事件列表"""
        return [event.to_dict() for event in self._events[start_index:] if event.public]
    
    def get_player_events(self, player_id: int, start_index: int = 0) -> List[Dict]:
        """获取指定玩家可见的事件列表"""
        player_events = []
        print(f"[DEBUG] 获取玩家 {player_id} 的事件，总事件数: {len(self._events)}")
        for event in self._events[start_index:]:
            print(f"[DEBUG] 检查事件: type={event.event_type.value}, public={event.public}, details={event.details}")
            if event.public:
                player_events.append(event.to_dict())
            elif "player_id" in event.details and event.details["player_id"] == player_id:
                print(f"[DEBUG] 添加私密事件给玩家 {player_id}")
                player_events.append(event.to_dict())
        print(f"[DEBUG] 玩家 {player_id} 可见事件数: {len(player_events)}")
        return player_events
    
    def get_all_events(self) -> List[Dict]:
        """获取所有事件（仅用于调试）"""
        return [event.to_dict() for event in self._events]
    
    def format_event(self, event: Dict) -> str:
        """格式化事件为可读文本"""
        # 如果传入的是字典，直接使用，否则尝试获取事件的详情
        details = event.get('details') if isinstance(event, dict) else event.details
        event_type = GameEventType(event.get('type')) if isinstance(event, dict) else event.event_type
        
        if event_type == GameEventType.GAME_START:
            return f"游戏开始！共有{details['player_count']}名玩家参与。"
            
        elif event_type == GameEventType.GAME_END:
            return f"游戏结束！{details['winning_team']}阵营获胜，共进行了{details['rounds']}个回合。"
            
        elif event_type == GameEventType.PHASE_CHANGE:
            phase_names = {
                "night": "夜晚",
                "day": "白天",
                "vote": "投票"
            }
            return f"进入{phase_names[details['phase']]}阶段。"
            
        elif event_type == GameEventType.PLAYER_DEATH:
            if details.get("message"):  # 处理平安夜消息
                return details["message"]
            elif details.get("player_name"):  # 处理玩家死亡
                if details.get("role_revealed", False):
                    return f"玩家 {details['player_name']}({details['role']}) 死亡。"
                else:
                    return f"玩家 {details['player_name']} 死亡。"
            return "有玩家死亡。"  # 默认消息
            
        elif event_type == GameEventType.WEREWOLF_KILL:
            if details.get("message"):
                return details["message"]
            if details.get("target_name"):
                return f"狼人选择击杀 {details['target_name']}。"
            return "狼人选择了他们的目标。"
            
        elif event_type == GameEventType.WITCH_SAVE:
            if details.get("message"):
                return details["message"]
            if details.get("saved"):
                if details.get("target_name"):
                    return f"女巫使用解药救活了 {details['target_name']}。"
                return "女巫使用了解药。"
            return "女巫没有使用解药。"
            
        elif event_type == GameEventType.WITCH_POISON:
            if details.get("message"):
                return details["message"]
            if details.get("used"):
                if details.get("target_name"):
                    return f"女巫使用毒药毒死了 {details['target_name']}。"
                return "女巫使用了毒药。"
            return "女巫没有使用毒药。"
            
        elif event_type == GameEventType.SEER_CHECK:
            if details.get("message"):
                return details["message"]  # 直接返回消息
            if details.get("target_name"):
                if "role" in details:  # 如果包含角色信息（预言家专属）
                    return f"预言家查验了 {details['target_name']}，Ta是{details['role']}"
                return f"预言家查验了 {details['target_name']}"  # 公开信息
            return "预言家查验了一名玩家"
            
        elif event_type == GameEventType.HUNTER_SHOT:
            if details.get("message"):
                return details["message"]
            return f"猎人 {details['hunter_name']} 开枪带走了 {details['target_name']}。"
            
        elif event_type == GameEventType.PLAYER_VOTE:
            if details.get("message"):
                return details["message"]
            return f"{details['voter_name']} 投票给了 {details['target_name']}。"
            
        elif event_type == GameEventType.VOTE_RESULT:
            if details.get("is_tie"):
                return "投票结果为平票，没有玩家被放逐。"
            else:
                return f"投票结果：{details['voted_name']} 被放逐。"
            
        elif event_type == GameEventType.PLAYER_SPEAK:
            if details.get("is_last_words", False):
                return f"[遗言] {details['player_name']}: {details['message']}"
            return f"{details['player_name']}: {details['message']}"
            
        return str(details)  # 默认返回详情的字符串形式 