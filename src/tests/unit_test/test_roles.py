import pytest
from ...models.roles.base_role import BaseRole, RoleType
from ...models.roles.witch import Witch
from ...models.roles.hunter import Hunter
from ...models.roles.seer import Seer
from ...models.roles.werewolf import Werewolf
from ...models.roles.villager import Villager
from ...models.player import Player

class TestBaseRole:
    """测试基础角色功能"""
    
    def test_role_initialization(self):
        """测试角色初始化"""
        role = BaseRole(RoleType.VILLAGER)
        assert role.role_type == RoleType.VILLAGER
        assert role.player_id is None
        assert role.is_alive is True
        assert role.death_reason is None
    
    def test_set_player(self):
        """测试设置玩家ID"""
        role = BaseRole(RoleType.WEREWOLF)
        role.set_player(1)
        assert role.player_id == 1
    
    def test_die(self):
        """测试角色死亡"""
        role = BaseRole(RoleType.SEER)
        role.die("werewolf")
        assert role.is_alive is False
        assert role.death_reason == "werewolf"

class TestWerewolf:
    """测试狼人角色"""
    
    def test_werewolf_initialization(self):
        """测试狼人初始化"""
        werewolf = Werewolf()
        assert werewolf.role_type == RoleType.WEREWOLF
        assert werewolf.has_voted is False
        
        # 创建狼人玩家
        player = Player(1, "狼人", werewolf)
        assert player.role.role_type == RoleType.WEREWOLF
        assert player.is_alive is True
    
    def test_werewolf_vote_reset(self):
        """测试狼人投票重置"""
        werewolf = Werewolf()
        werewolf.has_voted = True
        werewolf.reset_vote()
        assert werewolf.has_voted is False

class TestVillager:
    """测试平民角色"""
    
    def test_villager_initialization(self):
        """测试平民初始化"""
        villager = Villager()
        assert villager.role_type == RoleType.VILLAGER
        
        # 创建平民玩家
        player = Player(1, "平民", villager)
        assert player.role.role_type == RoleType.VILLAGER
        assert player.is_alive is True

class TestSeer:
    """测试预言家角色"""
    
    def test_seer_initialization(self):
        """测试预言家初始化"""
        seer = Seer()
        assert seer.role_type == RoleType.SEER
        assert len(seer.checked_players) == 0
        
        # 创建预言家玩家
        player = Player(1, "预言家", seer)
        assert player.role.role_type == RoleType.SEER
        assert player.is_alive is True
    
    def test_seer_check_player(self):
        """测试预言家查验玩家"""
        seer = Seer()
        
        # 测试查验新玩家
        seer.record_check(2)
        assert seer.has_checked(2) is True
        assert seer.has_checked(3) is False
        
        # 测试重复查验
        seer.record_check(2)
        assert len(seer.checked_players) == 1

class TestWitch:
    """测试女巫角色"""
    
    def test_witch_initialization(self):
        """测试女巫初始化"""
        witch = Witch()
        assert witch.role_type == RoleType.WITCH
        assert witch.has_potion("save") is True
        assert witch.has_potion("poison") is True
        
        # 创建女巫玩家
        player = Player(1, "女巫", witch)
        assert player.role.role_type == RoleType.WITCH
        assert player.is_alive is True
    
    def test_witch_use_potions(self):
        """测试女巫使用药水"""
        witch = Witch()
        
        # 测试使用解药
        assert witch.use_potion("save") is True
        assert witch.has_potion("save") is False
        assert witch.use_potion("save") is False  # 不能重复使用
        
        # 测试使用毒药
        assert witch.use_potion("poison") is True
        assert witch.has_potion("poison") is False
        assert witch.use_potion("poison") is False  # 不能重复使用
        
        # 测试使用不存在的药水
        assert witch.use_potion("fake") is False

class TestHunter:
    """测试猎人角色"""
    
    def test_hunter_initialization(self):
        """测试猎人初始化"""
        hunter = Hunter()
        assert hunter.role_type == RoleType.HUNTER
        assert hunter.has_shot is False
        assert hunter.can_shoot is True
        
        # 创建猎人玩家
        player = Player(1, "猎人", hunter)
        assert player.role.role_type == RoleType.HUNTER
        assert player.is_alive is True
    
    def test_hunter_shoot(self):
        """测试猎人开枪"""
        hunter = Hunter()
        
        # 测试正常开枪
        assert hunter.shoot() is True
        assert hunter.has_shot is True
        assert hunter.shoot() is False  # 不能重复开枪
        
        # 测试被毒死后无法开枪
        hunter = Hunter()
        hunter.die("poison")
        assert hunter.can_shoot is False
        assert hunter.shoot() is False
        
        # 测试其他死亡方式仍可开枪
        hunter = Hunter()
        hunter.die("werewolf")
        assert hunter.can_shoot is True
        assert hunter.shoot() is True 