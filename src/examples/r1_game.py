"""
使用 R1 模型的狼人杀游戏运行示例。
这个示例展示了如何使用更高级的 R1 模型来运行游戏。
"""

import asyncio
import os
from dotenv import load_dotenv
from ..controllers.game_controller import GameController
from ..models.game_state import GamePhase
from datetime import datetime

async def run_r1_game():
    """运行一个使用 R1 模型的狼人杀游戏示例"""
    # 初始化游戏控制器
    game = GameController()
    
    # 设置使用 R1 模型
    game.api_controller.set_model("r1")
    
    # 初始化玩家
    player_names = [
        "张三", "李四", "王五",  # 村民
        "赵六", "钱七", "孙八",  # 狼人
        "周九",  # 预言家
        "吴十",  # 女巫
        "郑十一"  # 猎人
    ]
    
    # 创建游戏日志
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"r1_game_log_{timestamp}.txt"
    print(f"游戏日志将保存到: {log_file}")
    
    game.game_output_file = open(log_file, "w", encoding="utf-8")
    game.write_to_log("=== 狼人杀游戏开始 (使用 R1 模型) ===\n")
    
    try:
        # 初始化游戏
        await game.initialize_game(player_names)
        
        # 打印初始游戏状态
        print("\n=== 游戏开始 ===")
        print("玩家角色分配：")
        for player in game.game_state.players:
            print(f"{player.name}: {player.role.role_type.value}")
        
        # 运行游戏直到结束
        while game.game_state.current_phase != GamePhase.GAME_OVER:
            print(f"\n=== 回合 {game.game_state.round_number + 1} ===")
            print(f"当前阶段: {game.game_state.current_phase.value}")
            
            # 执行当前阶段
            await game.next_phase()
            
            # 打印这个阶段的事件
            events = game.get_public_events(-10)
            print("\n本阶段事件：")
            for event in events:
                print(event)
            
            # 短暂暂停，便于观察
            await asyncio.sleep(2)
        
        # 打印游戏结果
        result = game.game_state.get_game_result()
        print("\n=== 游戏结束 ===")
        print(f"获胜阵营: {result['winning_team']}")
        print(f"总回合数: {result['rounds']}")
        
        print("\n存活玩家：")
        for player in result['alive_players']:
            print(f"{player['name']}({player['role']})")
        
        print("\n死亡玩家：")
        for player in result['dead_players']:
            print(f"{player['name']}({player['role']})")
            
    finally:
        # 确保关闭日志文件
        if game.game_output_file:
            game.game_output_file.close()

def main():
    # 加载环境变量
    load_dotenv()
    
    # 运行游戏
    asyncio.run(run_r1_game())

if __name__ == "__main__":
    main() 