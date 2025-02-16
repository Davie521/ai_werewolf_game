import pytest
from unittest.mock import Mock, AsyncMock, patch
from ..controllers.phases.night_phase_controller import NightPhaseController
from ..controllers.phases.day_phase_controller import DayPhaseController
from ..models.game_state import GameState, GamePhase
from ..models.game_log import GameLog, GameEvent, GameEventType
from ..controllers.api_controller import APIController
from ..models.roles.base_role import RoleType
from ..models.player import Player
from ..models.roles.hunter import Hunter
from ..models.roles.werewolf import Werewolf
from ..models.roles.witch import Witch
from ..models.roles.villager import Villager
from ..controllers.game_controller import GameController
import os
from ..models.roles import Seer

pytestmark = pytest.mark.asyncio

class TestGameFlow:
    @pytest.fixture
    def game_state(self):
        return GameState()
    
    @pytest.fixture
    def game_log(self):
        return GameLog()
    
    @pytest.fixture
    def api_controller(self):
        controller = Mock(spec=APIController)
        # 模拟API响应
        controller.get_vote_action = AsyncMock(return_value={"target_id": 1})
        return controller
    
    @pytest.fixture
    async def game_controller(self, game_state, api_controller):
        controller = GameController(game_state=game_state, api_controller=api_controller)
        
        # 预设玩家列表
        preset_players = [
            Player(1, "小北", Werewolf()),
            Player(2, "浩然", Werewolf()),
            Player(3, "子轩", Werewolf()),
            Player(4, "雨萱", Seer()),
            Player(5, "梦瑶", Witch()),
            Player(6, "思远", Hunter()),
            Player(7, "欣怡", Villager()),
            Player(8, "语嫣", Villager()),
            Player(9, "晓峰", Villager())
        ]
        
        # 使用预设玩家初始化游戏
        player_names = [p.name for p in preset_players]
        await controller.initialize_game(player_names, preset_players)
        return controller
    
    def _print_phase_events(self, game_log: GameLog, start_index: int) -> int:
        """打印从指定索引开始的新事件
        
        Args:
            game_log: 游戏日志
            start_index: 开始索引
            
        Returns:
            int: 最新事件的索引
        """
        events = game_log.get_all_events()
        for i in range(start_index, len(events)):
            print(game_log.format_event(events[i]))
        return len(events)

    async def test_complete_game_flow(self, game_controller):
        """测试完整的游戏流程"""
        # 获取 game_controller
        controller = await game_controller
        
        # 确保日志目录存在
        assert os.path.exists(controller.log_dir)
        assert controller.game_log._output_file is not None
        
        # 第一个夜晚
        controller.game_log.write_phase_header("第一个夜晚")
        controller.game_log.add_event(GameEvent(
            GameEventType.NIGHT_START,
            {"round_number": 1}
        ))
        
        # 狼人行动
        controller.game_log.add_event(GameEvent(
            GameEventType.NIGHT_ACTION,
            {"werewolf_kill": "欣怡"},
            public=False,
            visible_to=[1, 2]  # 只有狼人可见
        ))
        
        # 预言家行动
        controller.game_log.add_event(GameEvent(
            GameEventType.NIGHT_ACTION,
            {
                "seer_check": {
                    "target": "小北",
                    "is_werewolf": True
                }
            },
            public=False,
            visible_to=[3]  # 只有预言家可见
        ))
        
        # 女巫行动
        controller.game_log.add_event(GameEvent(
            GameEventType.NIGHT_ACTION,
            {"witch_save": True},
            public=False,
            visible_to=[5]  # 只有女巫可见
        ))
        
        controller.game_log.add_event(GameEvent(
            GameEventType.NIGHT_END,
            {"round_number": 1}
        ))
        
        # 第一天
        controller.game_log.write_phase_header("第一天")
        controller.game_log.add_event(GameEvent(
            GameEventType.DAY_START,
            {"round_number": 1}
        ))
        
        # 死亡公告
        controller.game_log.add_event(GameEvent(
            GameEventType.DEATH_ANNOUNCE,
            {
                "deaths": []  # 平安夜
            }
        ))
        
        # 玩家发言
        controller.game_log.add_event(GameEvent(
            GameEventType.PLAYER_SPEAK,
            {
                "player_name": "雨萱",
                "message": "我是预言家，我昨晚查验了小北，他是狼人！"
            }
        ))
        
        # 投票
        controller.game_log.add_event(GameEvent(
            GameEventType.VOTE_START,
            {}
        ))
        
        controller.game_log.add_event(GameEvent(
            GameEventType.VOTE_RESULT,
            {
                "voted_name": "小北",
                "role": "狼人",
                "is_tie": False
            }
        ))
        
        # 猎人开枪
        controller.game_log.add_event(GameEvent(
            GameEventType.HUNTER_SHOT,
            {
                "hunter_name": "思远",
                "target_name": "浩然",
                "target_role": "狼人"
            }
        ))
        
        controller.game_log.add_event(GameEvent(
            GameEventType.DAY_END,
            {"round_number": 1}
        ))
        
        # 游戏结束
        controller.game_log.add_event(GameEvent(
            GameEventType.GAME_END,
            {
                "winning_team": "好人阵营",
                "rounds": 1
            }
        ))
        
        # 写入游戏总结
        controller.game_log.write_game_summary(
            alive_players=[
                {"name": "雨萱", "role": "预言家"},
                {"name": "梦瑶", "role": "女巫"},
                {"name": "语嫣", "role": "村民"},
                {"name": "晓峰", "role": "村民"},
                {"name": "子轩", "role": "村民"}
            ],
            dead_players=[
                {"name": "小北", "role": "狼人", "death_reason": "voted"},
                {"name": "浩然", "role": "狼人", "death_reason": "hunter_shot"},
                {"name": "思远", "role": "猎人", "death_reason": "werewolf"},
                {"name": "欣怡", "role": "村民", "death_reason": "werewolf"}
            ]
        )
        
        # 关闭日志文件
        controller.game_log.close()
        
        # 验证日志文件存在
        log_files = os.listdir(controller.log_dir)
        assert len(log_files) > 0
        assert any(f.startswith("game_log_") and f.endswith(".txt") for f in log_files)