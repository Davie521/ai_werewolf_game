import pytest
from unittest.mock import Mock, AsyncMock
from ...controllers.game_controller import GameController
from ...models.game_state import GameState, GamePhase
from ...controllers.api_controller import APIController
from ...models.roles.base_role import RoleType

pytestmark = pytest.mark.asyncio

class TestR1Game:
    @pytest.fixture
    def game_state(self):
        return GameState()
    
    @pytest.fixture
    def api_controller(self):
        controller = Mock(spec=APIController)
        # 模拟API响应
        controller.get_werewolf_kill_target = AsyncMock(return_value=1)
        controller.get_seer_check_target = AsyncMock(return_value=2)
        controller.get_witch_action = AsyncMock(return_value=(None, None))
        controller.get_vote_action = AsyncMock(return_value={"target_id": 1})
        return controller
    
    @pytest.fixture
    def game_controller(self, game_state, api_controller):
        return GameController(game_state=game_state, api_controller=api_controller)
    
    async def test_game_initialization(self, game_controller):
        """测试游戏初始化"""
        player_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "郑十一"]
        await game_controller.initialize_game(player_names)
        
        # 验证游戏状态
        assert len(game_controller.game_state.players) == 9
        assert game_controller.game_state.current_phase == GamePhase.INIT
        assert game_controller.game_state.round_number == 0
        
        # 验证角色分配
        roles = [p.role.role_type for p in game_controller.game_state.players]
        assert sum(1 for r in roles if r == RoleType.WEREWOLF) == 3
        assert sum(1 for r in roles if r == RoleType.VILLAGER) == 3
        assert sum(1 for r in roles if r == RoleType.SEER) == 1
        assert sum(1 for r in roles if r == RoleType.WITCH) == 1
        assert sum(1 for r in roles if r == RoleType.HUNTER) == 1
    
    async def test_game_phase_transition(self, game_controller):
        """测试游戏阶段转换"""
        player_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "郑十一"]
        await game_controller.initialize_game(player_names)
        
        # 执行一个完整的回合
        for _ in range(3):  # 执行几个阶段
            game_over = await game_controller.next_phase()
            if game_over:
                break
        
        # 验证游戏状态
        assert game_controller.game_state.round_number >= 0
        assert game_controller.game_state.current_round is not None
        assert len(game_controller.get_public_events()) > 0

if __name__ == "__main__":
    asyncio.run(test_r1_game()) 