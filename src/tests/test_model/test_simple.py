import asyncio
import os
from dotenv import load_dotenv
from src.controllers.game_controller import GameController
from src.models.game_state import GamePhase
from datetime import datetime

# 加载环境变量
load_dotenv()

async def test_game_flow():
    """测试完整游戏流程 (使用简单模型)"""
    # 初始化游戏控制器
    game = GameController()
    # 设置使用chat模型
    model_name = "deepseek-chat"
    game.api_controller.set_model(model_name)
    
    # 初始化玩家
    player_names = [
        "张三", "李四", "王五",  # 村民
        "赵六", "钱七", "孙八",  # 狼人
        "周九",  # 预言家
        "吴十",  # 女巫
        "郑十一"  # 猎人
    ]
    
    # 创建游戏日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    game.game_output_file = open(f"game_log_{timestamp}.txt", "w", encoding="utf-8")
    game.write_to_log(f"=== 使用模型: {model_name} ===\n")
    
    await game.initialize_game(player_names)
    
    # 打印初始游戏状态
    print("\n游戏开始！")
    print("玩家角色分配：")
    for player in game.game_state.players:
        print(f"{player.name}: {player.role.role_type.value}")
    
    # 运行游戏直到结束
    while game.game_state.current_phase != GamePhase.GAME_OVER:
        print(f"\n当前回合: {game.game_state.round_number + 1}")
        print(f"当前阶段: {game.game_state.current_phase.value}")
        
        # 执行当前阶段
        await game.next_phase()
        
        # 打印这个阶段的事件
        events = game.get_public_events(-10)  # 获取最近10条公开事件
        print("\n本阶段事件：")
        for event in events:
            print(event)
        
        # 等待一下，便于观察
        await asyncio.sleep(2)
    
    # 打印游戏结果
    result = game.game_state.get_game_result()
    print("\n游戏结束！")
    print(f"获胜阵营: {result['winning_team']}")
    print(f"总回合数: {result['rounds']}")
    print("\n存活玩家：")
    for player in result['alive_players']:
        print(f"{player['name']}({player['role']})")
    print("\n死亡玩家：")
    for player in result['dead_players']:
        print(f"{player['name']}({player['role']})")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_game_flow()) 