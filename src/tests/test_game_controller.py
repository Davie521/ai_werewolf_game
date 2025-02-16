import pytest
from unittest.mock import Mock, patch, AsyncMock
from ..controllers.game_controller import GameController
from ..models.game_state import GameState
from ..controllers.api_controller import APIController
from ..models.game_log import GameEvent, GameEventType
from ..models.roles.base_role import RoleType
import os

pytestmark = pytest.mark.asyncio

class TestGameController:
    @pytest.fixture
    def game_state(self):
        return GameState()
    
    @pytest.fixture
    def api_controller(self):
        return Mock(spec=APIController)
    
    @pytest.fixture
    def game_controller(self, game_state, api_controller):
        controller = GameController(game_state=game_state, api_controller=api_controller)
        controller.phase_manager = AsyncMock()
        return controller
    
    async def test_initialization(self, game_controller):
        """测试GameController的基本初始化"""
        assert game_controller.game_state is not None
        assert game_controller.game_log is not None
        assert game_controller.api_controller is not None
        assert game_controller.phase_manager is not None
        assert game_controller.game_output_file is None
        
    @patch('builtins.open')
    async def test_initialize_game(self, mock_open, game_controller):
        """测试游戏初始化"""
        # 准备9名玩家
        player_names = [f"Player{i}" for i in range(1, 10)]
        mock_file = Mock()
        mock_open.return_value = mock_file
        
        await game_controller.initialize_game(player_names)
        
        # 验证游戏状态
        assert len(game_controller.game_state.players) == 9
        
        # 验证角色分配
        roles = [p.role.role_type for p in game_controller.game_state.players]
        assert sum(1 for r in roles if r == RoleType.WEREWOLF) == 3  # 3个狼人
        assert sum(1 for r in roles if r == RoleType.VILLAGER) == 3  # 3个平民
        assert sum(1 for r in roles if r == RoleType.SEER) == 1      # 1个预言家
        assert sum(1 for r in roles if r == RoleType.WITCH) == 1     # 1个女巫
        assert sum(1 for r in roles if r == RoleType.HUNTER) == 1    # 1个猎人
        
        # 验证日志文件创建
        mock_open.assert_called_once()
        file_path = mock_open.call_args[0][0]
        assert os.path.basename(file_path).startswith("game_log_")
        assert os.path.basename(file_path).endswith(".txt")
        assert "game_logs" in file_path
        
        # 验证游戏开始事件被记录
        events = game_controller.get_public_events()
        assert len(events) > 0
        assert any("游戏开始" in event for event in events)
        
    async def test_initialize_game_wrong_player_count(self, game_controller):
        """测试错误的玩家数量"""
        player_names = ["Player1", "Player2", "Player3"]  # 只有3名玩家
        
        with pytest.raises(ValueError) as excinfo:
            await game_controller.initialize_game(player_names)
        assert "当前游戏必须为9名玩家" in str(excinfo.value)
        
    async def test_run_game(self, game_controller):
        """测试游戏运行主循环"""
        # 设置模拟的phase_manager
        game_controller.phase_manager.execute_current_phase = AsyncMock()
        game_controller.phase_manager.next_phase = Mock(side_effect=[True, True, False])
        
        # 运行游戏
        await game_controller.run_game()
        
        # 验证phase_manager的方法被正确调用
        assert game_controller.phase_manager.execute_current_phase.call_count == 3
        assert game_controller.phase_manager.next_phase.call_count == 3
        
        # 验证execute_current_phase被正确等待
        for call in game_controller.phase_manager.execute_current_phase.mock_calls:
            assert call.awaited
        
    async def test_get_player_events(self, game_controller):
        """测试获取玩家事件"""
        # 添加一些测试事件
        test_event = GameEvent(
            GameEventType.DEATH_ANNOUNCE,
            {
                "deaths": [{
                    "player_id": 1,
                    "player_name": "Player1",
                    "role": "平民",
                    "reason": "狼人袭击"
                }]
            },
            public=False,  # 设置为私密事件
            visible_to=[1]  # 只对玩家1可见
        )
        game_controller.game_log.add_event(test_event)
        
        # 测试相关玩家能看到事件
        player1_events = game_controller.get_player_events(1)
        assert len(player1_events) == 1
        assert "死亡" in player1_events[0]
        
        # 测试其他玩家看不到私密事件
        player3_events = game_controller.get_player_events(3)
        assert len(player3_events) == 0
        
    async def test_get_public_events(self, game_controller):
        """测试获取公开事件"""
        # 添加一个公开事件
        public_event = GameEvent(
            GameEventType.GAME_START,
            {
                "player_count": 6,
                "players": [{"id": i + 1, "name": f"Player{i+1}"} for i in range(6)]
            }
        )
        game_controller.game_log.add_event(public_event)
        
        # 添加一个私密事件
        private_event = GameEvent(
            GameEventType.NIGHT_ACTION,
            {
                "witch_poison": True,
                "target": 1
            },
            public=False
        )
        game_controller.game_log.add_event(private_event)
        
        # 验证只能看到公开事件
        public_events = game_controller.get_public_events()
        assert len(public_events) == 1
        assert "游戏开始" in public_events[0]
        
    @patch('builtins.open')
    async def test_write_to_log(self, mock_open, game_controller):
        """测试写入日志文件"""
        # 模拟文件对象
        mock_file = Mock()
        mock_open.return_value = mock_file
        
        # 初始化游戏以创建日志文件
        game_controller.game_output_file = mock_file
        
        # 写入测试消息
        test_message = "测试日志消息"
        game_controller.write_to_log(test_message)
        
        # 验证写入操作
        mock_file.write.assert_called_once_with(test_message + "\n")
        mock_file.flush.assert_called_once()
        
    async def test_cleanup(self, game_controller):
        """测试清理资源"""
        # 模拟文件对象
        mock_file = Mock()
        game_controller.game_output_file = mock_file
        
        # 执行清理
        game_controller.cleanup()
        
        # 验证文件被关闭
        mock_file.close.assert_called_once() 