import pytest
import asyncio
from unittest.mock import Mock, patch
from src.controllers.api_controller import APIController
from src.models.player import Player
from src.models.roles.base_role import RoleType, BaseRole
from src.models.game_state import GameState, GamePhase

# Helper function to create mock players
def create_mock_player(id: int, name: str, role_type: RoleType) -> Player:
    role = BaseRole(role_type)
    return Player(id, name, role)

@pytest.fixture
def api_controller():
    return APIController(model_name="deepseek-r1")

@pytest.fixture
def mock_game_state():
    game_state = Mock(spec=GameState)
    game_state.round_number = 0
    game_state.phase = GamePhase.NIGHT
    
    # Create some mock players
    players = [
        create_mock_player(1, "Player1", RoleType.WEREWOLF),
        create_mock_player(2, "Player2", RoleType.VILLAGER),
        create_mock_player(3, "Player3", RoleType.SEER),
        create_mock_player(4, "Player4", RoleType.WITCH),
    ]
    
    game_state.players = players
    game_state.get_alive_players.return_value = players
    game_state._werewolves = [1]  # Player1 is werewolf
    
    return game_state

@pytest.mark.asyncio
async def test_generate_night_action_werewolf(api_controller, mock_game_state):
    # Mock the API response
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "kill", "target_id": 2}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        werewolf = create_mock_player(1, "Werewolf", RoleType.WEREWOLF)
        action = await api_controller.generate_night_action(werewolf, mock_game_state)
        
        assert action == {"werewolf_kill": {"target_id": 2}}

@pytest.mark.asyncio
async def test_generate_night_action_seer(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "check", "target_id": 2}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        seer = create_mock_player(3, "Seer", RoleType.SEER)
        action = await api_controller.generate_night_action(seer, mock_game_state)
        
        assert action == {"seer_check": {"target_id": 2}}

@pytest.mark.asyncio
async def test_generate_night_action_witch(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "potion", "save": true, "poison_target": null}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        witch = create_mock_player(4, "Witch", RoleType.WITCH)
        action = await api_controller.generate_night_action(witch, mock_game_state)
        
        assert action == {
            "witch_save": {"used": True},
            "witch_poison": {"target_id": None}
        }

@pytest.mark.asyncio
async def test_generate_discussion(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "discussion", "message": "I think Player2 is suspicious"}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        player = create_mock_player(1, "Player1", RoleType.WEREWOLF)
        message = await api_controller.generate_discussion(player, mock_game_state)
        
        assert message == "I think Player2 is suspicious"

@pytest.mark.asyncio
async def test_generate_vote(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "vote", "target_id": 2}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        player = create_mock_player(1, "Player1", RoleType.WEREWOLF)
        target_id = await api_controller.generate_vote(player, mock_game_state)
        
        assert target_id == 2

def test_set_model(api_controller):
    # Test valid model name
    api_controller.set_model("deepseek-chat")
    assert api_controller.model_name == "deepseek-chat"
    
    # Test invalid model name
    with pytest.raises(ValueError):
        api_controller.set_model("invalid-model")

@pytest.mark.asyncio
async def test_api_error_handling(api_controller, mock_game_state):
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        # Simulate API error
        mock_create.side_effect = Exception("API Error")
        
        player = create_mock_player(1, "Player1", RoleType.WEREWOLF)
        action = await api_controller.generate_night_action(player, mock_game_state)
        
        assert action == {}

def test_init_role_prompts(api_controller):
    prompts = api_controller._init_role_prompts()
    
    # Check if all role types have prompts
    assert RoleType.WEREWOLF in prompts
    assert RoleType.VILLAGER in prompts
    assert RoleType.SEER in prompts
    assert RoleType.WITCH in prompts
    assert RoleType.HUNTER in prompts
    
    # Check if prompts are non-empty strings
    for prompt in prompts.values():
        assert isinstance(prompt, str)
        assert len(prompt) > 0

@pytest.mark.asyncio
async def test_generate_night_action_villager(api_controller, mock_game_state):
    # Villagers should not have night actions
    villager = create_mock_player(2, "Villager", RoleType.VILLAGER)
    action = await api_controller.generate_night_action(villager, mock_game_state)
    assert action == {}

@pytest.mark.asyncio
async def test_generate_night_action_hunter(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"type": "prepare_shot", "target_id": 1}'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        hunter = create_mock_player(5, "Hunter", RoleType.HUNTER)
        action = await api_controller.generate_night_action(hunter, mock_game_state)
        
        assert action == {"hunter_shot": {"target_id": 1}}

@pytest.mark.asyncio
async def test_invalid_json_response(api_controller, mock_game_state):
    mock_response = {
        "choices": [{
            "message": {
                "content": 'invalid json'
            }
        }]
    }
    
    with patch('openai.OpenAI.chat.completions.create') as mock_create:
        mock_create.return_value = Mock(**mock_response)
        
        player = create_mock_player(1, "Player1", RoleType.WEREWOLF)
        action = await api_controller.generate_night_action(player, mock_game_state)
        
        assert action == {}

if __name__ == "__main__":
    pytest.main(["-v"])