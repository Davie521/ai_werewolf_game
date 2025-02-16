from typing import List, Optional, Dict, Tuple
from ..models.game_state import GameState, GamePhase, WinningTeam
from ..models.player import Player
from ..models.role import Role, RoleType
from ..models.game_log import GameLog, GameEvent, GameEventType
from .api_controller import APIController
import random
import asyncio
from datetime import datetime

class GameController:
    def __init__(self, game_state: Optional[GameState] = None, api_controller: Optional[APIController] = None):
        self.game_state = game_state or GameState()
        self.game_log = GameLog()
        self.api_controller = api_controller or APIController()
        self.game_output_file = None
        
    async def initialize_game(self, player_names: List[str]):
        """初始化游戏，分配角色"""
        # 重置游戏状态
        self.game_state.reset()
        
        # 创建游戏日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_output_file = open(f"game_log_{timestamp}.txt", "w", encoding="utf-8")
        
        # 生成角色
        roles = self._generate_roles()
        
        # 分配角色给玩家
        for i, name in enumerate(player_names):
            role = roles[i]
            player = Player(i + 1, name, role)  # 使用1-based的玩家ID
            self.game_state.add_player(player)
        
        # 记录游戏开始事件
        self.game_log.add_event(GameEvent(
            GameEventType.GAME_START,
            {
                "player_count": len(player_names),
                "players": [{"id": i + 1, "name": name} for i, name in enumerate(player_names)]
            }
        ))
        
        # 按阵营分组显示玩家角色
        werewolves = [p for p in self.game_state.players if p.role.role_type == RoleType.WEREWOLF]
        villagers = [p for p in self.game_state.players if p.role.role_type == RoleType.VILLAGER]
        seer = next((p for p in self.game_state.players if p.role.role_type == RoleType.SEER), None)
        witch = next((p for p in self.game_state.players if p.role.role_type == RoleType.WITCH), None)
        hunter = next((p for p in self.game_state.players if p.role.role_type == RoleType.HUNTER), None)
        
        self.write_to_log("=== 游戏开始 ===")
        self.write_to_log("\n角色分配：")
        self.write_to_log(f"狼人阵营: {', '.join(w.name for w in werewolves)}")
        self.write_to_log(f"普通村民: {', '.join(v.name for v in villagers)}")
        self.write_to_log(f"预言家: {seer.name}")
        self.write_to_log(f"女巫: {witch.name}")
        self.write_to_log(f"猎人: {hunter.name}")
        
        self.write_to_log("\n玩家ID对照表：")
        for player in self.game_state.players:
            self.write_to_log(f"{player.name}: ID={player.id}, 角色={player.role.role_type.value}")
        
        self.write_to_log("=" * 30 + "\n")
    
    def write_to_log(self, message: str):
        """写入日志文件"""
        if self.game_output_file:
            self.game_output_file.write(message + "\n")
            self.game_output_file.flush()
            
    def _generate_roles(self) -> List[Role]:
        """生成角色分配"""
        roles = [
            Role(RoleType.WEREWOLF) for _ in range(3)  # 3个狼人
        ] + [
            Role(RoleType.VILLAGER) for _ in range(3)  # 3个平民
        ] + [
            Role(RoleType.SEER),     # 预言家
            Role(RoleType.WITCH),    # 女巫
            Role(RoleType.HUNTER)    # 猎人
        ]
        random.shuffle(roles)
        return roles
        
    async def run_night_phase(self):
        """运行夜晚阶段"""
        self.write_to_log(f"\n=== 第{self.game_state.round_number + 1}天夜晚 ===")
        self.game_log.add_event(GameEvent(
            GameEventType.PHASE_CHANGE,
            {"phase": "night", "round": self.game_state.round_number}
        ))
        
        # 记录夜晚开始时的死亡玩家列表
        initial_dead_players = set(p.id for p in self.game_state.players if not p.is_alive)
        
        # 狼人行动
        werewolves = [p for p in self.game_state.players if p.role.role_type == RoleType.WEREWOLF and p.is_alive]
        if werewolves:
            self.write_to_log("\n狼人行动阶段:")
            self.write_to_log(f"存活狼人: {', '.join(w.name for w in werewolves)}")
            
            # 获取每个狼人的选择
            self.write_to_log("-> 狼人开始决定击杀目标...")
            votes = {}
            for wolf in werewolves:
                self.write_to_log(f"-> {wolf.name} 正在决策中...")
                action = await self.api_controller.generate_night_action(wolf, self.game_state)
                if "werewolf_kill" in action and action["werewolf_kill"]["target_id"] is not None:
                    target_id = action["werewolf_kill"]["target_id"]
                    target = self.game_state.get_player_by_id(target_id)
                    if target:
                        self.write_to_log(f"-> {wolf.name} 选择击杀 {target.name}")
                        votes[target_id] = votes.get(target_id, 0) + 1
            
            # 确定最终击杀目标
            if votes:
                max_votes = max(votes.values())
                targets = [tid for tid, v in votes.items() if v == max_votes]
                target_id = random.choice(targets)
                target = self.game_state.get_player_by_id(target_id)
                self.write_to_log(f"最终击杀目标: {target.name}")
                # 只记录击杀目标，不立即标记死亡
                self.game_state._night_actions["werewolf_kill"] = {"target_id": target_id}
                self.game_state._last_night_killed = target_id
                self.write_to_log("[DEBUG] 已记录狼人击杀目标到夜晚行动")
            else:
                self.write_to_log("狼人没有选择击杀目标")
        
        # 预言家行动
        seer = next((p for p in self.game_state.players if p.role.role_type == RoleType.SEER and p.is_alive), None)
        if seer:
            self.write_to_log("\n预言家行动阶段:")
            action = await self.api_controller.generate_night_action(seer, self.game_state)
            if "seer_check" in action and action["seer_check"]["target_id"] is not None:
                target_id = action["seer_check"]["target_id"]
                target = self.game_state.get_player_by_id(target_id)
                if target:
                    is_werewolf = target.role.role_type == RoleType.WEREWOLF
                    # 记录查验行为和结果到主持人日志
                    self.write_to_log(f"预言家查验了 {target.name}，Ta是{'狼人' if is_werewolf else '好人'}")
                    
                    # 记录查验结果（只对预言家可见）
                    check_result = f"你查验了 {target.name}，Ta是{'狼人' if is_werewolf else '好人'}"
                    self.game_log.add_event(GameEvent(
                        GameEventType.SEER_CHECK,
                        {
                            "player_id": seer.id,
                            "target_id": target.id,
                            "target_name": target.name,
                            "role": "狼人" if is_werewolf else "好人",
                            "message": check_result
                        },
                        public=False  # 查验结果是私密的
                    ))
                    
                    # 记录到游戏状态
                    self.game_state.record_night_action("seer_check", {"target_id": target.id})
                    # 记录查验结果到游戏状态
                    self.game_state._check_results[seer.id] = {
                        "player": target,
                        "role": "狼人" if is_werewolf else "好人"
                    }
                else:
                    self.write_to_log("预言家选择的目标无效")
            else:
                self.write_to_log("预言家没有选择查验目标")
        
        # 女巫行动
        witch = next((p for p in self.game_state.players if p.role.role_type == RoleType.WITCH and p.is_alive), None)
        if witch:
            self.write_to_log("\n女巫行动阶段:")
            self.write_to_log(f"[DEBUG] 女巫信息 - ID: {witch.id}, 名字: {witch.name}")
            
            # 获取女巫药水状态
            witch_potions = self.game_state.get_witch_potions(witch.id)
            self.write_to_log(f"[DEBUG] 女巫药水状态: 解药{'可用' if witch_potions['save'] else '已用'}, 毒药{'可用' if witch_potions['poison'] else '已用'}")
            
            # 获取今晚被杀的玩家
            killed_player = self.game_state.get_killed_player(witch.id)
            self.write_to_log(f"[DEBUG] 夜晚行动记录: {self.game_state._night_actions}")
            self.write_to_log(f"[DEBUG] 今晚被杀玩家: {killed_player.name if killed_player else '无'}")
            
            action = await self.api_controller.generate_night_action(witch, self.game_state)
            if "witch_save" in action:
                if action["witch_save"]["used"]:
                    target_id = self.game_state._last_night_killed
                    target = self.game_state.get_player_by_id(target_id)
                    # 检查是否是女巫自救
                    is_self_save = target and target.id == witch.id
                    # 第一夜可以自救，之后不能自救
                    if is_self_save and self.game_state.round_number > 0:
                        self.write_to_log("女巫不能在第一夜之后自救")
                    elif target:  # 只要目标存在就可以救
                        self.game_state._last_night_saved = True  # 标记已被救活
                        # 只在主持人日志中记录
                        self.write_to_log(f"女巫使用解药救活了 {target.name}")
                        # 记录救人结果（只对女巫可见）
                        self.game_log.add_event(GameEvent(
                            GameEventType.WITCH_SAVE,
                            {
                                "player_id": witch.id,
                                "target_id": target_id,
                                "target_name": target.name,
                                "message": "你使用解药救活了一名玩家"
                            },
                            public=False
                        ))
                        # 更新女巫的药水状态
                        self.game_state._witch_potions[witch.id]["save"] = False
                else:
                    self.write_to_log("女巫没有使用解药")
            
            if "witch_poison" in action and action["witch_poison"]["target_id"] is not None:
                target_id = action["witch_poison"]["target_id"]
                target = self.game_state.get_player_by_id(target_id)
                if target and target.is_alive:
                    # 记录毒药目标，不立即标记死亡
                    self.game_state._last_night_poisoned = target_id
                    # 更新女巫的毒药状态
                    self.game_state._witch_potions[witch.id]["poison"] = False
                    # 只在主持人日志中记录
                    self.write_to_log(f"女巫使用毒药毒死了 {target.name}")
                    # 记录毒人结果（只对女巫可见）
                    self.game_log.add_event(GameEvent(
                        GameEventType.WITCH_POISON,
                        {
                            "player_id": witch.id,
                            "target_id": target_id,
                            "target_name": target.name,
                            "message": "你使用毒药毒死了一名玩家"
                        },
                        public=False
                    ))
            else:
                self.write_to_log("女巫没有使用毒药")
        
        # 处理夜晚新死亡的玩家
        current_dead_players = set(p.id for p in self.game_state.players if not p.is_alive)
        new_dead_players = [p for p in self.game_state.players if p.id in (current_dead_players - initial_dead_players)]
        
        # 如果没有被女巫救活，则标记狼人击杀的目标死亡
        if self.game_state._last_night_killed and not self.game_state._last_night_saved:
            killed_player = self.game_state.get_player_by_id(self.game_state._last_night_killed)
            if killed_player and killed_player.is_alive:
                killed_player.is_alive = False
                killed_player.death_reason = "werewolf"
                new_dead_players.append(killed_player)
        
        # 处理被毒死的玩家
        if self.game_state._last_night_poisoned:
            poisoned_player = self.game_state.get_player_by_id(self.game_state._last_night_poisoned)
            if poisoned_player and poisoned_player.is_alive:
                poisoned_player.is_alive = False
                poisoned_player.death_reason = "poison"
                new_dead_players.append(poisoned_player)
        
        if new_dead_players:
            self.write_to_log("\n今晚死亡的玩家:")
            for player in new_dead_players:
                self.write_to_log(f"- {player.name} ({player.role.role_type.value})")
                await self._handle_player_death(player)
        else:
            self.write_to_log("\n今晚是平安夜，没有玩家死亡")
        
        self.write_to_log("=" * 30)
    
    async def run_day_phase(self):
        """运行白天阶段"""
        self.write_to_log(f"\n=== 第{self.game_state.round_number + 1}天白天 ===")
        self.game_log.add_event(GameEvent(
            GameEventType.PHASE_CHANGE,
            {"phase": "day", "round": self.game_state.round_number}
        ))
        
        # 公布昨晚死亡情况
        dead_players = self.game_state.get_last_night_dead_players()
        if dead_players:
            self.write_to_log("\n昨晚死亡的玩家：")
            for player in dead_players:
                self.write_to_log(f"- {player.name} ({player.role.role_type.value})")
                self.game_log.add_event(GameEvent(
                    GameEventType.PLAYER_DEATH,
                    {
                        "player_id": player.id,
                        "player_name": player.name,
                        "role": player.role.role_type.value,
                        "role_revealed": True
                    }
                ))
        else:
            self.write_to_log("\n昨晚是平安夜，没有玩家死亡")
            self.game_log.add_event(GameEvent(
                GameEventType.PLAYER_DEATH,
                {"message": "昨晚是平安夜"}
            ))
        
        self.write_to_log("")  # 添加空行分隔
        
        # 进行讨论
        await self.run_discussion()
    
    async def run_vote_phase(self):
        """运行投票阶段"""
        self.write_to_log("\n=== 投票阶段 ===")
        self.game_log.add_event(GameEvent(
            GameEventType.PHASE_CHANGE,
            {"phase": "vote", "round": self.game_state.round_number}
        ))
        
        # 获取每个玩家的投票
        alive_players = self.game_state.get_alive_players()
        for player in alive_players:
            vote_response = await self.api_controller.generate_vote(player, self.game_state)
            target_id = None
            
            if isinstance(vote_response, dict) and vote_response.get("type") == "vote":
                target_id = vote_response.get("target_id")
            else:
                target_id = vote_response  # 兼容旧的返回格式
                
            if target_id is not None and target_id != -1:
                self.game_state.record_vote(player.id, target_id)  # 直接记录到game_state
                self.record_vote(player.id, target_id)  # 记录到日志
        
        # 统计投票结果
        vote_count = {}  # target_id -> [voter_names]
        for voter_id, target_id in self.game_state.votes.items():
            voter = self.game_state.get_player_by_id(voter_id)
            if voter:
                if target_id not in vote_count:
                    vote_count[target_id] = []
                vote_count[target_id].append(voter.name)
        
        # 按得票数排序并显示结果
        self.write_to_log("\n投票统计：")
        sorted_votes = sorted(vote_count.items(), key=lambda x: len(x[1]), reverse=True)
        for target_id, voters in sorted_votes:
            target = self.game_state.get_player_by_id(target_id)
            if target:
                self.write_to_log(f"投给 {target.name} 的有：{', '.join(voters)} ({len(voters)}票)")
        
        # 处理投票结果
        voted_player, is_tie = self.game_state.process_vote()
        
        # 记录最终结果
        self.write_to_log("\n投票结果：")
        if is_tie:
            self.write_to_log("平票，没有玩家被放逐")
            # 添加投票结果事件
            self.game_log.add_event(GameEvent(
                GameEventType.VOTE_RESULT,
                {"is_tie": True}
            ))
        elif voted_player:
            self.write_to_log(f"{voted_player.name} 被放逐")
            # 添加投票结果事件
            self.game_log.add_event(GameEvent(
                GameEventType.VOTE_RESULT,
                {
                    "is_tie": False,
                    "voted_name": voted_player.name,
                    "voted_id": voted_player.id,
                    "role": voted_player.role.role_type.value
                }
            ))
            
            # 获取并记录遗言
            self.write_to_log("\n遗言：")
            last_words = await self.api_controller.generate_discussion(voted_player, self.game_state)
            self.write_to_log(f"{voted_player.name}：{last_words}")
            
            # 记录遗言事件
            self.game_log.add_event(GameEvent(
                GameEventType.PLAYER_SPEAK,
                {
                    "player_id": voted_player.id,
                    "player_name": voted_player.name,
                    "message": last_words,
                    "is_last_words": True
                }
            ))
            
            # 处理玩家死亡
            await self._handle_player_death(voted_player)
            
            # 如果被放逐的是猎人，给他开枪的机会
            if voted_player.role.role_type == RoleType.HUNTER:
                self.write_to_log("\n猎人开枪阶段：")
                
                # 获取猎人的开枪目标
                shot_target = await self.api_controller.generate_night_action(voted_player, self.game_state)
                if "hunter_shot" in shot_target and shot_target["hunter_shot"]["target_id"] is not None:
                    target_id = shot_target["hunter_shot"]["target_id"]
                    if await self.handle_hunter_shot(voted_player.id, target_id):
                        target = self.game_state.get_player_by_id(target_id)
                        self.write_to_log(f"猎人开枪带走了 {target.name}")
        
        self.write_to_log("=" * 30)
    
    async def _handle_player_death(self, player: Player):
        """处理玩家死亡"""
        # 记录死亡事件
        self.game_log.add_event(GameEvent(
            GameEventType.PLAYER_DEATH,
            {
                "player_id": player.id,
                "player_name": player.name,
                "role": player.role.role_type.value,
                "role_revealed": True
            }
        ))
        
        # 如果是猎人，立即处理开枪
        if player.role.role_type == RoleType.HUNTER:
            self.write_to_log(f"\n猎人 {player.name} 开枪阶段：")
            # 获取猎人的开枪目标
            shot_target = await self.api_controller.generate_night_action(player, self.game_state)
            if "hunter_shot" in shot_target and shot_target["hunter_shot"]["target_id"] is not None:
                target_id = shot_target["hunter_shot"]["target_id"]
                if await self.handle_hunter_shot(player.id, target_id):
                    target = self.game_state.get_player_by_id(target_id)
                    self.write_to_log(f"猎人开枪带走了 {target.name}")
    
    async def handle_hunter_shot(self, hunter_id: int, target_id: int) -> bool:
        """处理猎人开枪
        
        Args:
            hunter_id: 猎人ID
            target_id: 目标玩家ID
            
        Returns:
            bool: 是否成功处理猎人开枪
        """
        # 获取猎人和目标
        hunter = self.game_state.get_player_by_id(hunter_id)
        target = self.game_state.get_player_by_id(target_id)
        
        # 验证猎人身份和状态
        if not hunter or hunter.role.role_type != RoleType.HUNTER:
            self.write_to_log("无效的猎人ID")
            return False
            
        # 验证猎人是否已死亡
        if hunter.is_alive:
            self.write_to_log(f"猎人 {hunter.name} 还活着，不能开枪")
            return False
            
        # 检查死亡原因
        if hunter.death_reason == "poison":
            self.write_to_log(f"猎人 {hunter.name} 被毒死，无法开枪")
            return False
            
        # 验证目标是否有效
        if not target:
            self.write_to_log("无效的目标ID")
            return False
            
        # 验证目标是否存活
        if not target.is_alive:
            self.write_to_log(f"目标 {target.name} 已经死亡")
            return False
            
        # 执行猎人开枪
        target.is_alive = False
        target.death_reason = "hunter_shot"
        
        # 记录事件
        self.game_log.add_event(GameEvent(
            GameEventType.HUNTER_SHOT,
            {
                "hunter_id": hunter_id,
                "hunter_name": hunter.name,
                "target_id": target_id,
                "target_name": target.name
            }
        ))
        
        self.write_to_log(f"猎人 {hunter.name} 开枪击杀了 {target.name}")
        return True
    
    def record_vote(self, voter_id: int, target_id: int):
        """记录投票"""
        voter = self.game_state.get_player_by_id(voter_id)
        target = self.game_state.get_player_by_id(target_id)
        
        if voter and target:
            self.game_state.record_vote(voter_id, target_id)
            self.game_log.add_event(GameEvent(
                GameEventType.PLAYER_VOTE,
                {
                    "voter_id": voter_id,
                    "voter_name": voter.name,
                    "target_id": target_id,
                    "target_name": target.name
                }
            ))
            # 写入文件
            self.write_to_log(f"投票: {voter.name} -> {target.name}")
    
    def record_player_speech(self, player_id: int, message: str):
        """记录玩家发言"""
        player = self.game_state.get_player_by_id(player_id)
        if player:
            # 记录到游戏日志
            self.game_log.add_event(GameEvent(
                GameEventType.PLAYER_SPEAK,
                {
                    "player_id": player_id,
                    "player_name": player.name,
                    "message": message
                }
            ))
            # 写入文件
            self.write_to_log(f"{player.name}: {message}")
    
    async def next_phase(self):
        """进入下一个游戏阶段"""
        current_phase = self.game_state.current_phase
        
        if current_phase == GamePhase.NIGHT:
            await self.run_night_phase()
        elif current_phase == GamePhase.DAY:
            await self.run_day_phase()
        elif current_phase == GamePhase.VOTE:
            await self.run_vote_phase()
        
        # 检查游戏是否结束
        game_over, winning_team = self.game_state.check_game_over()
        if game_over:
            self.write_to_log("\n=== 游戏结束 ===")
            self.write_to_log(f"获胜阵营: {winning_team.value}")
            self.write_to_log(f"总回合数: {self.game_state.round_number}")
            
            alive_players = self.game_state.get_alive_players()
            self.write_to_log("\n存活玩家：")
            for player in alive_players:
                self.write_to_log(f"{player.name}({player.role.role_type.value})")
            
            dead_players = [p for p in self.game_state.players if not p.is_alive]
            self.write_to_log("\n死亡玩家：")
            for player in dead_players:
                self.write_to_log(f"{player.name}({player.role.role_type.value})")
            
            # 关闭日志文件
            if self.game_output_file:
                self.game_output_file.close()
                self.game_output_file = None
        
        # 进入下一个阶段
        self.game_state.next_phase()
    
    def get_player_events(self, player_id: int, start_index: int = 0) -> List[str]:
        """获取玩家可见的事件记录"""
        self.write_to_log(f"[DEBUG] 获取玩家 {player_id} 的事件，当前事件总数: {len(self.game_log._events)}")
        events = self.game_log.get_player_events(player_id, start_index)
        formatted_events = [self.game_log.format_event(event) for event in events]
        self.write_to_log(f"[DEBUG] 玩家 {player_id} 可见事件数: {len(formatted_events)}")
        return formatted_events
    
    def get_public_events(self, start_index: int = 0) -> List[str]:
        """获取公开事件记录"""
        events = self.game_log.get_public_events(start_index)
        return [self.game_log.format_event(event) for event in events]
    
    async def run_discussion(self):
        """运行讨论阶段"""
        alive_players = self.game_state.get_alive_players()
        for player in alive_players:
            # 获取玩家发言
            message = await self.api_controller.generate_discussion(player, self.game_state)
            
            # 记录发言
            self.record_player_speech(player.id, message)
            
            # 等待一小段时间，模拟真实对话节奏
            await asyncio.sleep(1)

    def check_game_over(self) -> str:
        """检查游戏是否结束
        
        Returns:
            str: 获胜阵营，"werewolf" 表示狼人胜利，"villager" 表示好人胜利，None 表示游戏未结束
        """
        werewolves = [p for p in self.game_state.players if p.role.role_type == RoleType.WEREWOLF and p.is_alive]
        villagers = [p for p in self.game_state.players if p.role.role_type != RoleType.WEREWOLF and p.is_alive]
        
        if not werewolves:
            return "villager"  # 所有狼人死亡，好人胜利
        elif len(werewolves) >= len(villagers):
            return "werewolf"  # 狼人数量大于等于好人，狼人胜利
        return None  # 游戏继续

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """通过名字获取玩家"""
        return next((p for p in self.game_state.players if p.name == name), None) 