from typing import List, Dict, Optional
from ..models.player import Player
from ..models.roles.base_role import RoleType
from ..models.game_state import GameState, GamePhase
from openai import OpenAI
import json
import os
import asyncio
import sys
import time

class APIController:
    def __init__(self, model_name="deepseek-r1"):
        self.system_prompts = self._init_role_prompts()
        self._loading_task = None
        self._player_sessions = {}  # 存储每个玩家的独立 session
        self.model_name = model_name  # 新增：模型选择
        
    def _init_role_prompts(self) -> Dict[RoleType, str]:
        """初始化每个角色的系统提示词"""
        return {
            RoleType.WEREWOLF: """你正在参与一个狼人杀游戏。这是一个推理策略游戏，玩家分为两个阵营：狼人阵营和好人阵营。

                                 游戏规则：
                                 1. 游戏分为白天和黑夜两个阶段交替进行
                                 2. 每个夜晚：
                                    - 狼人可以选择一名玩家击杀
                                    - 预言家可以查验一名玩家的真实身份
                                    - 女巫可以使用解药救人或使用毒药杀人（每种药只能用一次）
                                 3. 每个白天：
                                    - 公布夜晚死亡情况
                                    - 所有玩家依次发言，讨论信息
                                    - 所有玩家投票，得票最多的玩家被放逐
                                 4. 胜利条件：
                                    - 狼人阵营：杀死所有好人
                                    - 好人阵营：杀死所有狼人
                                 
                                 你的角色是狼人，属于狼人阵营。
                                 目标：与其他狼人合作，淘汰所有好人阵营。
                                 
                                 狼人战术指南：
                                 1. 刀法精准：优先击杀女巫、预言家，后期刀猎人/关键平民
                                 2. 发言统一：与狼队提前约定验人逻辑，避免内部矛盾
                                 3. 悍跳战术：
                                    - 可以直接对跳预言家，扰乱好人视野
                                    - 编造首夜验人结果，攻击真预言家"验人无收益"
                                    - 其他狼人要统一站边悍跳狼
                                 4. 倒钩战术：
                                    - 假意支持真预言家，暗中篡改验人信息
                                    - 在关键轮次反水归票真预言家
                                 5. 深水战术：
                                    - 发言保持中立，装作跟票平民
                                    - 决赛轮可跳神职抢夺归票权
                                 6. 煽动战术：
                                    - 假扮激进好人，攻击可疑玩家
                                    - 利用位置学带偏好人思路
                                 
                                 记住：悍跳要真，倒钩要深，刀法要狠，发言要稳！""",
            
            RoleType.VILLAGER: """你正在参与一个狼人杀游戏。这是一个推理策略游戏，玩家分为两个阵营：狼人阵营和好人阵营。

                                 游戏规则：
                                 1. 游戏分为白天和黑夜两个阶段交替进行
                                 2. 每个夜晚：
                                    - 狼人可以选择一名玩家击杀
                                    - 预言家可以查验一名玩家的真实身份
                                    - 女巫可以使用解药救人或使用毒药杀人（每种药只能用一次）
                                 3. 每个白天：
                                    - 公布夜晚死亡情况
                                    - 所有玩家依次发言，讨论信息
                                    - 所有玩家投票，得票最多的玩家被放逐
                                 4. 胜利条件：
                                    - 狼人阵营：杀死所有好人
                                    - 好人阵营：杀死所有狼人
                                 
                                 你的角色是普通村民，属于好人阵营。
                                 目标：与其他好人合作，找出并淘汰所有狼人。
                                 
                                 平民战术指南：
                                 1. 发言策略：
                                    - 可以尝试穿神职衣服（如假跳预言家）
                                    - 大胆发表意见，敢于质疑可疑玩家
                                    - 记录并分析玩家投票一致性
                                 2. 逻辑分析：
                                    - 关注多次弃票或跟风的玩家
                                    - 注意发言矛盾或态度反复的人
                                 3. 团队配合：
                                    - 支持可信的神职玩家
                                    - 通过互保形成信任链
                                    - 在神职死亡后主动带队归票
                                 4. 防守意识：
                                    - 避免过于激进被狼人针对
                                    - 保持中立直到获得确切信息
                                 
                                 记住：敢穿敢保，敢踩敢票，活着是盾，死了是矛！""",
            
            RoleType.SEER: """你正在参与一个狼人杀游戏。这是一个推理策略游戏，玩家分为两个阵营：狼人阵营和好人阵营。

                             游戏规则：
                             1. 游戏分为白天和黑夜两个阶段交替进行
                             2. 每个夜晚：
                                - 狼人可以选择一名玩家击杀
                                - 预言家可以查验一名玩家的真实身份
                                - 女巫可以使用解药救人或使用毒药杀人（每种药只能用一次）
                             3. 每个白天：
                                - 公布夜晚死亡情况
                                - 所有玩家依次发言，讨论信息
                                - 所有玩家投票，得票最多的玩家被放逐
                             4. 胜利条件：
                                - 狼人阵营：杀死所有好人
                                - 好人阵营：杀死所有狼人
                             
                             你的角色是预言家，属于好人阵营。
                             目标：帮助村民找出并淘汰狼人，但要注意保护自己。
                             
                             预言家战术指南：
                             1. 验人策略：
                                - 首夜优先验发言可疑的玩家
                                - 次夜验证关键发言者或神职玩家
                                - 避免重复验证同一条线的玩家
                             2. 身份保护：
                                - 考虑隐藏身份到第二夜
                                - 避免首夜被刀导致信息断层
                             3. 信息传递：
                                - 明确公开验人结果和顺序
                                - 避免被狼人混淆验人信息
                                - 用清晰的逻辑串联验人结果
                             4. 带队技巧：
                                - 及时归票确认的狼人
                                - 保护验出的好人玩家
                                - 引导队伍关注可疑目标
                             
                             记住：首验抓狼，次验保民，发言要硬，信息要清！""",
            
            RoleType.WITCH: """你正在参与一个狼人杀游戏。这是一个推理策略游戏，玩家分为两个阵营：狼人阵营和好人阵营。

                             游戏规则：
                             1. 游戏分为白天和黑夜两个阶段交替进行
                             2. 每个夜晚：
                                - 狼人可以选择一名玩家击杀
                                - 预言家可以查验一名玩家的真实身份
                                - 女巫可以使用解药救人或使用毒药杀人（每种药只能用一次）
                             3. 每个白天：
                                - 公布夜晚死亡情况
                                - 所有玩家依次发言，讨论信息
                                - 所有玩家投票，得票最多的玩家被放逐
                             4. 胜利条件：
                                - 狼人阵营：杀死所有好人
                                - 好人阵营：杀死所有狼人
                             
                             你的角色是女巫，属于好人阵营。
                             目标：帮助村民找出并淘汰狼人，合理使用药水。
                             
                             女巫战术指南：
                             1. 解药使用：
                                - 首夜考虑自救（防首刀）
                                - 优先救预言家（保证至少两夜验人）
                                - 若未自救则隐藏身份观察刀法
                             2. 毒药策略：
                                - 不要轻易使用，等待关键时机
                                - 针对发言矛盾或跟风站队的玩家
                                - 可以毒掉确认的狼人
                             3. 身份保护：
                                - 尽量隐藏身份直到使用药水
                                - 观察狼人刀法判断用药时机
                             4. 发言技巧：
                                - 装作普通平民发言
                                - 暗中保护可信好人
                                - 用毒药威慑可疑玩家
                             
                             记住：首夜自救，毒药慢用，装民到底，毒狼无形！""",
            
            RoleType.HUNTER: """你正在参与一个狼人杀游戏。这是一个推理策略游戏，玩家分为两个阵营：狼人阵营和好人阵营。

                               游戏规则：
                               1. 游戏分为白天和黑夜两个阶段交替进行
                               2. 每个夜晚：
                                  - 狼人可以选择一名玩家击杀
                                  - 预言家可以查验一名玩家的真实身份
                                  - 女巫可以使用解药救人或使用毒药杀人（每种药只能用一次）
                               3. 每个白天：
                                  - 公布夜晚死亡情况
                                  - 所有玩家依次发言，讨论信息
                                  - 所有玩家投票，得票最多的玩家被放逐
                               4. 胜利条件：
                                  - 狼人阵营：杀死所有好人
                                  - 好人阵营：杀死所有狼人
                               
                               你的角色是猎人，属于好人阵营。
                               目标：帮助村民找出并淘汰狼人，注意开枪时机。
                               
                               猎人战术指南：
                               1. 身份策略：
                                  - 残局阶段再跳身份归票
                                  - 避免过早暴露被狼人针对
                                  - 可以暗跳钓鱼，伪装平民
                               2. 开枪时机：
                                  - 被投票出局时翻牌反杀
                                  - 被狼人击杀时带走嫌疑人
                                  - 优先射杀划水不站队的玩家
                               3. 威慑作用：
                                  - 利用开枪威胁压制狼人
                                  - 保护关键好人免受伤害
                               4. 发言技巧：
                                  - 暗中观察可疑玩家
                                  - 记录反复倒票的玩家
                                  - 为开枪目标收集证据
                               
                               记住：明跳控场，暗藏追刀，枪口指狼，一换一高！"""
        }
    
    def _get_player_session(self, player_id: int) -> OpenAI:
        """获取或创建玩家的独立 session"""
        if player_id not in self._player_sessions:
            self._player_sessions[player_id] = OpenAI(
                base_url='https://tbnx.plus7.plus/v1',
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                timeout=120.0
            )
        return self._player_sessions[player_id]
    
    def set_model(self, model_name: str):
        """设置使用的模型"""
        if model_name not in ["deepseek-r1", "deepseek-chat"]:
            raise ValueError("不支持的模型类型。只支持 deepseek-r1 和 deepseek-chat")
        self.model_name = model_name
    
    async def generate_night_action(self, player: Player, game_state: GameState) -> Dict:
        """生成夜晚行动决策"""
        context = self._build_game_context(game_state, player)
        
        if player.role.role_type == RoleType.WEREWOLF:
            prompt = self._build_werewolf_prompt(game_state)
        elif player.role.role_type == RoleType.SEER:
            prompt = self._build_seer_prompt(game_state)
        elif player.role.role_type == RoleType.WITCH:
            prompt = self._build_witch_prompt(game_state)
        else:
            return {}  # 其他角色夜晚无行动
            
        response = await self._call_api(prompt, context, player)
        return self._parse_night_action(response, player.role.role_type)
    
    async def generate_discussion(self, player: Player, game_state: GameState) -> str:
        """生成白天讨论发言"""
        context = self._build_game_context(game_state, player)
        prompt = self._build_discussion_prompt(game_state, player)
        
        response = await self._call_api(prompt, context, player)
        return self._parse_discussion(response)
    
    async def generate_vote(self, player: Player, game_state: GameState) -> int:
        """生成投票决策"""
        context = self._build_game_context(game_state, player)
        prompt = self._build_vote_prompt(game_state)
        
        response = await self._call_api(prompt, context, player)
        return self._parse_vote(response, game_state)
    
    def _build_game_context(self, game_state: GameState, player: Player) -> str:
        """构建游戏上下文信息"""
        alive_players = game_state.get_alive_players()
        context = f"""
        当前游戏状态:
        - 回合数: {game_state.round_number}
        - 存活玩家: {[p.name for p in alive_players]}
        - 你的角色: {player.role.role_type.value}
        - 历史对话: {self._format_chat_history(game_state)}
        """
        return context
    
    async def _show_loading_animation(self):
        """显示加载动画"""
        animation = "|/-\\"
        idx = 0
        while True:
            print(f"\r    思考中... {animation[idx % len(animation)]}", end="")
            sys.stdout.flush()
            idx += 1
            await asyncio.sleep(0.1)
    
    async def _start_loading(self):
        """开始显示加载动画"""
        self._loading_task = asyncio.create_task(self._show_loading_animation())
    
    async def _stop_loading(self):
        """停止加载动画"""
        if self._loading_task:
            self._loading_task.cancel()
            try:
                await self._loading_task
            except asyncio.CancelledError:
                pass
            print("\r" + " " * 20 + "\r", end="")  # 清除加载动画
            sys.stdout.flush()
    
    async def _call_api(self, prompt: str, context: str, player: Player) -> str:
        """调用DeepSeek API"""
        try:
            print(f"\n[API] {player.name} ({player.role.role_type.value}) 正在思考...")
            
            await self._start_loading()
            client = self._get_player_session(player.id)
            system_prompt = self.system_prompts[player.role.role_type]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        wait_time = attempt * 5
                        print(f"[API] 等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                    
                    completion = client.chat.completions.create(
                        model=self.model_name,  # 使用选定的模型
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"{context}\n{prompt}"}
                        ],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    response = completion.choices[0].message.content.strip()
                    
                    # 根据不同模型处理响应
                    if self.model_name == "deepseek-r1":
                        # R1模型会返回<think>标签
                        if "<think>" in response:
                            think_parts = response.split("</think>")
                            if len(think_parts) > 1:
                                think_content = think_parts[0].replace("<think>", "").strip()
                                print(f"[API] {player.name} 的想法: {think_content}")
                                response = think_parts[1].strip()
                    else:
                        # Chat模型直接返回结果，不需要特殊处理
                        print(f"[API] {player.name} 的响应: {response}")
                    
                    # 尝试找到JSON对象
                    json_start = response.rfind("{")
                    json_end = response.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        try:
                            json.loads(json_str)  # 验证JSON是否有效
                            await self._stop_loading()
                            print(f"[API] {player.name} 做出了决定。")
                            return json_str
                        except json.JSONDecodeError:
                            pass
                    
                    if attempt < max_retries - 1:
                        print(f"[API] {player.name} 的响应格式不正确,重试中...")
                        continue
                    
                    # 最后一次尝试使用更直接的提示
                    print(f"[API] 最后一次尝试使用简化提示...")
                    completion = client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "请直接返回JSON格式的决策"},
                            {"role": "user", "content": prompt.split('请用以下格式返回：')[1]}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    response = completion.choices[0].message.content.strip()
                    print(f"[API] {player.name} 最终做出决定。")
                    
                    await self._stop_loading()
                    return response
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"[API] {player.name} 的第{attempt + 1}次尝试失败: {error_msg}")
                    
                    if "timeout" in error_msg.lower():
                        print("[API] 超时错误，将在重试前等待更长时间...")
                    elif "rate limit" in error_msg.lower():
                        print("[API] 速率限制，将在重试前等待更长时间...")
                    
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print("[API] 已达到最大重试次数，返回空响应")
            
            return "{}"
            
        except Exception as e:
            await self._stop_loading()
            print(f"[API] {player.name} 出错: {str(e)}")
            return "{}"
    
    def _parse_night_action(self, response: str, role_type: RoleType) -> Dict:
        """解析夜晚行动响应"""
        try:
            if not response:
                print("[API] 警告: 响应为空")
                return {}
            
            # 尝试从响应中提取 JSON 部分
            try:
                # 如果响应中包含思考过程，只取最后的 JSON 部分
                if "<think>" in response:
                    response = response[response.rfind("</think>") + 8:].strip()
                
                # 查找最后一个 JSON 对象
                json_start = response.rfind("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    action = json.loads(json_str)
                else:
                    print("[API] 警告: 未找到JSON响应")
                    return {}
            except json.JSONDecodeError as e:
                print(f"[API] JSON解析错误: {str(e)}")
                print(f"[API] 原始响应: {response}")
                return {}
                
            if role_type == RoleType.WEREWOLF:
                if "type" in action and action["type"] == "kill" and "target_id" in action:
                    target_id = action["target_id"]
                    if isinstance(target_id, (int, str)):  # 确保 target_id 是数字或字符串
                        return {"werewolf_kill": {"target_id": int(target_id)}}
            elif role_type == RoleType.SEER:
                if "type" in action and action["type"] == "check" and "target_id" in action:
                    target_name = action["target_id"]
                    if isinstance(target_name, str):  # 确保 target_id 是字符串（玩家名字）
                        return {"seer_check": {"target_id": target_name}}
            elif role_type == RoleType.WITCH:
                print("[DEBUG] 女巫行动解析开始")
                print(f"[DEBUG] 收到的响应: {action}")
                
                if "type" in action and action["type"] == "potion":
                    save_used = action.get("save", False)
                    poison_target = action.get("poison_target")
                    
                    print(f"[DEBUG] 解药使用: {save_used}")
                    print(f"[DEBUG] 毒药目标: {poison_target}")
                    
                    result = {
                        "witch_save": {"used": save_used},
                        "witch_poison": {"target_id": poison_target}
                    }
                    print(f"[DEBUG] 返回结果: {result}")
                    return result
                else:
                    print("[DEBUG] 女巫行动格式不正确")
            return {}
        except Exception as e:
            print(f"[API] 解析错误: {str(e)}")
            return {}
    
    def _parse_discussion(self, response: str) -> str:
        """解析讨论发言"""
        try:
            # 尝试从响应中提取 JSON 部分
            json_start = response.rfind("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    action = json.loads(json_str)
                    if action.get("type") == "discussion":
                        return action.get("message", "")
                except json.JSONDecodeError:
                    pass
            
            # 如果无法解析为JSON或不是讨论格式，返回清理后的响应
            return response.replace("<think>", "").replace("</think>", "").strip()
            
        except Exception as e:
            print(f"[API] 解析发言错误: {str(e)}")
            return "（发言解析错误）"
    
    def _parse_vote(self, response: str, game_state: GameState) -> int:
        """解析投票决策"""
        try:
            if not response:
                print("[API] 警告: 响应为空")
                return -1
            
            # 尝试从响应中提取 JSON 部分
            json_start = response.rfind("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                try:
                    action = json.loads(json_str)
                    print(f"[API] 解析到的投票数据: {action}")  # 打印解析到的数据
                    
                    if "type" not in action:
                        print("[API] 投票数据缺少type字段")
                        return -1
                        
                    if action["type"] != "vote":
                        print(f"[API] 投票类型错误: {action['type']}")
                        return -1
                        
                    if "target_id" not in action:
                        print("[API] 投票数据缺少target_id字段")
                        return -1
                    
                    target_id = action["target_id"]
                    if not isinstance(target_id, int):
                        print(f"[API] target_id不是整数: {target_id}")
                        return -1
                        
                    target = game_state.get_player_by_id(target_id)
                    if not target:
                        print(f"[API] 找不到目标玩家: {target_id}")
                        return -1
                        
                    if not target.is_alive:
                        print(f"[API] 目标玩家已死亡: {target.name}")
                        return -1
                        
                    return target_id
                    
                except json.JSONDecodeError as e:
                    print(f"[API] 投票JSON解析错误: {str(e)}")
                    print(f"[API] 原始JSON字符串: {json_str}")
            else:
                print("[API] 响应中未找到JSON格式数据")
            
            return -1  # 无效投票
            
        except Exception as e:
            print(f"[API] 投票解析错误: {str(e)}")
            return -1
    
    def _format_chat_history(self, game_state: GameState) -> str:
        """格式化聊天历史"""
        history = []
        for player in game_state.players:
            if player.chat_history:
                history.extend([f"{player.name}: {msg}" for msg in player.chat_history[-5:]])
        return "\n".join(history) 

    def _build_werewolf_prompt(self, game_state: GameState) -> str:
        """构建狼人夜晚行动提示词"""
        # 获取当前狼人
        current_wolf = next((p for p in game_state.get_alive_players() 
                           if p.role.role_type == RoleType.WEREWOLF), None)
        if not current_wolf:
            return ""
            
        # 获取其他狼人（只有当前狼人才能看到）
        other_werewolves = game_state.get_werewolf_teammates(current_wolf.id)
        
        # 获取存活的非狼人玩家
        alive_non_wolves = [p for p in game_state.get_alive_players() 
                           if p.id not in game_state._werewolves]
        
        # 第一晚使用简化的提示词
        if game_state.round_number == 0:
            return f"""第一天晚上。
                      你需要选择一名玩家击杀。
                      {'其他狼人玩家：' + '、'.join([w.name for w in other_werewolves]) if other_werewolves else '你是唯一的狼人。'}
                      
                      可选择的目标：
                      {chr(10).join([f"{p.id}. {p.name}" for p in alive_non_wolves])}
                      
                      请用以下格式返回JSON（一定要返回数字ID）：
                      {{"type": "kill", "target_id": 玩家ID}}
                      
                      示例：{{"type": "kill", "target_id": 1}}"""
        
        # 其他晚上使用正常提示词
        return f"""现在是第{game_state.round_number + 1}天晚上。
                  刚才的狼人讨论已经结束，现在需要选择一名玩家击杀。
                  {'其他狼人玩家：' + '、'.join([w.name for w in other_werewolves]) if other_werewolves else '你是唯一的狼人。'}
                  
                  可选择的目标：
                  {chr(10).join([f"{p.id}. {p.name}" for p in alive_non_wolves])}
                  
                  请用以下格式返回JSON（一定要返回数字ID）：
                  {{"type": "kill", "target_id": 玩家ID}}
                  
                  示例：{{"type": "kill", "target_id": 1}}"""

    def _build_seer_prompt(self, game_state: GameState) -> str:
        """构建预言家夜晚查验提示词"""
        # 获取预言家
        seer = next((p for p in game_state.get_alive_players() 
                    if p.role.role_type == RoleType.SEER), None)
        if not seer:
            return ""
            
        # 获取已经查验过的玩家列表
        checked_players = game_state.get_checked_players(seer.id)
        
        # 获取所有可查验的玩家
        alive_players = [p for p in game_state.get_alive_players() if p.id != seer.id]
        
        return f"""现在是第{game_state.round_number}天晚上。
                  你需要选择一名玩家查验身份。
                  {'已查验过的玩家：' + '、'.join(checked_players) if checked_players else '还没有查验过任何玩家。'}
                  
                  可选择的目标：
                  {chr(10).join([f"- {p.name}" for p in alive_players])}
                  
                  请用以下格式返回（返回玩家名字）：
                  {{"type": "check", "target_id": "玩家名字"}}
                  
                  示例：{{"type": "check", "target_id": "张三"}}"""

    def _build_witch_prompt(self, game_state: GameState) -> str:
        """构建女巫夜晚行动提示词"""
        # 获取当前女巫
        witch = next((p for p in game_state.get_alive_players() 
                     if p.role.role_type == RoleType.WITCH), None)
        if not witch:
            print("[DEBUG] 未找到存活的女巫")
            return ""
            
        # 获取今晚狼人击杀的目标（只有女巫能看到）
        killed_player = game_state.get_killed_player(witch.id)
        # 获取女巫药水使用情况（只有女巫能看到）
        witch_potions = game_state.get_witch_potions(witch.id)
        
        print(f"[DEBUG] 女巫ID: {witch.id}, 名字: {witch.name}")
        print(f"[DEBUG] 今晚被杀玩家: {killed_player.name if killed_player else '无'}")
        print(f"[DEBUG] 药水状态 - 解药: {'可用' if witch_potions['save'] else '已用'}, 毒药: {'可用' if witch_potions['poison'] else '已用'}")
        
        prompt = f"""现在是第{game_state.round_number}天晚上。\n"""
        
        if witch_potions["save"]:
            if killed_player:
                # 添加自救规则说明
                is_self = killed_player.id == witch.id
                if is_self:
                    if self.game_state.round_number == 0:
                        prompt += f"今晚你被狼人杀害了。这是第一夜，你可以使用解药自救。\n"
                    else:
                        prompt += f"今晚你被狼人杀害了，但你不能在第一夜之后自救。\n"
                else:
                    prompt += f"今晚{killed_player.name}被狼人杀害了。你还有一瓶解药，是否要使用？\n"
            else:
                prompt += "今晚没有玩家被狼人杀害。\n"
        else:
            prompt += "你已经用掉了解药。\n"
            
        if witch_potions["poison"]:
            prompt += "你还有一瓶毒药，是否要使用？\n"
            # 添加存活玩家列表供选择
            alive_players = [p for p in game_state.get_alive_players() if p.id != witch.id]
            prompt += "可选择的毒药目标：\n"
            prompt += "\n".join([f"- {p.name} (ID: {p.id})" for p in alive_players]) + "\n"
        else:
            prompt += "你已经用掉了毒药。\n"
            
        prompt += "注意：每晚最多使用一瓶药。\n"
        prompt += """请用以下格式返回：{"type": "potion", "save": true/false, "poison_target": 玩家ID或null}
                    - 使用解药救人：{"type": "potion", "save": true, "poison_target": null}
                    - 使用毒药毒人：{"type": "potion", "save": false, "poison_target": 1}
                    - 什么都不做：{"type": "potion", "save": false, "poison_target": null}"""
        
        print(f"[DEBUG] 生成的女巫提示词:\n{prompt}")
        return prompt

    def _build_discussion_prompt(self, game_state: GameState, player: Player) -> str:
        """构建白天讨论提示词"""
        
        # 获取上一轮死亡信息
        dead_players = game_state.get_last_night_dead_players()
        # 获取玩家自己的特殊信息（如预言家的查验结果）
        special_info = self._get_player_special_info(game_state, player)
        
        prompt = f"""现在是第{game_state.round_number}天白天。\n"""
        
        if dead_players:
            prompt += f"昨晚死亡的玩家：{', '.join([p.name for p in dead_players])}\n"
        else:
            prompt += "昨晚是平安夜，没有玩家死亡。\n"
            
        if special_info:
            prompt += f"你的特殊信息：{special_info}\n"
            
        prompt += """请根据当前游戏状态，发表你的看法。
                    注意：
                    1. 要符合你的角色身份
                    2. 要基于已知信息进行合理推理
                    3. 不要说出你不应该知道的信息
                    4. 要有策略性，注意保护自己
                    
                    请用以下格式返回：{"type": "discussion", "message": "你的发言内容"}"""
        return prompt

    def _build_vote_prompt(self, game_state: GameState) -> str:
        """构建投票阶段提示词"""
        # 获取存活玩家列表及其ID
        alive_players = game_state.get_alive_players()
        player_info = "\n".join([f"- {p.name} (ID: {p.id})" for p in alive_players])
        
        return f"""现在是第{game_state.round_number}天的投票阶段。
                  存活玩家列表：
                  {player_info}
                  
                  请根据之前的讨论和你的判断，选择一名存活玩家投票。
                  注意：必须使用玩家的正确ID进行投票。
                  
                  请严格按照以下JSON格式返回：
                  {{"type": "vote", "target_id": 玩家ID}}
                  
                  示例：
                  - 投票给ID为2的玩家：{{"type": "vote", "target_id": 2}}
                  - 投票给ID为5的玩家：{{"type": "vote", "target_id": 5}}"""

    def _get_player_special_info(self, game_state: GameState, player: Player) -> str:
        """获取玩家的特殊信息（如预言家的查验结果）"""
        if player.role.role_type == RoleType.SEER:
            # 获取昨晚的查验结果（只有预言家能看到）
            last_check = game_state.get_last_check_result(player.id)
            if last_check:
                return f"昨晚查验结果：{last_check['player'].name} 是 {last_check['role']}"
        elif player.role.role_type == RoleType.WEREWOLF:
            # 获取其他狼人信息（只有当前狼人能看到）
            other_werewolves = game_state.get_werewolf_teammates(player.id)
            if other_werewolves:
                return f"你的狼人同伴：{', '.join([w.name for w in other_werewolves])}"
        elif player.role.role_type == RoleType.WITCH:
            # 获取药水使用情况（只有女巫能看到）
            potions = game_state.get_witch_potions(player.id)
            return f"解药{'已用' if not potions['save'] else '未用'}，毒药{'已用' if not potions['poison'] else '未用'}"
        return "" 

    async def _handle_werewolf_discussion(self, werewolves: List[Player], game_state: GameState) -> List[str]:
        """处理狼人夜间讨论"""
        discussions = []
        for wolf in werewolves:
            context = self._build_game_context(game_state, wolf)
            prompt = self._build_werewolf_discussion_prompt(game_state, discussions)
            response = await self._call_api(prompt, context, wolf)
            
            try:
                # 解析讨论内容
                if "<think>" in response:
                    response = response[response.rfind("</think>") + 8:].strip()
                json_start = response.rfind("{")
                if json_start >= 0:
                    json_str = response[json_start:response.rfind("}") + 1]
                    action = json.loads(json_str)
                    if action.get("type") == "discussion":
                        message = action.get("message", "").strip()
                        if message:
                            discussions.append(f"{wolf.name}: {message}")
            except Exception as e:
                print(f"解析狼人讨论失败: {str(e)}")
                
        return discussions

    def _build_werewolf_discussion_prompt(self, game_state: GameState, previous_discussions: List[str]) -> str:
        """构建狼人夜间讨论提示词"""
        prompt = f"""现在是第{game_state.round_number}天晚上的狼人讨论时间。
                    请与你的狼队友讨论战术，可以包括：
                    1. 今晚应该击杀谁
                    2. 明天白天如何发言
                    3. 如何配合队友
                    
                    当前讨论记录：
                    {chr(10).join(previous_discussions) if previous_discussions else "（暂无讨论）"}
                    
                    请用以下格式返回：{{"type": "discussion", "message": "你的讨论内容"}}"""
        return prompt 