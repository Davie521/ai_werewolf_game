import pytest
from ...models.game_state import GameState, GamePhase, WinningTeam
from ...models.game_log import GameLog
from ...models.player import Player
from ...models.roles.base_role import BaseRole, RoleType

from ...controllers.game_phase_manager import GamePhaseManager
from ...controllers.api_controller import APIController
from ..test_model.mock_api_controller import MockAPIController

@pytest.fixture
def game_setup():
    """基础游戏设置"""
    game_state = GameState()
    game_log = GameLog()
    api_controller = MockAPIController()
    phase_manager = GamePhaseManager(game_state, game_log, api_controller)
    
    # 添加测试玩家
    players = [
        Player(1, "狼人1", BaseRole(RoleType.WEREWOLF)),
        Player(2, "狼人2", BaseRole(RoleType.WEREWOLF)),
        Player(3, "狼人3", BaseRole(RoleType.WEREWOLF)),
        Player(4, "平民1", BaseRole(RoleType.VILLAGER)),
        Player(5, "平民2", BaseRole(RoleType.VILLAGER)),
        Player(6, "平民3", BaseRole(RoleType.VILLAGER)),
        Player(7, "预言家", BaseRole(RoleType.SEER)),
        Player(8, "女巫", BaseRole(RoleType.WITCH)),
        Player(9, "猎人", BaseRole(RoleType.HUNTER))
    ]
    
    for player in players:
        game_state.add_player(player)
        
    return game_state, game_log, api_controller, phase_manager

class TestPhaseFlow:
    """测试阶段流转"""
    
    def test_initial_phase(self, game_setup):
        """基础游戏设置"""
        game_state, _, _, phase_manager = game_setup
        assert game_state.current_phase == GamePhase.INIT
        
    def test_role_assignment_phase(self, game_setup):
        
        game_state, _, _, phase_manager = game_setup
        next_phase = phase_manager.get_next_phase(GamePhase.INIT)
        assert next_phase == GamePhase.ROLE_ASSIGNMENT
        
    def test_first_night_flow(self, game_setup):
        """测试第0晚的阶段流转"""
        game_state, _, _, phase_manager = game_setup
        
        # 从角色分配到第0晚开始
        phase = phase_manager.get_next_phase(GamePhase.ROLE_ASSIGNMENT)
        assert phase == GamePhase.NIGHT_START_0
        
        # 第0晚的完整流程
        phase = phase_manager.get_next_phase(GamePhase.NIGHT_START_0)
        assert phase == GamePhase.WEREWOLF_TURN_0
        
        phase = phase_manager.get_next_phase(GamePhase.WEREWOLF_TURN_0)
        assert phase == GamePhase.SEER_TURN_0
        
        phase = phase_manager.get_next_phase(GamePhase.SEER_TURN_0)
        assert phase == GamePhase.WITCH_TURN_0
        
        phase = phase_manager.get_next_phase(GamePhase.WITCH_TURN_0)
        assert phase == GamePhase.NIGHT_END_0
        
        phase = phase_manager.get_next_phase(GamePhase.NIGHT_END_0)
        assert phase == GamePhase.DAY_START
        
    def test_day_phase_flow(self, game_setup):
        """测试白天的阶段流转"""
        game_state, _, _, phase_manager = game_setup
        
        # 正常白天流程(无猎人死亡)
        phase = phase_manager.get_next_phase(GamePhase.DAY_START)
        assert phase == GamePhase.DEATH_REPORT
        
        phase = phase_manager.get_next_phase(GamePhase.DEATH_REPORT)
        assert phase == GamePhase.DISCUSSION  # 无猎人死亡时跳过FIRST_HUNTER_SHOT
        
        phase = phase_manager.get_next_phase(GamePhase.DISCUSSION)
        assert phase == GamePhase.VOTE
        
        phase = phase_manager.get_next_phase(GamePhase.VOTE)
        assert phase == GamePhase.EXILE
        
        phase = phase_manager.get_next_phase(GamePhase.EXILE)
        assert phase == GamePhase.DAY_END  # 无猎人被放逐时跳过EXILE_HUNTER_SHOT
        
        phase = phase_manager.get_next_phase(GamePhase.DAY_END)
        assert phase == GamePhase.NIGHT_START
        
    @pytest.mark.asyncio
    async def test_hunter_death_flow(self, game_setup):
        """测试猎人死亡时的阶段流转"""
        game_state, _, _, phase_manager = game_setup
        
        # 模拟猎人夜晚死亡
        hunter = game_state.get_player_by_id(9)  # 猎人ID为9
        hunter.is_alive = False
        hunter.death_reason = "werewolf"
        game_state.start_new_round()
        game_state.record_death(hunter.id, "werewolf", "night")
        
        # 检查是否进入猎人开枪阶段
        phase = phase_manager.get_next_phase(GamePhase.DEATH_REPORT)
        assert phase == GamePhase.FIRST_HUNTER_SHOT
        
    @pytest.mark.asyncio
    async def test_hunter_exile_flow(self, game_setup):
        """测试猎人被放逐时的阶段流转"""
        game_state, _, _, phase_manager = game_setup
        
        # 模拟猎人被放逐
        game_state.start_new_round()
        game_state.record_exile(9)  # 猎人ID为9
        
        # 检查是否进入猎人开枪阶段
        phase = phase_manager.get_next_phase(GamePhase.EXILE)
        assert phase == GamePhase.EXILE_HUNTER_SHOT 