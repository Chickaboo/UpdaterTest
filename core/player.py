from typing import List, Optional, Dict, Any, Tuple
from core.utils import generate_id
from core.constants import *

class Player:
    """Represents a player in the tournament."""
    def __init__(self, name: str, rating: Optional[int] = None, player_id: Optional[str] = None,
                 phone: Optional[str] = None, email: Optional[str] = None, club: Optional[str] = None,
                 federation: Optional[str] = None, gender: Optional[str] = None, dob: Optional[str] = None) -> None:
        self.id: str = player_id or generate_id("player_")
        self.name: str = name
        self.rating: int = rating if rating is not None else 1000
        self.phone: Optional[str] = phone
        self.email: Optional[str] = email
        self.club: Optional[str] = club
        self.federation: Optional[str] = federation
        self.gender: Optional[str] = gender
        self.dob: Optional[str] = dob
        self.score: float = 0.0
        self.is_active: bool = True # Used for withdrawals

        # History
        self.color_history: List[Optional[str]] = [] # Stores "White", "Black", or None (for bye)
        self.opponent_ids: List[Optional[str]] = []
        self.results: List[Optional[float]] = []
        self.running_scores: List[float] = []
        self.has_received_bye: bool = False
        self.num_black_games: int = 0 # Counts actual games played as Black
        self.float_history: List[int] = []  # Track rounds where player floated down

        # Tiebreakers (calculated)
        self.tiebreakers: Dict[str, float] = {}

        # Runtime cache
        self._opponents_played_cache: List[Optional['Player']] = []

    def __repr__(self) -> str:
        status = "" if self.is_active else " (Inactive)"
        return f"{self.name} ({self.rating}){status}"

    def get_opponent_objects(self, players_dict: Dict[str, 'Player']) -> List[Optional['Player']]:
        """Resolves opponent ID's to Player objects using the provided dictionary."""
        if len(self._opponents_played_cache) != len(self.opponent_ids):
             self._opponents_played_cache = [players_dict.get(opp_id) if opp_id else None for opp_id in self.opponent_ids]
        return self._opponents_played_cache

    def get_last_two_colors(self) -> Tuple[Optional[str], Optional[str]]:
        """Returns the colors of the last two non-bye games played."""
        valid_colors = [c for c in self.color_history if c is not None]
        if len(valid_colors) >= 2: return valid_colors[-1], valid_colors[-2]
        elif len(valid_colors) == 1: return valid_colors[-1], None
        else: return None, None

    def get_color_preference(self) -> Optional[str]:
        """Determines color preference based on FIDE/USCF rules.
        1. Absolute: If last two played games had same color, must get the other.
        2. Preference: If colors are unbalanced, prefer the color that moves towards balance.
        Returns: "White", "Black", or None if no preference or perfectly balanced.
        """
        valid_played_colors = [c for c in self.color_history if c is not None]

        if len(valid_played_colors) >= 2:
            last_color = valid_played_colors[-1]
            second_last_color = valid_played_colors[-2]
            if last_color == second_last_color:
                return "Black" if last_color == "White" else "White"

        white_games_played = valid_played_colors.count("White")
        black_games_played = valid_played_colors.count("Black")

        if white_games_played > black_games_played:
            return "Black"
        elif black_games_played > white_games_played:
            return "White"
        
        return None

    def add_round_result(self, opponent: Optional['Player'], result: float, color: Optional[str]):
        """Records the outcome of a round for the player."""
        opponent_id = opponent.id if opponent else None
        self.opponent_ids.append(opponent_id)
        self.results.append(result)
        self.score += result
        self.running_scores.append(self.score)
        self.color_history.append(color) # color can be None for a bye
        if color == "Black": 
            self.num_black_games += 1
        if opponent is None: # This means it was a bye
            self.has_received_bye = True
            logging.debug(f"Player {self.name} marked as having received a bye.")
        self._opponents_played_cache = [] # Invalidate cache

    def to_dict(self) -> Dict[str, Any]:
        """Serializes player data."""
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Deserializes player data."""
        player = cls(
            name=data['name'],
            rating=data.get('rating', 1000),
            player_id=data['id'],
            phone=data.get('phone'),
            email=data.get('email'),
            club=data.get('club'),
            federation=data.get('federation'),
            gender=data.get('gender'),
            dob=data.get('dob')
        )
        for key, value in data.items():
             if hasattr(player, key) and not key.startswith('_'):
                  setattr(player, key, value)
        # Ensure essential lists exist if loading older format without them
        for list_attr in ['color_history', 'opponent_ids', 'results', 'running_scores', 'float_history']:
             if not hasattr(player, list_attr) or getattr(player, list_attr) is None:
                  setattr(player, list_attr, [])
        if not hasattr(player, 'has_received_bye'): # For older save files
            player.has_received_bye = (None in player.opponent_ids) if player.opponent_ids else False
        if not hasattr(player, 'num_black_games'): # For older save files
            player.num_black_games = player.color_history.count("Black") if player.color_history else 0

        return player