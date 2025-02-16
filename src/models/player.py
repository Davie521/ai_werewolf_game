from .role import Role, RoleType

class Player:
    def __init__(self, player_id: int, name: str, role: Role):
        self.id = player_id
        self.name = name
        self.role = role
        self.is_alive = True
        self.death_reason = None  # 可能的值：werewolf, poison, voted, hunter_shot
        self.chat_history = []
    
    def add_chat(self, message: str):
        self.chat_history.append(message)
    
    def kill(self, reason: str = None):
        self.is_alive = False
        self.death_reason = reason
    
    def can_use_ability(self, ability_name: str) -> bool:
        return self.role.abilities.get(ability_name, False) 