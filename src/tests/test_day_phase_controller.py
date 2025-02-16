import pytest
from unittest.mock import Mock, AsyncMock, patch
from ..controllers.phases.day_phase_controller import DayPhaseController
from ..models.game_state import GameState, GamePhase
from ..models.game_log import GameLog
from ..controllers.api_controller import APIController
from ..models.roles.base_role import RoleType
from ..models.player import Player
from ..models.roles.hunter import Hunter
from ..models.roles.werewolf import Werewolf
from ..models.roles.witch import Witch
from ..models.roles.villager import Villager

pytestmark = pytest.mark.asyncio

class TestDayPhaseController:
    @pytest.fixture
    def game_state(self):
        return GameState()
    
    @pytest.fixture
    def game_log(self):
        return GameLog()
    
    @pytest.fixture
    def api_controller(self):
        return Mock(spec=APIController)
    
    @pytest.fixture
    def day_controller(self, game_state, game_log, api_controller):
        return DayPhaseController(game_state, game_log, api_controller)
    
    async def test_hunter_vote_and_shoot(self, day_controller, game_state):
        """测试猎人在投票环节可以开枪"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        werewolf = Player(2, "狼人", Werewolf())
        villager = Player(3, "村民", Villager())
        game_state.add_player(hunter)
        game_state.add_player(werewolf)
        game_state.add_player(villager)
        
        # 设置投票结果（猎人被投票出局）
        game_state.start_new_round()
        game_state.record_vote(2, hunter.id)  # 狼人投票猎人
        game_state.record_vote(3, hunter.id)  # 村民投票猎人
        
        # 处理投票结果
        day_controller._process_vote_result()
        
        # 验证猎人死亡但仍能开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "voted"
        assert hunter.role.can_shoot  # 被投票后仍能开枪
        
    async def test_hunter_poisoned_no_shot(self, day_controller, game_state):
        """测试被毒死的猎人在白天不能开枪"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        witch = Player(2, "女巫", Witch())
        villager = Player(3, "村民", Villager())
        game_state.add_player(hunter)
        game_state.add_player(witch)
        game_state.add_player(villager)
        
        # 设置夜晚被毒死
        game_state.start_new_round()
        hunter.die("poison")  # 直接设置猎人被毒死
        hunter.role.can_shoot = False  # 被毒死后失去开枪能力
        
        # 设置投票
        game_state.record_vote(2, villager.id)
        game_state.record_vote(3, villager.id)
        
        # 处理投票结果
        day_controller._process_vote_result()
        
        # 验证猎人不能开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "poison"
        assert not hunter.role.can_shoot  # 被毒死后不能开枪
        
    async def test_hunter_killed_by_werewolf_can_shoot(self, day_controller, game_state):
        """测试被狼人杀死的猎人在白天可以开枪"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        werewolf = Player(2, "狼人", Werewolf())
        villager = Player(3, "村民", Villager())
        game_state.add_player(hunter)
        game_state.add_player(werewolf)
        game_state.add_player(villager)
        
        # 设置夜晚被狼人杀死
        game_state.start_new_round()
        hunter.die("werewolf")  # 直接设置猎人被狼人杀死
        
        # 设置投票
        game_state.record_vote(2, villager.id)
        game_state.record_vote(3, villager.id)
        
        # 处理投票结果
        day_controller._process_vote_result()
        
        # 验证猎人可以开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "werewolf"
        assert hunter.role.can_shoot  # 被狼人杀死后可以开枪 