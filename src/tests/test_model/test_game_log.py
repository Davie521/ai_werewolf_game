import pytest
from ...models.game_log import GameLog, GameEvent, GameEventType

class TestGameLog:
    @pytest.fixture
    def game_log(self):
        return GameLog()
    
    def test_game_start_event(self, game_log):
        """测试游戏开始事件的格式化"""
        event = GameEvent(
            GameEventType.GAME_START,
            {
                "player_count": 6,
                "players": [
                    {"id": 1, "name": "猎人"},
                    {"id": 2, "name": "狼人1"},
                    {"id": 3, "name": "狼人2"},
                    {"id": 4, "name": "女巫"},
                    {"id": 5, "name": "村民1"},
                    {"id": 6, "name": "村民2"}
                ]
            }
        )
        game_log.add_event(event)
        formatted = game_log.format_event(game_log.get_all_events()[0])
        assert "游戏开始！共有6名玩家参与" in formatted
        assert "猎人, 狼人1, 狼人2, 女巫, 村民1, 村民2" in formatted
    
    def test_game_end_event(self, game_log):
        """测试游戏结束事件的格式化"""
        event = GameEvent(
            GameEventType.GAME_END,
            {
                "winning_team": "好人阵营",
                "rounds": 3
            }
        )
        game_log.add_event(event)
        formatted = game_log.format_event(game_log.get_all_events()[0])
        assert "游戏结束！好人阵营获胜，共进行了3个回合" in formatted
    
    def test_night_action_events(self, game_log):
        """测试夜晚行动事件的格式化"""
        # 测试狼人击杀
        event1 = GameEvent(
            GameEventType.NIGHT_ACTION,
            {
                "werewolf_kill": "村民1"
            }
        )
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "狼人选择击杀了村民1" in formatted1
        
        # 测试女巫救人和毒人
        event2 = GameEvent(
            GameEventType.NIGHT_ACTION,
            {
                "witch_save": True,
                "witch_poison": "狼人1"
            }
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "女巫使用了解药" in formatted2
        assert "女巫使用了毒药" in formatted2
        
        # 测试预言家查验
        event3 = GameEvent(
            GameEventType.NIGHT_ACTION,
            {
                "seer_check": {
                    "target": "狼人1",
                    "is_werewolf": True
                }
            }
        )
        game_log.add_event(event3)
        formatted3 = game_log.format_event(game_log.get_all_events()[2])
        assert "预言家查验了狼人1，发现他是狼人" in formatted3
        
        # 测试平静的夜晚
        event4 = GameEvent(
            GameEventType.NIGHT_ACTION,
            {}
        )
        game_log.add_event(event4)
        formatted4 = game_log.format_event(game_log.get_all_events()[3])
        assert "这是一个平静的夜晚" in formatted4
    
    def test_death_announce_events(self, game_log):
        """测试死亡公告事件的格式化"""
        # 测试平安夜
        event1 = GameEvent(
            GameEventType.DEATH_ANNOUNCE,
            {"deaths": []}
        )
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "昨晚是平安夜" in formatted1
        
        # 测试单人死亡
        event2 = GameEvent(
            GameEventType.DEATH_ANNOUNCE,
            {
                "deaths": [{
                    "player_name": "村民1",
                    "role": "平民",
                    "reason": "werewolf"
                }]
            }
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "昨晚村民1(平民)被狼人杀死" in formatted2
        
        # 测试多人死亡
        event3 = GameEvent(
            GameEventType.DEATH_ANNOUNCE,
            {
                "deaths": [
                    {
                        "player_name": "村民1",
                        "role": "平民",
                        "reason": "werewolf"
                    },
                    {
                        "player_name": "狼人1",
                        "role": "狼人",
                        "reason": "poison"
                    }
                ]
            }
        )
        game_log.add_event(event3)
        formatted3 = game_log.format_event(game_log.get_all_events()[2])
        assert "昨晚村民1(平民)被狼人杀死，狼人1(狼人)被女巫毒死" in formatted3
    
    def test_vote_events(self, game_log):
        """测试投票相关事件的格式化"""
        # 测试开始投票
        event1 = GameEvent(GameEventType.VOTE_START, {})
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "开始投票" in formatted1
        
        # 测试平票
        event2 = GameEvent(
            GameEventType.VOTE_RESULT,
            {"is_tie": True}
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "投票结果为平票，没有玩家被放逐" in formatted2
        
        # 测试放逐结果
        event3 = GameEvent(
            GameEventType.VOTE_RESULT,
            {
                "is_tie": False,
                "voted_name": "狼人1",
                "role": "狼人"
            }
        )
        game_log.add_event(event3)
        formatted3 = game_log.format_event(game_log.get_all_events()[2])
        assert "投票结果：狼人1 (狼人) 被放逐" in formatted3
    
    def test_hunter_shot_events(self, game_log):
        """测试猎人开枪事件的格式化"""
        # 测试宣布可以开枪
        event1 = GameEvent(
            GameEventType.HUNTER_SHOT,
            {
                "hunter_name": "猎人",
                "time": "exile"
            }
        )
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "猎人猎人可以开枪" in formatted1
        
        # 测试实际开枪
        event2 = GameEvent(
            GameEventType.HUNTER_SHOT,
            {
                "hunter_name": "猎人",
                "target_name": "狼人1",
                "target_role": "狼人",
                "time": "exile"
            }
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "猎人猎人开枪带走了狼人1 (狼人)" in formatted2
    
    def test_player_speak_events(self, game_log):
        """测试玩家发言事件的格式化"""
        # 测试普通发言
        event1 = GameEvent(
            GameEventType.PLAYER_SPEAK,
            {
                "player_name": "村民1",
                "message": "我是好人"
            }
        )
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "村民1: 我是好人" in formatted1
        
        # 测试遗言
        event2 = GameEvent(
            GameEventType.LAST_WORDS,
            {
                "player_name": "猎人",
                "message": "我要开枪带走你"
            }
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "[遗言] 猎人: 我要开枪带走你" in formatted2
    
    def test_round_events(self, game_log):
        """测试回合相关事件的格式化"""
        # 测试回合开始
        event1 = GameEvent(
            GameEventType.ROUND_START,
            {"round_number": 1}
        )
        game_log.add_event(event1)
        formatted1 = game_log.format_event(game_log.get_all_events()[0])
        assert "第1回合开始" in formatted1
        
        # 测试夜晚开始
        event2 = GameEvent(
            GameEventType.NIGHT_START,
            {"round_number": 1}
        )
        game_log.add_event(event2)
        formatted2 = game_log.format_event(game_log.get_all_events()[1])
        assert "第1个夜晚开始了" in formatted2
        
        # 测试白天开始
        event3 = GameEvent(
            GameEventType.DAY_START,
            {"round_number": 1}
        )
        game_log.add_event(event3)
        formatted3 = game_log.format_event(game_log.get_all_events()[2])
        assert "第1天开始了" in formatted3
    
    def test_event_visibility(self, game_log):
        """测试事件可见性"""
        # 公开事件
        public_event = GameEvent(
            GameEventType.GAME_START,
            {"player_count": 6},
            public=True
        )
        game_log.add_event(public_event)
        
        # 私密事件
        private_event = GameEvent(
            GameEventType.NIGHT_ACTION,
            {"werewolf_kill": "村民1"},
            public=False,
            visible_to=[1, 2]  # 只对玩家1和2可见
        )
        game_log.add_event(private_event)
        
        events = game_log.get_all_events()
        assert events[0]["public"] is True
        assert events[1]["public"] is False
        assert events[1]["visible_to"] == [1, 2] 