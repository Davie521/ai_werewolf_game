from enum import Enum
from typing import Optional, Dict, Any

class RoleType(Enum):
    WEREWOLF = "狼人"
    VILLAGER = "平民"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"

class BaseRole:
    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.player_id: Optional[int] = None
        self.is_alive: bool = True
        self.death_reason: Optional[str] = None
        
    def set_player(self, player_id: int):
        self.player_id = player_id
        
    def die(self, reason: str):
        self.is_alive = False
        self.death_reason = reason
        
    @property
    def name(self) -> str:
        """返回角色名称"""
        return self.role_type.value

def create_role(role_type: RoleType) -> BaseRole:
    """创建角色实例
    
    Args:
        role_type: 角色类型枚举
        
    Returns:
        对应类型的角色实例
    """
    # 导入具体的角色类
    from .werewolf import Werewolf
    from .villager import Villager
    from .seer import Seer
    from .witch import Witch
    from .hunter import Hunter
    
    # 根据角色类型创建对应的实例
    role_classes = {
        RoleType.WEREWOLF: Werewolf,
        RoleType.VILLAGER: Villager,
        RoleType.SEER: Seer,
        RoleType.WITCH: Witch,
        RoleType.HUNTER: Hunter
    }
    
    role_class = role_classes.get(role_type)
    if not role_class:
        raise ValueError(f"未知的角色类型: {role_type}")
        
    return role_class(role_type) 