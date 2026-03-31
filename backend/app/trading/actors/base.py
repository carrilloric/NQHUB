"""
Base Actor class for NQHUB trading system.
"""
from typing import Optional
from nautilus_trader.common.actor import Actor
from nautilus_trader.config import ActorConfig


<<<<<<< HEAD
class NQHubActorConfig(ActorConfig, kw_only=True):
=======
class NQHubActorConfig(ActorConfig):
>>>>>>> 1ee3282 (feat(AUT-336): Implement VectorBT Pro backtesting engine with Celery workers)
    """Configuration for NQHubActor."""
    bot_id: str
    component_id: Optional[str] = None


class NQHubActor(Actor):
    """
    Base class for all NQHUB Actors.

    This class extends the NautilusTrader Actor to provide
    common functionality for all NQHUB trading actors.
    """

    def __init__(self, config: NQHubActorConfig):
        """
        Initialize NQHubActor.

        Args:
            config: Actor configuration including bot_id
        """
        super().__init__(config)
        self.bot_id = config.bot_id
        self.component_id = config.component_id or f"{config.bot_id}-{self.__class__.__name__}"

    def on_start(self) -> None:
        """Called when the actor starts."""
        self.log.info(f"Starting {self.component_id}")

    def on_stop(self) -> None:
        """Called when the actor stops."""
        self.log.info(f"Stopping {self.component_id}")