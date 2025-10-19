"""
Custom exceptions for Scrim.GG application.
"""


class ScrimGGException(Exception):
    """Base exception for all Scrim.GG errors."""
    pass


class ValidationError(ScrimGGException):
    """Raised when validation fails."""
    pass


class PlayerNotFoundError(ScrimGGException):
    """Raised when a player is not found."""
    pass


class LobbyNotFoundError(ScrimGGException):
    """Raised when a lobby is not found."""
    pass


class MatchNotFoundError(ScrimGGException):
    """Raised when a match is not found."""
    pass


class QueueError(ScrimGGException):
    """Raised when queue operations fail."""
    pass


class MatchmakingError(ScrimGGException):
    """Raised when matchmaking fails."""
    pass


class VetoError(ScrimGGException):
    """Raised when veto operations fail."""
    pass


class MatchStateError(ScrimGGException):
    """Raised when match state is invalid."""
    pass


class PlayerInActiveMatchError(ScrimGGException):
    """Raised when player is already in an active match."""
    
    def __init__(self, puuid, match_id):
        self.puuid = puuid
        self.match_id = match_id
        super().__init__(f"Player {puuid} is already in active match {match_id}")


class LobbyFullError(ScrimGGException):
    """Raised when trying to join a full lobby."""
    pass


class InsufficientPlayersError(ScrimGGException):
    """Raised when there are not enough players."""
    pass

