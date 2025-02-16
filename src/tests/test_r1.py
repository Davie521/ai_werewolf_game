import pytest
import asyncio
import os
from dotenv import load_dotenv
from ..controllers.game_controller import GameController
from ..models.game_state import GamePhase
from ..models.role import RoleType

# 加载环境变量
load_dotenv()

@pytest.fixture
def game():
    return GameController()

@pytest.mark.asyncio
async def test_r1_game():
    """测试使用 R1 模型的完整游戏流程"""
    game = GameController()
    
    # 初始化游戏
    player_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十", "郑十一"]
    await game.initialize_game(player_names)
    
    # 运行游戏直到结束
    game_over = False
    while not game_over:
        await game.next_phase()
        # 检查游戏是否结束
        game_over, _ = game.game_state.check_game_over()
    
    # 关闭日志文件
    if game.game_output_file:
        game.game_output_file.close()

if __name__ == "__main__":
    asyncio.run(test_r1_game()) 