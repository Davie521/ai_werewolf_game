"""
Mock API Controller for testing
"""
from src.controllers.api_controller import APIController
from src.models.roles.base_role import RoleType

class MockAPIController(APIController):
    """Mock API controller for testing purposes"""
    
    async def get_werewolf_kill_target(self, game_state, game_log):
        """Mock werewolf kill target selection"""
        # Return first alive non-werewolf player
        for player in game_state.players:
            if player.is_alive and player.role.role_type != RoleType.WEREWOLF:
                return player.id
        return None

    async def get_seer_check_target(self, game_state, game_log):
        """Mock seer check target selection"""
        # Return first alive player that hasn't been checked
        for player in game_state.players:
            if player.is_alive and not game_state.is_player_checked_by_seer(player.id):
                return player.id
        return None

    async def get_witch_action(self, game_state, game_log):
        """Mock witch action selection"""
        # Always save if possible, never poison
        if game_state.witch_can_save:
            return "save", game_state.last_killed_player_id
        return None, None

    async def get_hunter_shot_target(self, game_state, game_log):
        """Mock hunter shot target selection"""
        # Return first alive player that isn't the hunter
        hunter_id = None
        for player in game_state.players:
            if player.role.role_type == RoleType.HUNTER:
                hunter_id = player.id
                break
                
        for player in game_state.players:
            if player.is_alive and player.id != hunter_id:
                return player.id
        return None

    async def get_player_vote(self, game_state, game_log):
        """Mock player vote selection"""
        # Return first alive player that isn't self
        for player in game_state.players:
            if player.is_alive and player.id != game_state.current_player_id:
                return player.id
        return None 