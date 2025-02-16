from typing import Optional
from .roles.base_role import BaseRole, RoleType

class Player:
    """玩家类，代表游戏中的一个玩家"""
    
    def __init__(self, player_id: int, name: str, role: BaseRole):
        """初始化玩家
        
        Args:
            player_id: 玩家ID
            name: 玩家名字
            role: 玩家的角色
        """
        self.id = player_id
        self.name = name
        self.role = role
        self.role.set_player(player_id)  # 设置角色的玩家ID
        self.is_alive = True
        self.death_reason: Optional[str] = None  # 可能的值：werewolf, poison, voted, hunter_shot
        self.has_last_words = False  # 是否已经发表遗言
        self.chat_history = []
    
    @property
    def role_type(self) -> RoleType:
        """获取玩家的角色类型"""
        return self.role.role_type
        
    def die(self, reason: str):
        """玩家死亡
        
        Args:
            reason: 死亡原因，可能的值：
                   - werewolf: 被狼人杀死
                   - poison: 被女巫毒死
                   - voted: 被投票放逐
                   - hunter_shot: 被猎人射杀
        """
        if not self.is_alive:  # 已经死亡的玩家不能再次死亡
            return
            
        self.is_alive = False
        self.death_reason = reason
        self.role.die(reason)  # 通知角色死亡
        
    def can_speak(self) -> bool:
        """检查玩家是否可以发言
        
        Returns:
            bool: 是否可以发言
        """
        # 活着的玩家总是可以发言
        if self.is_alive:
            return True
        # 死亡的玩家只有在未发表遗言时可以发言
        return not self.has_last_words
        
    def speak_last_words(self):
        """标记玩家已发表遗言"""
        if not self.is_alive and not self.has_last_words:
            self.has_last_words = True
        
    def to_dict(self) -> dict:
        """将玩家信息转换为字典格式
        
        Returns:
            dict: 玩家信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.name,
            "is_alive": self.is_alive,
            "death_reason": self.death_reason,
            "has_last_words": self.has_last_words
        }
    
    def add_chat(self, message: str):
        """添加聊天记录
        
        Args:
            message: 聊天消息
        """
        self.chat_history.append(message)
    
    def can_use_ability(self, ability_name: str) -> bool:
        """检查是否可以使用特定能力
        
        Args:
            ability_name: 能力名称
            
        Returns:
            bool: 是否可以使用该能力
        """
        # 死亡玩家不能使用能力
        if not self.is_alive:
            return False
        return self.role.abilities.get(ability_name, False)
    
    def __str__(self) -> str:
        """返回玩家的字符串表示"""
        return self.name
        
    def __repr__(self) -> str:
        """返回玩家的详细字符串表示"""
        return f"Player({self.id}, {self.name}, {self.role.name})" 