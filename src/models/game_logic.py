async def handle_seer_check(self, seer_id: int, target_id: int) -> None:
    """处理预言家查验行为"""
    seer = self.game_state.get_player_by_id(seer_id)
    target = self.game_state.get_player_by_id(target_id)
    
    if not seer or not target:
        return
    
    # 记录查验结果
    is_werewolf = target.role.role_type == RoleType.WEREWOLF
    self.game_state._check_results[seer_id] = {
        "player": target,
        "role": "狼人" if is_werewolf else "好人"
    }
    
    # 记录已查验的玩家
    if seer_id not in self.game_state._checked_players:
        self.game_state._checked_players[seer_id] = set()
    self.game_state._checked_players[seer_id].add(target_id)
    
    # 记录查验行为到游戏日志
    self.game_state.record_night_action("seer_check", {"target_id": target_id})
    
    # 写入游戏输出文件
    await self.game_output.write_game_event(
        f"预言家查验了{target.name}，发现Ta是{'狼人' if is_werewolf else '好人'}"
    )