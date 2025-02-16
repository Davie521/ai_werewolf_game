from .base_role import BaseRole, RoleType

class Villager(BaseRole):
    def __init__(self, role_type: RoleType = RoleType.VILLAGER):
        super().__init__(role_type)
        self.abilities = {} 