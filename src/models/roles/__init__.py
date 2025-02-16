"""
Roles package initialization.
"""

from .base_role import BaseRole, RoleType
from .villager import Villager
from .werewolf import Werewolf
from .seer import Seer
from .witch import Witch
from .hunter import Hunter

__all__ = [
    'BaseRole',
    'RoleType',
    'Villager',
    'Werewolf',
    'Seer',
    'Witch',
    'Hunter'
] 