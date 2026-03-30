"""
BacktestOptimizer - Grid search and walk-forward optimization using VectorBT Pro.

Runs N backtests in parallel (4-16 workers configurable).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Type, Optional, Tuple
from itertools import product
from datetime import datetime, timedelta
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing

from app.research.backtesting.engine import BacktestEngine, ApexValidator
from app.research.backtesting.schemas import (
    BacktestConfig,
    BacktestResults,
    OptimizationConfig,
    OptimizationResults
)
from app.research.strategies.base import NQHubStrategy


class BacktestOptimizer:
    """
    Grid search and walk-forward optimization using vbt.Portfolio.

    Runs N backtests in parallel (4-16 workers configurable).
    """

    def __init__(self, n_jobs: int = 4, apex_validator=None):
        """Initialize the BacktestOptimizer.

        Args:
            n_jobs: Number of parallel jobs for optimization
            apex_validator: Optional ApexValidator instance
        """
        self.n_jobs = min(n_jobs, multiprocessing.cpu_count())
        self.apex_validator = apex_validator or ApexValidator()
        self.engine = BacktestEngine(apex_validator=self.apex_validator)

    def grid_search(
        self,
        strategy_class: Type[NQHubStrategy],
        param_grid: Dict[str, List[Any]],
        candles: pd.DataFrame,
        config: Optional[BacktestConfig] = None
    ) -> List[BacktestResults]:
        """
        Iterate over parameter combinations, run backtest for each one.

        Args:
            strategy_class: Strategy class to optimize
            param_grid: Dictionary mapping parameter names to lists of values
            candles: DataFrame with OHLCV data
            config: Optional base BacktestConfig (will use defaults if not provided)

        Returns:
            List of BacktestResults for all parameter combinations
        """
        # Create base config if not provided
        if config is None:
            config = BacktestConfig(
                strategy_id=strategy_class.__name__,
                timeframe="1min",
                start_date=candles.index[0] if hasattr(candles.index, '__getitem__') else datetime.now(),
                end_date=candles.index[-1] if hasattr(candles.index, '__getitem__') else datetime.now()
            )

        # Generate all parameter combinations
        param_combinations = self._generate_param_combinations(param_grid)

        # If no parameters, run single backtest with default
        if len(param_combinations) == 0:
            strategy = strategy_class()
            results = self.engine.run_backtest(strategy, candles, config)
            return [results]

        # Run backtests in parallel
        results = []
        if self.n_jobs == 1:
            # Sequential execution
            for params in param_combinations:
                result = self._run_single_backtest(
                    strategy_class, params, candles, config
                )
                results.append(result)
        else:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []
                for params in param_combinations:
                    future = executor.submit(
                        self._run_single_backtest,
                        strategy_class, params, candles, config
                    )
                    futures.append(future)

                # Collect results
                for future in futures:
                    result = future.result()
                    results.append(result)

        return results

    def walk_forward(
        self,
        strategy_class: Type[NQHubStrategy],
        candles: pd.DataFrame,
        n_splits: int = 5,
        train_ratio: float = 0.7,
        param_grid: Optional[Dict[str, List[Any]]] = None
    ) -> List[BacktestResults]:
        """
        Walk-forward validation: rolling windows of train/test.

        Args:
            strategy_class: Strategy class to test
            candles: DataFrame with OHLCV data
            n_splits: Number of train/test splits
            train_ratio: Ratio of data to use for training
            param_grid: Optional parameter grid for optimization in each split

        Returns:
            List of BacktestResults for each split
        """
        # Validate inputs
        if len(candles) < n_splits * 10:
            raise ValueError(
                f"Insufficient data for {n_splits} splits. "
                f"Have {len(candles)} rows, need at least {n_splits * 10}"
            )

        # Calculate split sizes
        total_size = len(candles)
        split_size = total_size // n_splits
        train_size = int(split_size * train_ratio)
        test_size = split_size - train_size

        results = []

        for i in range(n_splits):
            # Calculate split indices
            start_idx = i * test_size
            train_end_idx = start_idx + train_size
            test_end_idx = min(train_end_idx + test_size, total_size)

            # Split data
            train_data = candles.iloc[start_idx:train_end_idx]
            test_data = candles.iloc[train_end_idx:test_end_idx]

            if len(test_data) == 0:
                continue

            # If param_grid provided, optimize on train data
            if param_grid:
                # Find best parameters on training data
                train_results = self.grid_search(
                    strategy_class=strategy_class,
                    param_grid=param_grid,
                    candles=train_data
                )

                # Select best parameters (highest Sharpe ratio)
                best_result = max(train_results, key=lambda r: r.sharpe_ratio)
                best_params = best_result.strategy_params

                # Test on out-of-sample data with best parameters
                strategy = strategy_class(**best_params)
            else:
                # Use default parameters
                strategy = strategy_class()

            # Run backtest on test data
            config = BacktestConfig(
                strategy_id=f"{strategy_class.__name__}_split_{i}",
                timeframe="1min",
                start_date=test_data.index[0] if hasattr(test_data.index, '__getitem__') else datetime.now(),
                end_date=test_data.index[-1] if hasattr(test_data.index, '__getitem__') else datetime.now()
            )

            result = self.engine.run_backtest(strategy, test_data, config)

            # Mark this as a walk-forward split result
            result.backtest_id = f"{result.backtest_id}_split_{i}"

            results.append(result)

        return results

    def _generate_param_combinations(
        self, param_grid: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate all combinations of parameters from grid.

        Args:
            param_grid: Dictionary mapping parameter names to lists of values

        Returns:
            List of parameter dictionaries
        """
        if not param_grid:
            return []

        # Get parameter names and value lists
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        # Generate all combinations
        combinations = []
        for values in product(*param_values):
            param_dict = dict(zip(param_names, values))
            combinations.append(param_dict)

        return combinations

    def _run_single_backtest(
        self,
        strategy_class: Type[NQHubStrategy],
        params: Dict[str, Any],
        candles: pd.DataFrame,
        config: BacktestConfig
    ) -> BacktestResults:
        """
        Run a single backtest with given parameters.

        Args:
            strategy_class: Strategy class to instantiate
            params: Parameters for the strategy
            candles: DataFrame with OHLCV data
            config: Backtest configuration

        Returns:
            BacktestResults for this parameter combination
        """
        # Instantiate strategy with parameters
        strategy = strategy_class(**params) if params else strategy_class()

        # Run backtest
        results = self.engine.run_backtest(strategy, candles, config)

        # Store parameters in results
        results.strategy_params = params

        return results

    def find_best_parameters(
        self,
        results: List[BacktestResults],
        metric: str = "sharpe_ratio"
    ) -> Tuple[Dict[str, Any], BacktestResults]:
        """
        Find best parameters from optimization results.

        Args:
            results: List of BacktestResults from optimization
            metric: Metric to optimize (sharpe_ratio, total_return, profit_factor)

        Returns:
            Tuple of (best_parameters, best_result)
        """
        if not results:
            raise ValueError("No results to analyze")

        # Find best result by metric
        best_result = max(results, key=lambda r: getattr(r, metric, 0))
        best_params = best_result.strategy_params or {}

        return best_params, best_result

    def create_optimization_report(
        self,
        results: List[BacktestResults],
        optimization_type: str = "grid_search",
        metric: str = "sharpe_ratio"
    ) -> OptimizationResults:
        """
        Create a comprehensive optimization report.

        Args:
            results: List of BacktestResults
            optimization_type: Type of optimization performed
            metric: Metric that was optimized

        Returns:
            OptimizationResults with summary and all results
        """
        if not results:
            raise ValueError("No results to create report from")

        # Find best parameters
        best_params, best_result = self.find_best_parameters(results, metric)

        # Create optimization results
        return OptimizationResults(
            optimization_id=str(uuid.uuid4()),
            optimization_type=optimization_type,
            strategy_class=results[0].strategy_id.split('_')[0] if results else "Unknown",
            best_params=best_params,
            best_metric_value=getattr(best_result, metric, 0),
            best_backtest_id=best_result.backtest_id,
            all_results=results,
            n_iterations=len(results)
        )

    def parallel_optimization(
        self,
        strategy_classes: List[Type[NQHubStrategy]],
        param_grids: List[Dict[str, List[Any]]],
        candles: pd.DataFrame
    ) -> Dict[str, OptimizationResults]:
        """
        Run optimization for multiple strategies in parallel.

        Args:
            strategy_classes: List of strategy classes to optimize
            param_grids: List of parameter grids (one per strategy)
            candles: DataFrame with OHLCV data

        Returns:
            Dictionary mapping strategy names to optimization results
        """
        if len(strategy_classes) != len(param_grids):
            raise ValueError("Number of strategies must match number of param grids")

        results_map = {}

        with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = {}

            # Submit optimization tasks
            for strategy_class, param_grid in zip(strategy_classes, param_grids):
                future = executor.submit(
                    self.grid_search,
                    strategy_class,
                    param_grid,
                    candles
                )
                futures[future] = strategy_class.__name__

            # Collect results
            for future in futures:
                strategy_name = futures[future]
                results = future.result()
                optimization_report = self.create_optimization_report(
                    results,
                    optimization_type="grid_search"
                )
                results_map[strategy_name] = optimization_report

        return results_map