from .base_role import BaseRole, RoleType

class Seer(BaseRole):
    def __init__(self, role_type: RoleType = RoleType.SEER):
        super().__init__(role_type)
        self.checked_players = set()  # 记录已经查验过的玩家ID
        
    def record_check(self, player_id: int):
        """记录已查验的玩家"""
        self.checked_players.add(player_id)
        
    def has_checked(self, player_id: int) -> bool:
        """检查玩家是否已被查验"""
        return player_id in self.checked_players 