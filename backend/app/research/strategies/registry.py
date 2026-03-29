"""
Strategy Registry

Central registry for managing trading strategies in NQHUB.

The registry provides:
- Strategy registration and discovery
- Strategy versioning and metadata management
- Strategy validation and testing
- Integration with API endpoints for notebook registration

Usage:
    # In notebook or script
    from app.research.strategies import StrategyRegistry, RuleBasedStrategy, StrategyMetadata

    # Create strategy
    metadata = StrategyMetadata(
        name="FVG Retest Strategy",
        description="Trades FVG retests with bias confirmation",
        version="1.0.0",
        author="researcher@nqhub.com"
    )

    class MyStrategy(RuleBasedStrategy):
        ...

    strategy = MyStrategy(metadata)

    # Register strategy
    registry = StrategyRegistry()
    registry.register(strategy)

    # Later: retrieve and use strategy
    strategy = registry.get("FVG Retest Strategy", version="1.0.0")
    signals = strategy.generate_signals(market_state)
"""

from typing import Dict, List, Optional, Type
from datetime import datetime
import json
import logging

from .base import NQHubStrategy, StrategyMetadata

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """
    Central registry for managing trading strategies.

    Strategies are stored in memory and can optionally be persisted to:
    - PostgreSQL database (metadata + pickled strategy object)
    - File system (JSON metadata + Python source code)
    - Redis (for fast access in live trading)

    The registry maintains a catalog of:
    - Strategy metadata (name, version, author, type)
    - Strategy instances (ready to generate signals)
    - Strategy performance history
    - Strategy dependencies (required features, models)
    """

    def __init__(self):
        """Initialize empty strategy registry."""
        # In-memory storage: {name: {version: strategy}}
        self._strategies: Dict[str, Dict[str, NQHubStrategy]] = {}

        # Strategy metadata index
        self._metadata: Dict[str, StrategyMetadata] = {}

        # Performance tracking
        self._performance: Dict[str, Dict[str, List[float]]] = {}

        logger.info("Initialized StrategyRegistry")

    def register(
        self,
        strategy: NQHubStrategy,
        overwrite: bool = False
    ) -> bool:
        """
        Register a strategy in the registry.

        Args:
            strategy: Strategy instance to register
            overwrite: If True, overwrite existing strategy with same name/version

        Returns:
            True if registration successful

        Raises:
            ValueError: If strategy already exists and overwrite=False

        Example:
            registry = StrategyRegistry()

            metadata = StrategyMetadata(
                name="My Strategy",
                version="1.0.0",
                author="me@example.com"
            )

            class MyStrategy(RuleBasedStrategy):
                ...

            strategy = MyStrategy(metadata)
            registry.register(strategy)
        """
        name = strategy.metadata.name
        version = strategy.metadata.version

        # Check if strategy already exists
        if name in self._strategies:
            if version in self._strategies[name] and not overwrite:
                raise ValueError(
                    f"Strategy '{name}' version '{version}' already registered. "
                    f"Use overwrite=True to replace."
                )

        # Initialize name entry if needed
        if name not in self._strategies:
            self._strategies[name] = {}
            self._performance[name] = {}

        # Register strategy
        self._strategies[name][version] = strategy
        self._metadata[f"{name}@{version}"] = strategy.metadata

        logger.info(
            f"Registered strategy: {name} v{version} "
            f"(type={strategy.metadata.strategy_type})"
        )

        return True

    def get(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[NQHubStrategy]:
        """
        Retrieve a strategy from the registry.

        Args:
            name: Strategy name
            version: Strategy version (if None, returns latest version)

        Returns:
            Strategy instance or None if not found

        Example:
            strategy = registry.get("My Strategy", version="1.0.0")
            if strategy:
                signals = strategy.generate_signals(market_state)
        """
        if name not in self._strategies:
            logger.warning(f"Strategy '{name}' not found in registry")
            return None

        # If version not specified, get latest version
        if version is None:
            versions = list(self._strategies[name].keys())
            if not versions:
                return None

            # Sort versions and get latest
            versions.sort(reverse=True)
            version = versions[0]

        strategy = self._strategies[name].get(version)

        if strategy is None:
            logger.warning(
                f"Strategy '{name}' version '{version}' not found"
            )

        return strategy

    def list_strategies(
        self,
        strategy_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        List all registered strategies.

        Args:
            strategy_type: Filter by strategy type ("rule_based", "ml", "rl", "hybrid")

        Returns:
            List of dictionaries with strategy info

        Example:
            strategies = registry.list_strategies(strategy_type="rule_based")
            for s in strategies:
                print(f"{s['name']} v{s['version']}")
        """
        strategies = []

        for name, versions in self._strategies.items():
            for version, strategy in versions.items():
                # Apply type filter if specified
                if strategy_type and strategy.metadata.strategy_type != strategy_type:
                    continue

                strategies.append({
                    "name": name,
                    "version": version,
                    "type": strategy.metadata.strategy_type,
                    "author": strategy.metadata.author,
                    "description": strategy.metadata.description,
                    "is_fitted": strategy.is_fitted,
                    "required_features": strategy.required_features(),
                })

        return strategies

    def unregister(self, name: str, version: Optional[str] = None) -> bool:
        """
        Unregister a strategy from the registry.

        Args:
            name: Strategy name
            version: Strategy version (if None, removes all versions)

        Returns:
            True if unregistration successful

        Example:
            # Remove specific version
            registry.unregister("My Strategy", version="1.0.0")

            # Remove all versions
            registry.unregister("My Strategy")
        """
        if name not in self._strategies:
            logger.warning(f"Strategy '{name}' not found")
            return False

        if version is None:
            # Remove all versions
            del self._strategies[name]
            del self._performance[name]

            # Remove from metadata index
            keys_to_remove = [
                key for key in self._metadata.keys()
                if key.startswith(f"{name}@")
            ]
            for key in keys_to_remove:
                del self._metadata[key]

            logger.info(f"Unregistered all versions of strategy '{name}'")
        else:
            # Remove specific version
            if version in self._strategies[name]:
                del self._strategies[name][version]
                del self._metadata[f"{name}@{version}"]

                # If no versions left, remove name entry
                if not self._strategies[name]:
                    del self._strategies[name]
                    del self._performance[name]

                logger.info(f"Unregistered strategy '{name}' v{version}")
            else:
                logger.warning(
                    f"Strategy '{name}' version '{version}' not found"
                )
                return False

        return True

    def validate_strategy(self, strategy: NQHubStrategy) -> Dict[str, bool]:
        """
        Validate a strategy before registration.

        Checks:
        - Has valid metadata
        - Implements required methods
        - Has sensible parameters

        Args:
            strategy: Strategy to validate

        Returns:
            Dictionary with validation results

        Example:
            validation = registry.validate_strategy(my_strategy)
            if validation["is_valid"]:
                registry.register(my_strategy)
            else:
                print("Validation errors:", validation["errors"])
        """
        errors = []
        warnings = []

        # Check metadata
        if not strategy.metadata.name:
            errors.append("Strategy name is required")

        if not strategy.metadata.version:
            errors.append("Strategy version is required")

        if not strategy.metadata.description:
            warnings.append("Strategy description is empty")

        # Check required methods are implemented
        try:
            features = strategy.required_features()
            if not features:
                warnings.append("Strategy requires no features (unusual)")
        except NotImplementedError:
            errors.append("required_features() not implemented")

        # Check strategy type
        valid_types = ["rule_based", "ml", "rl", "hybrid"]
        if strategy.metadata.strategy_type not in valid_types:
            errors.append(
                f"Invalid strategy type: {strategy.metadata.strategy_type}. "
                f"Must be one of: {valid_types}"
            )

        # For ML/RL strategies, check if fitted
        if strategy.metadata.strategy_type in ["ml", "rl"]:
            if not strategy.is_fitted:
                warnings.append(
                    f"{strategy.metadata.strategy_type.upper()} strategy is not fitted. "
                    f"Train before use."
                )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def get_metadata(self, name: str, version: Optional[str] = None) -> Optional[StrategyMetadata]:
        """
        Get strategy metadata without loading the full strategy.

        Args:
            name: Strategy name
            version: Strategy version (if None, returns latest)

        Returns:
            StrategyMetadata or None
        """
        if version is None:
            # Get latest version
            if name not in self._strategies:
                return None

            versions = list(self._strategies[name].keys())
            if not versions:
                return None

            versions.sort(reverse=True)
            version = versions[0]

        key = f"{name}@{version}"
        return self._metadata.get(key)

    def export_to_dict(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Export registry to dictionary.

        Returns:
            Dictionary with all registered strategies

        Example:
            data = registry.export_to_dict()
            with open("strategies.json", "w") as f:
                json.dump(data, f, indent=2)
        """
        return {
            "strategies": self.list_strategies(),
            "count": len(self._strategies),
            "exported_at": datetime.utcnow().isoformat(),
        }

    def clear(self):
        """Clear all registered strategies (use with caution!)"""
        self._strategies.clear()
        self._metadata.clear()
        self._performance.clear()
        logger.warning("Registry cleared - all strategies removed")

    def __len__(self) -> int:
        """Return total number of registered strategies (all versions)"""
        return sum(len(versions) for versions in self._strategies.values())

    def __contains__(self, name: str) -> bool:
        """Check if a strategy name exists in registry"""
        return name in self._strategies

    def __repr__(self) -> str:
        total = len(self)
        unique_names = len(self._strategies)
        return (
            f"StrategyRegistry("
            f"strategies={unique_names}, "
            f"total_versions={total})"
        )


# Global registry instance (singleton pattern)
_global_registry: Optional[StrategyRegistry] = None


def get_registry() -> StrategyRegistry:
    """
    Get global strategy registry instance (singleton).

    Returns:
        Global StrategyRegistry instance

    Example:
        from app.research.strategies.registry import get_registry

        registry = get_registry()
        registry.register(my_strategy)
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = StrategyRegistry()

    return _global_registry
