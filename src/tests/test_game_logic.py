import pytest
import pytest_asyncio
from src.models.game_state import GameState
from src.controllers.game_controller import GameController
from src.models.role import RoleType
from src.models.player import Player
from src.tests.mock_api_controller import MockAPIController

def get_player_by_role(game: GameController, role_type: RoleType) -> Player:
    """根据角色类型获取玩家"""
    for player in game.game_state.players:
        if player.role.role_type == role_type:
            if role_type == RoleType.SEER:
                print(f"[DEBUG] 找到预言家: ID={player.id}, name={player.name}")
            return player
    return None

@pytest_asyncio.fixture
async def game():
    """创建游戏实例的fixture"""
    api_controller = MockAPIController()
    game_state = GameState()
    game_controller = GameController(game_state, api_controller)
    player_names = [
        "村民1", "村民2", "村民3",  # 村民
        "狼人1", "狼人2", "狼人3",  # 狼人
        "预言家", "女巫", "猎人"    # 神职
    ]
    await game_controller.initialize_game(player_names)
    return game_controller

@pytest.mark.asyncio
async def test_game_initialization(game: GameController):
    """测试游戏初始化"""
    # 验证玩家数量
    assert len(game.game_state.players) == 9
    
    # 验证角色分配
    roles = [p.role.role_type for p in game.game_state.players]
    assert roles.count(RoleType.WEREWOLF) == 3
    assert roles.count(RoleType.VILLAGER) == 3
    assert roles.count(RoleType.WITCH) == 1
    assert roles.count(RoleType.SEER) == 1
    assert roles.count(RoleType.HUNTER) == 1

@pytest.mark.asyncio
async def test_night_phase(game: GameController):
    """测试夜晚阶段"""
    # 场景1：昨晚死亡信息显示
    # 模拟狼人击杀
    target = game.game_state.get_player_by_id(1)
    target.is_alive = False
    target.death_reason = "werewolf"
    game.game_state._last_night_killed = target.id
    
    # 运行白天阶段
    await game.run_day_phase()
    
    # 验证日志文件中的死亡信息
    with open(game.game_output_file.name, 'r', encoding='utf-8') as f:
        log_text = f.read()
        assert "昨晚是平安夜" not in log_text  # 不应该显示平安夜
        assert f"昨晚死亡的玩家：" in log_text  # 应该显示死亡玩家
        assert f"- {target.name}" in log_text  # 应该显示死亡玩家名字
    
    # 重置游戏状态
    game.game_state.reset()
    await game.initialize_game(["村民1", "村民2", "村民3", "狼人1", "狼人2", "狼人3", "预言家", "女巫", "猎人"])
    
    # 场景2：被救活显示为平安夜
    # 模拟狼人击杀并被救活
    target = game.game_state.get_player_by_id(1)
    target.is_alive = True  # 被救活
    target.death_reason = None
    game.game_state._last_night_killed = target.id
    game.game_state._last_night_saved = True
    
    # 运行白天阶段
    await game.run_day_phase()
    
    # 验证日志文件中显示平安夜
    with open(game.game_output_file.name, 'r', encoding='utf-8') as f:
        log_text = f.read()
        assert "昨晚是平安夜" in log_text  # 应该显示平安夜
        assert f"- {target.name}" not in log_text  # 不应该显示任何死亡玩家
    
    # 清理资源
    if game.game_output_file:
        game.game_output_file.close()

@pytest.mark.asyncio
async def test_vote_phase(game: GameController):
    """测试投票阶段"""
    # 运行投票阶段
    await game.run_vote_phase()
    
    # 验证投票记录
    votes = game.game_state.votes
    assert len(votes) > 0
    
    # 验证投票结果
    voted_out_player = next((p for p in game.game_state.players if not p.is_alive), None)
    assert voted_out_player is not None

@pytest.mark.asyncio
async def test_hunter_shot_scenarios(game: GameController):
    """测试猎人开枪的不同场景"""
    player_names = [
        "村民1", "村民2", "村民3",  # 村民
        "狼人1", "狼人2", "狼人3",  # 狼人
        "预言家", "女巫", "猎人"    # 神职
    ]
    
    # 场景1：猎人被投票放逐
    hunter = get_player_by_role(game, RoleType.HUNTER)
    target = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)  # 选择一个村民作为目标
    
    hunter.is_alive = False
    hunter.death_reason = "voted"
    result = await game.handle_hunter_shot(hunter.id, target.id)
    assert result is True  # 确认开枪成功
    assert not target.is_alive  # 确认目标已死亡
    assert target.death_reason == "hunter_shot"  # 验证死亡原因
    
    # 重置游戏状态
    await game.initialize_game(player_names)
    hunter = get_player_by_role(game, RoleType.HUNTER)
    target = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)  # 选择一个村民作为目标
    
    # 场景2：猎人被狼人杀死
    hunter.is_alive = False
    hunter.death_reason = "werewolf"
    result = await game.handle_hunter_shot(hunter.id, target.id)
    assert result is True  # 确认开枪成功
    assert not target.is_alive  # 确认目标已死亡
    assert target.death_reason == "hunter_shot"  # 验证死亡原因
    
    # 重置游戏状态
    await game.initialize_game(player_names)
    hunter = get_player_by_role(game, RoleType.HUNTER)
    target = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)  # 选择一个村民作为目标
    
    # 场景3：猎人被女巫毒死
    hunter.is_alive = False
    hunter.death_reason = "poison"
    result = await game.handle_hunter_shot(hunter.id, target.id)
    assert result is False  # 确认开枪失败
    assert target.is_alive  # 确认目标还活着
    assert target.death_reason is None  # 确认没有死亡原因
    
    # 场景4：猎人死亡时的自动开枪处理
    await game.initialize_game(player_names)
    hunter = get_player_by_role(game, RoleType.HUNTER)
    target = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)  # 选择一个村民作为目标
    
    # 模拟猎人被狼人杀死
    hunter.is_alive = False
    hunter.death_reason = "werewolf"
    await game._handle_player_death(hunter)
    
    # 验证目标玩家的状态（根据 MockAPIController 的行为，应该会射杀 ID 为 3 的玩家）
    target = next(p for p in game.game_state.players if p.id == 3)
    assert not target.is_alive  # 确认目标已死亡
    assert target.death_reason == "hunter_shot"  # 验证死亡原因

@pytest.mark.asyncio
async def test_game_over_conditions(game: GameController):
    """测试游戏结束条件"""
    player_names = [
        "村民1", "村民2", "村民3",  # 村民
        "狼人1", "狼人2", "狼人3",  # 狼人
        "预言家", "女巫", "猎人"    # 神职
    ]
    
    # 杀死所有好人
    for player in game.game_state.players:
        if player.role.role_type != RoleType.WEREWOLF:
            player.is_alive = False
    
    # 验证狼人胜利
    assert game.check_game_over() == "werewolf"
    
    # 重置游戏状态
    await game.initialize_game(player_names)
    
    # 杀死所有狼人
    for player in game.game_state.players:
        if player.role.role_type == RoleType.WEREWOLF:
            player.is_alive = False
    
    # 验证好人胜利
    assert game.check_game_over() == "villager"

@pytest.mark.asyncio
async def test_seer_check_visibility(game: GameController):
    """测试预言家查验信息的可见性"""
    # 获取预言家和其他玩家
    seer = get_player_by_role(game, RoleType.SEER)
    villager = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)

    # 运行夜晚阶段并更新游戏状态
    await game.next_phase()  # 这会运行夜晚阶段并更新游戏状态

    # 获取预言家可见的事件
    seer_events = game.get_player_events(seer.id)
    seer_check_events = [e for e in seer_events if "你查验了" in e]

    # 获取普通村民可见的事件
    villager_events = game.get_player_events(villager.id)
    villager_check_events = [e for e in villager_events if "预言家查验了" in e]


    # 验证预言家能看到查验信息
    assert len(seer_check_events) == 1
    # 验证普通村民不能看到查验结果
    assert len(villager_check_events) == 0

@pytest.mark.asyncio
async def test_first_night_seer_check(game: GameController):
    """测试第一天晚上预言家的查验是否正确记录在日志中"""
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证日志文件中的预言家查验记录
    with open(game.game_output_file.name, 'r', encoding='utf-8') as f:
        log_text = f.read()
        # 确保日志中包含预言家查验信息
        assert "预言家行动阶段:" in log_text
        assert "预言家查验了" in log_text
        assert "是好人" in log_text or "是狼人" in log_text 

@pytest.mark.asyncio
async def test_witch_save_mechanics(game: GameController):
    """测试女巫救人机制"""
    # 获取女巫和其他玩家
    witch = get_player_by_role(game, RoleType.WITCH)
    villager = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)
    
    # 场景1：第一夜女巫自救
    # 设置女巫被狼人杀死
    game.game_state._last_night_killed = witch.id
    game.game_state._witch_potions[witch.id] = {"save": True, "poison": True}
    game.game_state.round_number = 0  # 第一夜
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证女巫存活（被自救）
    assert witch.is_alive  # 因为被救了所以应该存活
    assert witch.death_reason is None  # 没有死亡原因
    assert game.game_state._witch_potions[witch.id]["save"] is False  # 解药已使用
    
    # 场景2：非第一夜女巫不能自救
    await game.initialize_game(["村民1", "村民2", "村民3", "狼人1", "狼人2", "狼人3", "预言家", "女巫", "猎人"])
    witch = get_player_by_role(game, RoleType.WITCH)
    game.game_state._last_night_killed = witch.id
    game.game_state._witch_potions[witch.id] = {"save": True, "poison": True}
    game.game_state.round_number = 1  # 非第一夜
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证女巫死亡（不能自救）
    assert not witch.is_alive
    assert witch.death_reason == "werewolf"
    assert game.game_state._witch_potions[witch.id]["save"] is True  # 解药未使用
    
    # 场景3：女巫救其他玩家
    await game.initialize_game(["村民1", "村民2", "村民3", "狼人1", "狼人2", "狼人3", "预言家", "女巫", "猎人"])
    witch = get_player_by_role(game, RoleType.WITCH)
    villager = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)
    game.game_state._last_night_killed = villager.id
    game.game_state._witch_potions[witch.id] = {"save": True, "poison": True}
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证村民存活（被救）
    assert villager.is_alive
    assert villager.death_reason is None
    assert game.game_state._witch_potions[witch.id]["save"] is False  # 解药已使用

@pytest.mark.asyncio
async def test_witch_poison_mechanics(game: GameController):
    """测试女巫毒药机制"""
    # 获取女巫和目标
    witch = get_player_by_role(game, RoleType.WITCH)
    target = next(p for p in game.game_state.players if p.role.role_type == RoleType.WEREWOLF)
    
    # 确保目标初始状态是存活的
    target.is_alive = True
    target.death_reason = None
    
    # 设置女巫有毒药
    game.game_state._witch_potions[witch.id] = {"save": False, "poison": True}
    
    # 记录毒药目标
    game.game_state._last_night_poisoned = target.id
    game.game_state._last_night_killed = None  # 确保没有狼人击杀
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证目标死亡
    assert not target.is_alive
    assert target.death_reason == "poison"
    assert game.game_state._witch_potions[witch.id]["poison"] is False  # 毒药已使用

@pytest.mark.asyncio
async def test_night_phase_death_timing(game: GameController):
    """测试夜晚阶段的死亡时机"""
    # 获取相关角色
    witch = get_player_by_role(game, RoleType.WITCH)
    werewolf = next(p for p in game.game_state.players if p.role.role_type == RoleType.WEREWOLF)
    villager = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)
    
    # 场景1：狼人击杀但被女巫救活
    game.game_state._last_night_killed = villager.id
    game.game_state._witch_potions[witch.id] = {"save": True, "poison": True}
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证村民存活
    assert villager.is_alive
    assert villager.death_reason is None
    
    # 场景2：狼人击杀和女巫毒人
    await game.initialize_game(["村民1", "村民2", "村民3", "狼人1", "狼人2", "狼人3", "预言家", "女巫", "猎人"])
    witch = get_player_by_role(game, RoleType.WITCH)
    villager1 = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER)
    villager2 = next(p for p in game.game_state.players if p.role.role_type == RoleType.VILLAGER and p.id != villager1.id)
    
    # 设置狼人击杀和女巫毒人
    game.game_state._last_night_killed = villager1.id
    game.game_state._last_night_poisoned = villager2.id
    game.game_state._witch_potions[witch.id] = {"save": False, "poison": True}
    
    # 运行夜晚阶段
    await game.run_night_phase()
    
    # 验证两个玩家都死亡，且死亡原因正确
    assert not villager1.is_alive
    assert villager1.death_reason == "werewolf"
    assert not villager2.is_alive
    assert villager2.death_reason == "poison" 