from .base_role import BaseRole, RoleType
from typing import Dict

class Witch(BaseRole):
    def __init__(self, role_type: RoleType = RoleType.WITCH):
        super().__init__(role_type)
        self.potions = {
            "save": True,    # 解药是否还在
            "poison": True   # 毒药是否还在
        }
        
    def use_potion(self, potion_type: str) -> bool:
        """使用药水
        
        Args:
            potion_type: "save" 或 "poison"
            
        Returns:
            bool: 是否使用成功
        """
        if potion_type in self.potions and self.potions[potion_type]:
            self.potions[potion_type] = False  # 使用后药水消失
            return True
        return False
        
    def has_potion(self, potion_type: str) -> bool:
        """检查是否还有指定的药水
        
        Args:
            potion_type: "save" 或 "poison"
            
        Returns:
            bool: 是否还有药水可用
        """
        return self.potions.get(potion_type, False)  # 检查药水是否还在 