"""
简单的狼人杀游戏运行示例。
使用 deepseek-chat 模型进行游戏流程的演示。
"""

import asyncio
import os
from dotenv import load_dotenv
from ..controllers.game_controller import GameController
from ..models.game_state import GamePhase
from datetime import datetime

async def run_simple_game():
    """运行一个简单的狼人杀游戏示例"""
    # 初始化游戏控制器
    game = GameController()
    
    # 设置使用的模型
    game.api_controller.set_model("deepseek-chat")
    
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
    log_file = f"simple_game_log_{timestamp}.txt"
    print(f"游戏日志将保存到: {log_file}")
    
    game.game_output_file = open(log_file, "w", encoding="utf-8")
    game.write_to_log(f"=== 狼人杀游戏开始 (使用模型: deepseek-chat) ===\n")
    
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
            events = game.get_public_events(1)  # 只获取最近的1个事件
            if events:
                print("\n本阶段事件：")
                for event in events:
                    print(event)
            
            # 如果是讨论阶段，显示玩家发言
            if game.game_state.current_phase == GamePhase.DISCUSSION:
                print("\n玩家发言：")
                for player in game.game_state.get_alive_players():
                    # 获取玩家发言
                    speech = await game.api_controller.generate_discussion(
                        player,
                        game.game_state
                    )
                    if speech:
                        print(f"{player.name}: {speech}")
            
            # 短暂暂停，便于观察
            await asyncio.sleep(2)
        
        # 打印游戏结果
        result = game.game_state.get_game_result()
        print("\n=== 游戏结束 ===")
        print(f"获胜阵营: {result['winning_team']}")
        print(f"总回合数: {result['rounds']}")
        
        print("\n存活玩家：")
        for player in game.game_state.get_alive_players():
            print(f"{player.name}({player.role.role_type.value})")
        
        print("\n死亡玩家：")
        dead_players = [p for p in game.game_state.players if not p.is_alive]
        for player in dead_players:
            print(f"{player.name}({player.role.role_type.value}) - 死因: {player.death_reason}")
            
    finally:
        # 确保关闭日志文件
        if game.game_output_file:
            game.game_output_file.close()

def main():
    # 加载环境变量
    load_dotenv()
    
    # 运行游戏
    asyncio.run(run_simple_game())

if __name__ == "__main__":
    main() 