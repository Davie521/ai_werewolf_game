from enum import Enum

class RoleType(Enum):
    VILLAGER = "村民"
    WEREWOLF = "狼人"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"

class Role:
    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.abilities = self._init_abilities(role_type)
        # 初始化药水状态
        self.has_antidote = False
        self.has_poison = False
        if role_type == RoleType.WITCH:
            self.has_antidote = True
            self.has_poison = True
    
    def _init_abilities(self, role_type: RoleType) -> dict:
        abilities = {
            RoleType.VILLAGER: {},
            RoleType.WEREWOLF: {"kill": True},
            RoleType.SEER: {"check": True},
            RoleType.WITCH: {
                "save_potion": True,
                "poison_potion": True
            },
            RoleType.HUNTER: {"shoot": True}
        }
        return abilities.get(role_type, {}) 