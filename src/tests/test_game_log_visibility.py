import pytest
from ..models.game_log import GameLog, GameEvent, GameEventType
from ..models.roles.base_role import RoleType
from ..models.player import Player
from ..models.roles.werewolf import Werewolf
from ..models.roles.witch import Witch
from ..models.roles.seer import Seer
from ..models.roles.hunter import Hunter
from ..models.roles.villager import Villager

class TestGameLogVisibility:
    @pytest.fixture
    def game_log(self):
        return GameLog()
    
    @pytest.fixture
    def players(self):
        """创建测试玩家"""
        return [
            Player(1, "狼人1", Werewolf()),
            Player(2, "狼人2", Werewolf()),
            Player(3, "预言家", Seer()),
            Player(4, "女巫", Witch()),
            Player(5, "猎人", Hunter()),
            Player(6, "村民", Villager())
        ]
    
    def test_werewolf_visibility(self, game_log, players):
        """测试狼人能看到的信息"""
        werewolf = players[0]  # 狼人1
        
        # 添加各种事件
        events = [
            # 公开事件
            GameEvent(
                GameEventType.GAME_START,
                {
                    "player_count": 6,
                    "players": [{"id": p.id, "name": p.name} for p in players]
                }
            ),
            
            # 狼人行动（对所有狼人可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {"werewolf_kill": "村民"},
                public=False,
                visible_to=[1, 2]  # 狼人1和狼人2的ID
            ),
            
            # 预言家行动（只对预言家可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "seer_check": {
                        "target": "狼人1",
                        "is_werewolf": True
                    }
                },
                public=False,
                visible_to=[3]  # 预言家的ID
            ),
            
            # 女巫行动（只对女巫可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "witch_save": True,
                    "witch_poison": "狼人1"
                },
                public=False,
                visible_to=[4]  # 女巫的ID
            ),
            
            # 死亡公告（公开）
            GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {
                    "deaths": [{
                        "player_name": "村民",
                        "role": "平民",
                        "reason": "werewolf"
                    }]
                }
            )
        ]
        
        for event in events:
            game_log.add_event(event)
        
        # 获取狼人可见的事件
        visible_events = [
            event for event in game_log.get_all_events()
            if event["public"] or werewolf.id in event.get("visible_to", [])
        ]
        
        # 验证狼人能看到的事件
        assert len(visible_events) == 3  # 游戏开始、狼人行动、死亡公告
        assert any(e["type"] == "game_start" for e in visible_events)
        assert any(e["type"] == "night_action" and "werewolf_kill" in e["details"] for e in visible_events)
        assert any(e["type"] == "death_announce" for e in visible_events)
        
        # 验证狼人看不到的事件
        assert not any(e["type"] == "night_action" and "seer_check" in e["details"] for e in visible_events)
        assert not any(e["type"] == "night_action" and "witch_save" in e["details"] for e in visible_events)
    
    def test_seer_visibility(self, game_log, players):
        """测试预言家能看到的信息"""
        seer = players[2]  # 预言家
        
        # 添加各种事件
        events = [
            # 公开事件
            GameEvent(
                GameEventType.GAME_START,
                {
                    "player_count": 6,
                    "players": [{"id": p.id, "name": p.name} for p in players]
                }
            ),
            
            # 狼人行动（对狼人可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {"werewolf_kill": "村民"},
                public=False,
                visible_to=[1, 2]
            ),
            
            # 预言家查验结果（对预言家可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "seer_check": {
                        "target": "狼人1",
                        "is_werewolf": True
                    }
                },
                public=False,
                visible_to=[3]
            ),
            
            # 死亡公告（公开）
            GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {
                    "deaths": [{
                        "player_name": "村民",
                        "role": "平民",
                        "reason": "werewolf"
                    }]
                }
            )
        ]
        
        for event in events:
            game_log.add_event(event)
        
        # 获取预言家可见的事件
        visible_events = [
            event for event in game_log.get_all_events()
            if event["public"] or seer.id in event.get("visible_to", [])
        ]
        
        # 验证预言家能看到的事件
        assert len(visible_events) == 3  # 游戏开始、预言家查验、死亡公告
        assert any(e["type"] == "game_start" for e in visible_events)
        assert any(e["type"] == "night_action" and "seer_check" in e["details"] for e in visible_events)
        assert any(e["type"] == "death_announce" for e in visible_events)
        
        # 验证预言家看不到的事件
        assert not any(e["type"] == "night_action" and "werewolf_kill" in e["details"] for e in visible_events)
    
    def test_witch_visibility(self, game_log, players):
        """测试女巫能看到的信息"""
        witch = players[3]  # 女巫
        
        # 添加各种事件
        events = [
            # 公开事件
            GameEvent(
                GameEventType.GAME_START,
                {
                    "player_count": 6,
                    "players": [{"id": p.id, "name": p.name} for p in players]
                }
            ),
            
            # 狼人行动（对女巫可见，因为她需要知道谁被杀了）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {"werewolf_kill": "村民"},
                public=False,
                visible_to=[1, 2, 4]  # 包括女巫ID
            ),
            
            # 女巫行动结果（对女巫可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "witch_save": True,
                    "witch_poison": "狼人1"
                },
                public=False,
                visible_to=[4]
            ),
            
            # 死亡公告（公开）
            GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {
                    "deaths": [{
                        "player_name": "狼人1",
                        "role": "狼人",
                        "reason": "poison"
                    }]
                }
            )
        ]
        
        for event in events:
            game_log.add_event(event)
        
        # 获取女巫可见的事件
        visible_events = [
            event for event in game_log.get_all_events()
            if event["public"] or witch.id in event.get("visible_to", [])
        ]
        
        # 验证女巫能看到的事件
        assert len(visible_events) == 4  # 游戏开始、狼人行动、女巫行动、死亡公告
        assert any(e["type"] == "game_start" for e in visible_events)
        assert any(e["type"] == "night_action" and "werewolf_kill" in e["details"] for e in visible_events)
        assert any(e["type"] == "night_action" and "witch_save" in e["details"] for e in visible_events)
        assert any(e["type"] == "death_announce" for e in visible_events)
    
    def test_villager_visibility(self, game_log, players):
        """测试普通村民能看到的信息"""
        villager = players[5]  # 村民
        
        # 添加各种事件
        events = [
            # 公开事件
            GameEvent(
                GameEventType.GAME_START,
                {
                    "player_count": 6,
                    "players": [{"id": p.id, "name": p.name} for p in players]
                }
            ),
            
            # 狼人行动（对狼人可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {"werewolf_kill": "村民"},
                public=False,
                visible_to=[1, 2]
            ),
            
            # 预言家行动（对预言家可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "seer_check": {
                        "target": "狼人1",
                        "is_werewolf": True
                    }
                },
                public=False,
                visible_to=[3]
            ),
            
            # 女巫行动（对女巫可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "witch_save": True,
                    "witch_poison": "狼人1"
                },
                public=False,
                visible_to=[4]
            ),
            
            # 死亡公告（公开）
            GameEvent(
                GameEventType.DEATH_ANNOUNCE,
                {
                    "deaths": [{
                        "player_name": "村民",
                        "role": "平民",
                        "reason": "werewolf"
                    }]
                }
            ),
            
            # 投票结果（公开）
            GameEvent(
                GameEventType.VOTE_RESULT,
                {
                    "is_tie": False,
                    "voted_name": "狼人1",
                    "role": "狼人"
                }
            )
        ]
        
        for event in events:
            game_log.add_event(event)
        
        # 获取村民可见的事件
        visible_events = [
            event for event in game_log.get_all_events()
            if event["public"] or villager.id in event.get("visible_to", [])
        ]
        
        # 验证村民能看到的事件
        assert len(visible_events) == 3  # 只能看到公开事件：游戏开始、死亡公告、投票结果
        assert any(e["type"] == "game_start" for e in visible_events)
        assert any(e["type"] == "death_announce" for e in visible_events)
        assert any(e["type"] == "vote_result" for e in visible_events)
        
        # 验证村民看不到的事件
        assert not any(e["type"] == "night_action" for e in visible_events)
    
    def test_get_player_events(self, game_log, players):
        """测试获取指定玩家的事件"""
        # 添加各种事件
        events = [
            # 公开事件
            GameEvent(
                GameEventType.GAME_START,
                {
                    "player_count": 6,
                    "players": [{"id": p.id, "name": p.name} for p in players]
                }
            ),
            
            # 狼人行动（对狼人可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {"werewolf_kill": "村民"},
                public=False,
                visible_to=[1, 2]
            ),
            
            # 预言家行动（对预言家可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "seer_check": {
                        "target": "狼人1",
                        "is_werewolf": True
                    }
                },
                public=False,
                visible_to=[3]
            ),
            
            # 女巫行动（对女巫可见）
            GameEvent(
                GameEventType.NIGHT_ACTION,
                {
                    "witch_save": True,
                    "witch_poison": "狼人1"
                },
                public=False,
                visible_to=[4]
            )
        ]
        
        for event in events:
            game_log.add_event(event)
        
        # 测试每个玩家能看到的事件数量
        for player in players:
            visible_events = [
                event for event in game_log.get_all_events()
                if event["public"] or player.id in event.get("visible_to", [])
            ]
            
            if player.role.role_type == RoleType.WEREWOLF:
                assert len(visible_events) == 2  # 游戏开始 + 狼人行动
            elif player.role.role_type == RoleType.SEER:
                assert len(visible_events) == 2  # 游戏开始 + 预言家行动
            elif player.role.role_type == RoleType.WITCH:
                assert len(visible_events) == 2  # 游戏开始 + 女巫行动
            else:
                assert len(visible_events) == 1  # 只能看到游戏开始 