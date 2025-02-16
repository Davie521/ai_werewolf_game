from .base_role import BaseRole, RoleType

class Hunter(BaseRole):
    def __init__(self, role_type: RoleType = RoleType.HUNTER):
        super().__init__(role_type)
        self.has_shot = False
        self.can_shoot = True  # 是否有开枪能力(被毒死时失去能力)
        
    def shoot(self) -> bool:
        """尝试开枪
        
        Returns:
            bool: 是否开枪成功
        """
        if self.can_shoot and not self.has_shot:
            self.has_shot = True
            return True
        return False
        
    def die(self, reason: str):
        """重写死亡方法,处理被毒死的情况"""
        super().die(reason)
        if reason == "poison":
            self.can_shoot = False 