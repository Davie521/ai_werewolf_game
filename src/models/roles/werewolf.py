from .base_role import BaseRole, RoleType

class Werewolf(BaseRole):
    def __init__(self, role_type: RoleType = RoleType.WEREWOLF):
        super().__init__(role_type)
        self.has_voted = False
        
    def reset_vote(self):
        self.has_voted = False 