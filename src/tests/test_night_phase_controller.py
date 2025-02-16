import pytest
from unittest.mock import Mock, AsyncMock, patch
from ..controllers.phases.night_phase_controller import NightPhaseController
from ..models.game_state import GameState, GamePhase, NightAction
from ..models.game_log import GameLog
from ..controllers.api_controller import APIController
from ..models.roles.base_role import RoleType
from ..models.player import Player
from ..models.roles.werewolf import Werewolf
from ..models.roles.witch import Witch
from ..models.roles.villager import Villager
from ..models.roles.hunter import Hunter

pytestmark = pytest.mark.asyncio

class TestNightPhaseController:
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
    def night_controller(self, game_state, game_log, api_controller):
        return NightPhaseController(game_state, game_log, api_controller)
    
    async def test_process_werewolf_kill(self, night_controller, game_state):
        """测试狼人击杀处理"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        game_state.add_player(villager)
        
        # 设置夜晚行动
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = False
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证村民死亡
        assert not villager.is_alive
        assert villager.death_reason == "werewolf"
        assert len(game_state.current_round.deaths) == 1
        assert game_state.current_round.deaths[0]["player_id"] == villager.id
        assert game_state.current_round.deaths[0]["reason"] == "werewolf"
    
    async def test_process_witch_save(self, night_controller, game_state):
        """测试女巫救人"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(villager)
        game_state.add_player(witch)
        
        # 设置夜晚行动
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = True
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证村民存活
        assert villager.is_alive
        assert villager.death_reason is None
        assert len(game_state.current_round.deaths) == 0
        
        # 验证解药已使用
        witch_potions = game_state.get_witch_potions(witch.id)
        assert not witch_potions["save"]
    
    async def test_process_witch_poison(self, night_controller, game_state):
        """测试女巫毒人"""
        # 创建测试玩家
        werewolf = Player(1, "狼人", Werewolf())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(werewolf)
        game_state.add_player(witch)
        
        # 设置夜晚行动
        game_state.start_new_round()
        game_state.current_round.night_action.witch_poison = werewolf.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证狼人死亡
        assert not werewolf.is_alive
        assert werewolf.death_reason == "poison"
        assert len(game_state.current_round.deaths) == 1
        assert game_state.current_round.deaths[0]["player_id"] == werewolf.id
        assert game_state.current_round.deaths[0]["reason"] == "poison"
        
        # 验证毒药已使用
        witch_potions = game_state.get_witch_potions(witch.id)
        assert not witch_potions["poison"]
    
    async def test_multiple_deaths(self, night_controller, game_state):
        """测试多人死亡情况"""
        # 创建测试玩家
        villager1 = Player(1, "村民1", Villager())
        villager2 = Player(2, "村民2", Villager())
        witch = Player(3, "女巫", Witch())
        game_state.add_player(villager1)
        game_state.add_player(villager2)
        game_state.add_player(witch)
        
        # 设置夜晚行动：狼人杀一个，女巫毒一个
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager1.id
        game_state.current_round.night_action.witch_save = False
        game_state.current_round.night_action.witch_poison = villager2.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证两人都死亡
        assert not villager1.is_alive
        assert villager1.death_reason == "werewolf"
        assert not villager2.is_alive
        assert villager2.death_reason == "poison"
        assert len(game_state.current_round.deaths) == 2
    
    async def test_no_deaths(self, night_controller, game_state):
        """测试无人死亡的情况"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(villager)
        game_state.add_player(witch)
        
        # 设置夜晚行动：没有任何击杀
        game_state.start_new_round()
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证无人死亡
        assert villager.is_alive
        assert villager.death_reason is None
        assert len(game_state.current_round.deaths) == 0
    
    async def test_witch_save_and_poison_same_night(self, night_controller, game_state):
        """测试女巫同时救人和毒人"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        werewolf = Player(2, "狼人", Werewolf())
        witch = Player(3, "女巫", Witch())
        game_state.add_player(villager)
        game_state.add_player(werewolf)
        game_state.add_player(witch)
        
        # 设置夜晚行动：狼人杀村民，女巫救村民并毒狼人
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = True
        game_state.current_round.night_action.witch_poison = werewolf.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证村民存活，狼人未死亡（因为女巫一晚只能用一瓶药）
        assert villager.is_alive
        assert villager.death_reason is None
        assert werewolf.is_alive  # 毒药未生效
        assert werewolf.death_reason is None
        assert len(game_state.current_round.deaths) == 0
        
        # 验证只使用了解药
        witch_potions = game_state.get_witch_potions(witch.id)
        assert not witch_potions["save"]  # 解药已用
        assert witch_potions["poison"]    # 毒药未用
    
    async def test_witch_one_potion_per_night(self, night_controller, game_state):
        """测试女巫一晚只能用一瓶药"""
        # 创建测试玩家
        villager1 = Player(1, "村民1", Villager())
        villager2 = Player(2, "村民2", Villager())
        witch = Player(3, "女巫", Witch())
        game_state.add_player(villager1)
        game_state.add_player(villager2)
        game_state.add_player(witch)
        
        # 设置夜晚行动：尝试同时使用救药和毒药
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager1.id
        game_state.current_round.night_action.witch_save = True
        game_state.current_round.night_action.witch_poison = villager2.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证只有第一个药水生效（救人）
        assert villager1.is_alive  # 被救活了
        assert villager1.death_reason is None
        assert villager2.is_alive  # 毒药没有生效
        assert villager2.death_reason is None
        assert len(game_state.current_round.deaths) == 0
        
        # 验证只使用了一瓶药
        witch_potions = game_state.get_witch_potions(witch.id)
        assert not witch_potions["save"]  # 解药已用
        assert witch_potions["poison"]    # 毒药未用
    
    async def test_multiple_kill_actions_same_target(self, night_controller, game_state):
        """测试同一个人被多次击杀的情况"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(villager)
        game_state.add_player(witch)
        
        # 设置夜晚行动：狼人杀和女巫毒同一个人
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = False
        game_state.current_round.night_action.witch_poison = villager.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证玩家死亡，但只记录一次死亡（以第一个死因为准）
        assert not villager.is_alive
        assert villager.death_reason == "werewolf"  # 第一个死因
        assert len(game_state.current_round.deaths) == 1
        assert game_state.current_round.deaths[0]["player_id"] == villager.id
        assert game_state.current_round.deaths[0]["reason"] == "werewolf"
    
    async def test_witch_potion_usage_tracking(self, night_controller, game_state):
        """测试女巫药水使用情况追踪"""
        # 创建测试玩家
        villager = Player(1, "村民", Villager())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(villager)
        game_state.add_player(witch)
        
        # 第一回合：使用解药
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = True
        
        # 处理第一回合夜晚行动
        night_controller._process_night_actions()
        
        # 验证解药使用情况
        witch_potions = game_state.get_witch_potions(witch.id)
        assert not witch_potions["save"]  # 解药已用
        assert witch_potions["poison"]    # 毒药还在
        
        # 第二回合：尝试再次使用解药（应该无效）
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = villager.id
        game_state.current_round.night_action.witch_save = True
        
        # 处理第二回合夜晚行动
        night_controller._process_night_actions()
        
        # 验证第二次使用解药无效
        assert not villager.is_alive
        assert villager.death_reason == "werewolf"
    
    async def test_hunter_poisoned_at_night(self, night_controller, game_state):
        """测试猎人被毒死后不能开枪"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        witch = Player(2, "女巫", Witch())
        villager = Player(3, "村民", Villager())
        game_state.add_player(hunter)
        game_state.add_player(witch)
        game_state.add_player(villager)
        
        # 设置夜晚行动：女巫毒死猎人
        game_state.start_new_round()
        game_state.current_round.night_action.witch_poison = hunter.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证猎人死亡且不能开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "poison"
        assert not hunter.role.can_shoot  # 被毒死后不能开枪
        
    async def test_hunter_killed_by_werewolf(self, night_controller, game_state):
        """测试猎人被狼人杀死后可以开枪"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        villager = Player(2, "村民", Villager())
        game_state.add_player(hunter)
        game_state.add_player(villager)
        
        # 设置夜晚行动：狼人杀死猎人
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = hunter.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证猎人死亡但仍能开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "werewolf"
        assert hunter.role.can_shoot  # 被狼人杀死后仍能开枪
        
    async def test_hunter_multiple_deaths(self, night_controller, game_state):
        """测试猎人同时被狼人和女巫攻击"""
        # 创建测试玩家
        hunter = Player(1, "猎人", Hunter())
        witch = Player(2, "女巫", Witch())
        game_state.add_player(hunter)
        game_state.add_player(witch)
        
        # 设置夜晚行动：狼人和女巫同时攻击猎人
        game_state.start_new_round()
        game_state.current_round.night_action.werewolf_kill = hunter.id
        game_state.current_round.night_action.witch_poison = hunter.id
        
        # 处理夜晚行动
        night_controller._process_night_actions()
        
        # 验证猎人死亡，且死因是第一个行动（狼人击杀），因此仍能开枪
        assert not hunter.is_alive
        assert hunter.death_reason == "werewolf"  # 第一个死因
        assert hunter.role.can_shoot  # 被狼人杀死后仍能开枪
        assert len(game_state.current_round.deaths) == 1  # 只记录一次死亡 