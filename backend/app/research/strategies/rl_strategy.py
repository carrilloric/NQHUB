"""
RLStrategy

Reinforcement Learning-based trading strategies.

These strategies use RL agents that learn optimal trading policies through
interaction with the market environment.

Common RL algorithms:
- Deep Q-Network (DQN)
- Proximal Policy Optimization (PPO)
- Soft Actor-Critic (SAC)
- Twin Delayed DDPG (TD3)

The agent learns to maximize cumulative reward (profit) by taking actions
(long, short, flat) in response to market states.

Example:
    class MyRLStrategy(RLStrategy):
        def train(self, env, n_episodes=1000):
            # Train RL agent
            self.agent = PPO("MlpPolicy", env)
            self.agent.learn(total_timesteps=n_episodes)
            self.is_fitted = True

        def generate_signals(self, market_state: MarketState, data=None) -> pd.Series:
            # Use trained agent to select action
            observation = self._state_to_observation(market_state)
            action = self.agent.predict(observation)
            signal = self._action_to_signal(action)
            return pd.Series([signal], index=[market_state.timestamp])
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .base import NQHubStrategy, StrategyMetadata
from app.research.market_state import MarketState


class RLStrategy(NQHubStrategy):
    """
    Base class for reinforcement learning strategies.

    RL strategies learn optimal trading policies by maximizing cumulative reward.
    The agent interacts with a trading environment and learns from experience.

    Key concepts:
    - State: Current market conditions (MarketState + OHLCV data)
    - Action: Trading decision (long=1, flat=0, short=-1)
    - Reward: Profit/loss from the action
    - Policy: Mapping from states to actions

    Workflow:
    1. train() - Train the RL agent in simulated environment
    2. generate_signals() - Use trained agent to make trading decisions
    3. evaluate() - Test agent performance on unseen data

    Advantages:
    - Can learn complex, non-linear strategies
    - Optimizes for long-term cumulative profit
    - Handles sequential decision-making naturally
    - Can incorporate risk management in reward function

    Disadvantages:
    - Requires extensive training (compute-intensive)
    - Sample inefficiency (needs many episodes)
    - Unstable training (hyperparameter sensitive)
    - Difficult to interpret learned policy
    """

    def __init__(self, metadata: StrategyMetadata, **kwargs):
        """
        Initialize RL strategy.

        Args:
            metadata: Strategy metadata
            **kwargs: Strategy-specific parameters

        Common parameters:
        - algorithm: RL algorithm ("dqn", "ppo", "sac", "td3")
        - learning_rate: Learning rate for optimizer
        - gamma: Discount factor (0.0 - 1.0)
        - epsilon: Exploration rate (for epsilon-greedy policies)
        - replay_buffer_size: Size of experience replay buffer
        - batch_size: Mini-batch size for training
        - n_episodes: Number of training episodes
        """
        metadata.strategy_type = "rl"
        super().__init__(metadata, **kwargs)

        # RL strategies need training
        self.is_fitted = False
        self.agent = None
        self.training_history: Dict[str, List[float]] = {
            "episode_rewards": [],
            "episode_lengths": [],
            "loss": [],
        }

    def train(self, env, n_episodes: int = 1000, **train_params):
        """
        Train the RL agent in a trading environment.

        Args:
            env: Trading environment (gym.Env compatible)
            n_episodes: Number of training episodes
            **train_params: Additional training parameters

        Example:
            from stable_baselines3 import PPO

            class MyRLStrategy(RLStrategy):
                def train(self, env, n_episodes=1000):
                    self.agent = PPO("MlpPolicy", env, verbose=1)
                    self.agent.learn(total_timesteps=n_episodes * 1000)
                    self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement train()"
        )

    def select_action(self, observation: np.ndarray, deterministic: bool = True) -> int:
        """
        Select action using trained RL agent.

        Args:
            observation: Current state observation (numpy array)
            deterministic: If True, use deterministic policy (no exploration)

        Returns:
            Action: 0 (long), 1 (flat), 2 (short)

        Raises:
            ValueError: If agent is not trained
        """
        if not self.is_fitted:
            raise ValueError(
                f"Strategy '{self.metadata.name}' must be trained before use. "
                f"Call train() first."
            )

        if self.agent is None:
            raise ValueError(
                f"Strategy '{self.metadata.name}' has no agent. "
                f"Implement train() and set self.agent."
            )

        # For stable-baselines3 agents
        if hasattr(self.agent, 'predict'):
            action, _ = self.agent.predict(observation, deterministic=deterministic)
            return action

        raise NotImplementedError(
            f"{self.__class__.__name__} agent does not support predict()"
        )

    # Subclasses must implement these abstract methods
    def required_features(self) -> List[str]:
        """
        Declare required features.

        For RL strategies, this includes all state information needed by the agent.

        Example:
            return [
                "active_fvgs", "active_obs", "bias", "session",
                "key_levels", "account_equity", "position"
            ]
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement required_features()"
        )

    def generate_signals(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate signals using trained RL agent.

        Args:
            market_state: Current MarketState
            data: OHLCV data for observation

        Returns:
            pd.Series with signals (1/0/-1)

        Example:
            observation = self._state_to_observation(market_state, data)
            action = self.select_action(observation)
            signal = self._action_to_signal(action)
            return pd.Series([signal], index=[market_state.timestamp])
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate_signals()"
        )

    def position_size(self, signal: int, market_state: MarketState, **kwargs) -> float:
        """
        Calculate position size.

        For RL strategies, position sizing can be:
        - Part of the action space (continuous control)
        - Fixed size (1 contract)
        - Based on Q-values or value function

        Default: Fixed size (1 contract)
        """
        if signal == 0:
            return 0.0

        # Get risk per trade from parameters
        risk_per_trade = self.params.get("risk_per_trade", 1.0)

        if signal == 1:  # Long
            return risk_per_trade
        elif signal == -1:  # Short
            return -risk_per_trade
        else:
            return 0.0

    # Helper methods for RL strategies

    def _state_to_observation(self, market_state: MarketState, data: Optional[pd.DataFrame] = None) -> np.ndarray:
        """
        Convert MarketState and data to observation vector for RL agent.

        Override this to create custom state representation.

        Args:
            market_state: Current MarketState
            data: Optional OHLCV data

        Returns:
            Numpy array representing the state

        Example:
            features = [
                len(market_state.get_active_fvgs("5min")),
                1 if market_state.get_bias("5min") == "bullish" else 0,
                1 if market_state.session == "NY_AM" else 0,
                # ... more features
            ]
            return np.array(features, dtype=np.float32)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _state_to_observation()"
        )

    def _action_to_signal(self, action: int) -> int:
        """
        Convert RL action to trading signal.

        Args:
            action: Action from RL agent (typically 0, 1, 2)

        Returns:
            Signal: 1 (long), 0 (flat), -1 (short)

        Example:
            # If action space is {0: long, 1: flat, 2: short}
            action_map = {0: 1, 1: 0, 2: -1}
            return action_map[action]
        """
        # Default mapping: 0→long, 1→flat, 2→short
        action_map = {0: 1, 1: 0, 2: -1}
        return action_map.get(action, 0)

    def save_agent(self, filepath: str):
        """
        Save trained RL agent to disk.

        Args:
            filepath: Path to save the agent

        Example:
            # For stable-baselines3
            self.agent.save(filepath)
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement save_agent()"
        )

    def load_agent(self, filepath: str):
        """
        Load trained RL agent from disk.

        Args:
            filepath: Path to load the agent from

        Example:
            # For stable-baselines3
            from stable_baselines3 import PPO
            self.agent = PPO.load(filepath)
            self.is_fitted = True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement load_agent()"
        )

    def get_training_history(self) -> Dict[str, List[float]]:
        """
        Get training history (rewards, losses, etc.)

        Returns:
            Dictionary with training metrics
        """
        return self.training_history

    def __repr__(self) -> str:
        trained_status = "trained" if self.is_fitted else "not trained"
        return (
            f"RLStrategy("
            f"name='{self.metadata.name}', "
            f"version='{self.metadata.version}', "
            f"status='{trained_status}')"
        )
