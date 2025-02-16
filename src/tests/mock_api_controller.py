from src.models.role import RoleType

class MockAPIController:
    """简化版的Mock API控制器，用于单元测试"""
    async def generate_night_action(self, player, game_state):
        if player.role.role_type == RoleType.WEREWOLF:
            return {"werewolf_kill": {"target_id": 1}}  # 总是击杀ID为1的玩家
        elif player.role.role_type == RoleType.SEER:
            target_id = 2  # 总是查验ID为2的玩家
            target = game_state.get_player_by_id(target_id)
            if target:
                is_werewolf = target.role.role_type == RoleType.WEREWOLF
                # 记录查验结果到游戏状态
                game_state.record_night_action("seer_check", {"target_id": target_id})
                # 记录已查验的玩家
                if player.id not in game_state._checked_players:
                    game_state._checked_players[player.id] = set()
                game_state._checked_players[player.id].add(target_id)
                
                # 记录查验结果
                game_state._check_results[player.id] = {
                    "player": target,
                    "role": "狼人" if is_werewolf else "好人"
                }
                
                print(f"[DEBUG] 预言家查验: 目标={target.name}, 结果={'狼人' if is_werewolf else '好人'}")
                return {"seer_check": {"target_id": target_id}}
            return {"seer_check": {"target_id": None}}
        elif player.role.role_type == RoleType.WITCH:
            # 获取女巫药水状态
            potions = game_state.get_witch_potions(player.id)
            # 获取今晚被杀的玩家
            killed_player = game_state.get_killed_player(player.id)
            
            # 根据游戏状态决定是否使用解药
            use_save = False
            if potions["save"] and killed_player:
                if killed_player.id == player.id:  # 如果被杀的是女巫自己
                    use_save = game_state.round_number == 0  # 只在第一夜可以自救
                else:
                    use_save = True  # 救其他人
            
            # 根据游戏状态决定是否使用毒药
            poison_target = None
            if potions["poison"] and game_state._last_night_poisoned is not None:
                poison_target = game_state._last_night_poisoned
            
            return {
                "witch_save": {"used": use_save},
                "witch_poison": {"target_id": poison_target}
            }
        elif player.role.role_type == RoleType.HUNTER:
            return {"hunter_shot": {"target_id": 3}}  # 总是射杀ID为3的玩家
        return {}
        
    async def generate_discussion(self, player, game_state):
        if player.role.role_type == RoleType.SEER:
            # 如果是预言家，在发言中包含查验结果
            last_check = game_state.get_last_check_result(player.id)
            if last_check:
                return f"{player.name}: 我查验了{last_check['player'].name}，他是{last_check['role']}"
        return f"{player.name}的测试发言"
        
    async def generate_vote(self, player, game_state):
        return {"type": "vote", "target_id": 1}  # 总是投票给ID为1的玩家
        
    async def _handle_werewolf_discussion(self, werewolves, game_state):
        return [f"{wolf.name}: 测试狼人讨论" for wolf in werewolves] 