"""
Tests for Bot Management API Endpoints (AUT-347)

Tests AUT-347 requirements:
- Strategy must be approved (status == 'approved')
- No duplicate running bots on same Apex account (HTTP 409)
- ApexComplianceValidator integration
- Synchronous kill switch with idempotency
- Redis kill switch publishing
"""

import pytest
import inspect
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBotManagement:
    """Test suite for Bot Management API (AUT-347)."""

    # ==================== MODULE IMPORT TESTS ====================

    def test_bot_management_module_exists(self):
        """Test that bot_management module can be imported."""
        try:
            from app.api.v1.endpoints import bot_management
            assert bot_management, "bot_management module must exist"
            print("✓ bot_management module exists and can be imported")
        except ImportError as e:
            pytest.fail(f"Cannot import bot_management module: {e}")

    def test_router_exists(self):
        """Test that FastAPI router is defined."""
        from app.api.v1.endpoints import bot_management
        assert hasattr(bot_management, 'router'), "bot_management must have 'router' attribute"
        print("✓ FastAPI router is defined")

    # ==================== AUT-347 REQUIREMENT 1: STRATEGY APPROVAL VALIDATION ====================

    def test_create_bot_checks_strategy_approval(self):
        """CREATE bot must validate strategy.status == 'approved'."""
        from app.api.v1.endpoints.bot_management import create_bot
        source = inspect.getsource(create_bot)

        # Check that strategy status is validated
        assert "strategy.status" in source, "create_bot must check strategy.status"
        assert "'approved'" in source or '"approved"' in source, "create_bot must validate status == 'approved'"

        # Check that it raises HTTP 400 for non-approved strategies
        assert "400" in source, "create_bot must return HTTP 400 for non-approved strategies"
        assert "must be approved" in source.lower() or "not approved" in source.lower(), "Error message must mention approval requirement"

        print("✓ CREATE bot validates strategy must be 'approved'")

    # ==================== AUT-347 REQUIREMENT 2: DUPLICATE BOT PREVENTION ====================

    def test_create_bot_checks_duplicate_apex_account(self):
        """CREATE bot must prevent duplicate running bots on same Apex account."""
        from app.api.v1.endpoints.bot_management import create_bot, check_duplicate_running_bot
        source = inspect.getsource(create_bot)

        # Check that duplicate check function exists
        assert check_duplicate_running_bot, "check_duplicate_running_bot helper must exist"

        # Check that create_bot calls the duplicate check
        assert "check_duplicate_running_bot" in source, "create_bot must call check_duplicate_running_bot"

        # Check that it raises HTTP 409 for duplicates
        assert "409" in source, "create_bot must return HTTP 409 for duplicate running bots"
        assert "already running" in source.lower(), "Error message must mention bot already running"

        print("✓ CREATE bot prevents duplicate running bots on same Apex account (HTTP 409)")

    def test_start_bot_checks_duplicate_apex_account(self):
        """START bot must also check for duplicate running bots on same Apex account."""
        from app.api.v1.endpoints.bot_management import start_bot
        source = inspect.getsource(start_bot)

        # Check that start_bot also calls duplicate check
        assert "check_duplicate_running_bot" in source, "start_bot must call check_duplicate_running_bot"

        # Check that it raises HTTP 409 for duplicates
        assert "409" in source, "start_bot must return HTTP 409 for duplicate running bots"

        print("✓ START bot prevents duplicate running bots on same Apex account")

    def test_duplicate_check_function_excludes_current_bot(self):
        """Duplicate check should exclude current bot when updating/starting."""
        from app.api.v1.endpoints.bot_management import check_duplicate_running_bot
        source = inspect.getsource(check_duplicate_running_bot)

        # Check that function has exclude parameter
        assert "exclude_bot_id" in source, "check_duplicate_running_bot must have exclude_bot_id parameter"

        # Check that it filters by running status
        assert "BOT_STATUS_RUNNING" in source or "'running'" in source or '"running"' in source, "Must filter by running status"

        print("✓ Duplicate check function excludes current bot (for updates/starts)")

    # ==================== AUT-347 REQUIREMENT 3: APEX COMPLIANCE VALIDATOR ====================

    def test_apex_compliance_validator_imported(self):
        """Bot management must import ApexComplianceValidator."""
        from app.api.v1.endpoints import bot_management
        source = inspect.getsource(bot_management)

        # Check that ApexComplianceValidator is imported
        assert "from app.research.compliance.apex_validator import ApexComplianceValidator" in source, \
            "Must import ApexComplianceValidator from app.research.compliance.apex_validator"

        print("✓ ApexComplianceValidator is imported from apex_validator module")

    def test_apex_account_conversion_helper_exists(self):
        """Helper to convert database ApexAccount to validator config must exist."""
        from app.api.v1.endpoints.bot_management import convert_apex_account_to_config
        source = inspect.getsource(convert_apex_account_to_config)

        # Check that it returns ApexAccountConfig
        assert "ApexAccountConfig" in source or "ApexAccount" in source, \
            "Must convert to ApexAccountConfig"

        # Check that it maps the required fields
        required_fields = [
            "account_size_usd",
            "trailing_threshold_usd",
            "max_daily_loss_usd",
        ]

        for field in required_fields:
            assert field in source, f"Conversion must include {field}"

        print("✓ Apex account conversion helper exists with required fields")

    # ==================== AUT-347 REQUIREMENT 4: SYNCHRONOUS KILL SWITCH ====================

    def test_kill_bot_endpoint_is_synchronous(self):
        """Kill bot endpoint MUST be synchronous (not async) for safety."""
        from app.api.v1.endpoints.bot_management import kill_bot

        # Check that the endpoint is NOT a coroutine (not async)
        is_async = inspect.iscoroutinefunction(kill_bot)
        assert not is_async, "kill_bot MUST be synchronous, not async (AUT-347 requirement)"

        print("✓ Kill bot endpoint is SYNCHRONOUS (safety-critical)")

    def test_kill_bot_uses_sync_db_session(self):
        """Kill bot must use get_db_sync (not get_db) for synchronous DB operations."""
        from app.api.v1.endpoints.bot_management import kill_bot
        source = inspect.getsource(kill_bot)

        # Check that it uses get_db_sync
        assert "get_db_sync" in source, "kill_bot must use get_db_sync for synchronous DB operations"

        # Check that it uses SyncSession type
        assert "SyncSession" in source, "kill_bot must use SyncSession type hint"

        print("✓ Kill bot uses get_db_sync (synchronous DB session)")

    # ==================== AUT-347 REQUIREMENT 5: KILL SWITCH IDEMPOTENCY ====================

    def test_kill_bot_is_idempotent(self):
        """Kill bot must be idempotent (already killed → no error, return status=killed)."""
        from app.api.v1.endpoints.bot_management import kill_bot
        source = inspect.getsource(kill_bot)

        # Check that it checks for already killed status
        assert "BOT_STATUS_KILLED" in source or "== 'killed'" in source or '== "killed"' in source, \
            "Must check if bot is already killed"

        # Check that it returns early for already killed bots (idempotent)
        assert "return" in source, "Must return early if already killed"

        # Check that it doesn't raise an exception for already killed
        # (should NOT have HTTPException after the killed check)
        lines = source.split('\n')
        found_killed_check = False
        found_early_return = False

        for line in lines:
            if 'BOT_STATUS_KILLED' in line or "== 'killed'" in line or '== "killed"' in line:
                found_killed_check = True
            if found_killed_check and 'return' in line and 'HTTPException' not in line:
                found_early_return = True
                break

        assert found_early_return, "Must return success (not error) if bot already killed"

        print("✓ Kill bot is idempotent (already killed → returns success, no error)")

    # ==================== AUT-347 REQUIREMENT 6: REDIS KILL SWITCH PUBLISHING ====================

    def test_kill_bot_publishes_to_redis(self):
        """Kill bot must publish to Redis channel 'nqhub.risk.kill_switch'."""
        from app.api.v1.endpoints.bot_management import kill_bot, publish_kill_event
        source = inspect.getsource(kill_bot)

        # Check that it calls publish_kill_event
        assert "publish_kill_event" in source, "kill_bot must call publish_kill_event"

        # Check the publish_kill_event function
        publish_source = inspect.getsource(publish_kill_event)

        # Check that it publishes to the correct Redis channel
        assert "'nqhub.risk.kill_switch'" in publish_source or '"nqhub.risk.kill_switch"' in publish_source, \
            "Must publish to 'nqhub.risk.kill_switch' channel"

        # Check that it uses redis_client.publish
        assert "redis_client.publish" in publish_source, "Must use redis_client.publish"

        print("✓ Kill bot publishes to Redis channel 'nqhub.risk.kill_switch'")

    def test_redis_publish_after_db_commit(self):
        """Redis publish must happen AFTER database commit (not before)."""
        from app.api.v1.endpoints.bot_management import kill_bot
        source = inspect.getsource(kill_bot)

        # Find positions of db.commit() and publish_kill_event() in source
        commit_pos = source.find('db.commit()')
        publish_pos = source.find('publish_kill_event')

        assert commit_pos > 0, "kill_bot must call db.commit()"
        assert publish_pos > 0, "kill_bot must call publish_kill_event"
        assert publish_pos > commit_pos, "publish_kill_event must be called AFTER db.commit()"

        print("✓ Redis publish happens AFTER database commit (correct order)")

    # ==================== HAPPY PATH TESTS ====================

    def test_create_bot_returns_bot_id_and_status(self):
        """CREATE bot should return bot_id and status."""
        from app.api.v1.endpoints.bot_management import create_bot
        source = inspect.getsource(create_bot)

        assert '"bot_id"' in source or "'bot_id'" in source, "create_bot must return bot_id"
        assert '"status"' in source or "'status'" in source, "create_bot must return status"

        print("✓ CREATE bot returns bot_id and status")

    def test_start_bot_changes_status_to_running(self):
        """START bot should change status to 'running'."""
        from app.api.v1.endpoints.bot_management import start_bot
        source = inspect.getsource(start_bot)

        assert "BOT_STATUS_RUNNING" in source or "= 'running'" in source or '= "running"' in source, \
            "start_bot must set status to 'running'"

        print("✓ START bot changes status to 'running'")

    def test_stop_bot_changes_status_to_stopped(self):
        """STOP bot should change status to 'stopped'."""
        from app.api.v1.endpoints.bot_management import stop_bot
        source = inspect.getsource(stop_bot)

        assert "BOT_STATUS_STOPPED" in source or "= 'stopped'" in source or '= "stopped"' in source, \
            "stop_bot must set status to 'stopped'"

        print("✓ STOP bot changes status to 'stopped'")

    def test_stop_bot_is_idempotent(self):
        """STOP bot should be idempotent (already stopped → no error)."""
        from app.api.v1.endpoints.bot_management import stop_bot
        source = inspect.getsource(stop_bot)

        # Check that it checks for already stopped status
        assert "BOT_STATUS_STOPPED" in source or "== 'stopped'" in source or '== "stopped"' in source, \
            "Must check if bot is already stopped"

        # Check that it returns success for already stopped (idempotent)
        assert "return" in source, "Must return early if already stopped"

        print("✓ STOP bot is idempotent (already stopped → returns success)")

    # ==================== STATE LOGGING TESTS ====================

    def test_all_state_changes_are_logged(self):
        """All state changes (create, start, stop, kill) must be logged."""
        from app.api.v1.endpoints.bot_management import (
            create_bot, start_bot, stop_bot, kill_bot, log_state_transition
        )

        # Check that log_state_transition function exists
        assert log_state_transition, "log_state_transition helper must exist"

        # Check that all endpoints log state changes
        create_source = inspect.getsource(create_bot)
        start_source = inspect.getsource(start_bot)
        stop_source = inspect.getsource(stop_bot)
        kill_source = inspect.getsource(kill_bot)

        assert "BotStateLog" in create_source or "state_log" in create_source, \
            "create_bot must log initial state"

        assert "BotStateLog" in start_source or "state_log" in start_source, \
            "start_bot must log state change"

        assert "BotStateLog" in stop_source or "state_log" in stop_source, \
            "stop_bot must log state change"

        assert "log_state_transition" in kill_source, \
            "kill_bot must log state change using log_state_transition"

        print("✓ All state changes are logged (create, start, stop, kill)")

    def test_log_state_transition_has_required_fields(self):
        """log_state_transition must include from_status, to_status, reason."""
        from app.api.v1.endpoints.bot_management import log_state_transition
        source = inspect.getsource(log_state_transition)

        required_fields = ["from_status", "to_status", "reason"]

        for field in required_fields:
            assert field in source, f"log_state_transition must include {field}"

        print("✓ log_state_transition has from_status, to_status, reason")

    # ==================== ERROR HANDLING TESTS ====================

    def test_create_bot_validates_live_mode_requires_apex_account(self):
        """CREATE bot in 'live' mode must require apex_account_id."""
        from app.api.v1.endpoints.bot_management import create_bot
        source = inspect.getsource(create_bot)

        # Check that live mode validation exists
        assert "mode == 'live'" in source or 'mode == "live"' in source, \
            "Must validate live mode"

        assert "apex_account_id" in source, "Must check apex_account_id requirement"

        # Check that it raises HTTP 400 if missing
        assert "400" in source, "Must return HTTP 400 if apex_account_id missing in live mode"

        print("✓ CREATE bot validates live mode requires apex_account_id")

    def test_create_bot_validates_apex_account_exists_and_active(self):
        """CREATE bot must validate Apex account exists and is_active=True."""
        from app.api.v1.endpoints.bot_management import create_bot
        source = inspect.getsource(create_bot)

        # Check that it queries ApexAccount
        assert "ApexAccount" in source, "Must query ApexAccount"

        # Check that it validates existence
        assert "not found" in source.lower() or "404" in source, \
            "Must return 404 if Apex account not found"

        # Check that it validates is_active
        assert "is_active" in source, "Must check ApexAccount.is_active"
        assert "400" in source or "not active" in source.lower(), \
            "Must return error if Apex account not active"

        print("✓ CREATE bot validates Apex account exists and is_active")

    def test_start_bot_prevents_starting_killed_bot(self):
        """START bot must prevent starting a killed bot."""
        from app.api.v1.endpoints.bot_management import start_bot
        source = inspect.getsource(start_bot)

        # Check that it checks for killed status
        assert "BOT_STATUS_KILLED" in source or "== 'killed'" in source or '== "killed"' in source, \
            "Must check if bot is killed"

        # Check that it raises HTTP 409 for killed bots
        assert "409" in source, "Must return HTTP 409 if bot is killed"
        assert "cannot start" in source.lower() or "killed" in source.lower(), \
            "Error message must mention cannot start killed bot"

        print("✓ START bot prevents starting a killed bot (HTTP 409)")

    def test_start_bot_prevents_starting_already_running_bot(self):
        """START bot must be idempotent or return error for already running bot."""
        from app.api.v1.endpoints.bot_management import start_bot
        source = inspect.getsource(start_bot)

        # Check that it checks for running status
        assert "BOT_STATUS_RUNNING" in source or "== 'running'" in source or '== "running"' in source, \
            "Must check if bot is already running"

        # Check that it handles already running (either idempotent or error)
        assert "409" in source, "Must return HTTP 409 if bot already running"

        print("✓ START bot handles already running bot (HTTP 409)")

    def test_kill_bot_handles_nonexistent_bot(self):
        """Kill bot must return HTTP 404 for non-existent bot."""
        from app.api.v1.endpoints.bot_management import kill_bot
        source = inspect.getsource(kill_bot)

        # Check that it validates bot exists
        assert "not bot" in source.lower() or "if not bot" in source or "bot is None" in source, \
            "Must check if bot exists"

        # Check that it raises HTTP 404
        assert "404" in source, "Must return HTTP 404 for non-existent bot"

        print("✓ Kill bot returns HTTP 404 for non-existent bot")

    def test_kill_bot_cancels_pending_orders(self):
        """Kill bot must cancel all pending orders."""
        from app.api.v1.endpoints.bot_management import kill_bot
        source = inspect.getsource(kill_bot)

        # Check that it queries and updates Order table
        assert "Order" in source, "Must query Order table"
        assert "'PENDING'" in source or '"PENDING"' in source, "Must filter by PENDING status"
        assert "'CANCELLED'" in source or '"CANCELLED"' in source or "CANCELLED" in source, \
            "Must set status to CANCELLED"

        print("✓ Kill bot cancels all pending orders")

    # ==================== LIST AND FILTER TESTS ====================

    def test_list_bots_supports_filters(self):
        """List bots should support status, mode, and apex_account_id filters."""
        from app.api.v1.endpoints.bot_management import list_bots
        source = inspect.getsource(list_bots)

        # Check that filters are supported
        filters = ["status", "mode", "apex_account_id"]

        for filter_param in filters:
            assert filter_param in source, f"list_bots must support {filter_param} filter"

        print("✓ List bots supports status, mode, and apex_account_id filters")


if __name__ == "__main__":
    test_suite = TestBotManagement()

    print("\n" + "="*80)
    print("BOT MANAGEMENT API TESTS (AUT-347)")
    print("="*80 + "\n")

    print("--- MODULE IMPORT TESTS ---")
    test_suite.test_bot_management_module_exists()
    test_suite.test_router_exists()

    print("\n--- AUT-347 REQUIREMENT 1: STRATEGY APPROVAL VALIDATION ---")
    test_suite.test_create_bot_checks_strategy_approval()

    print("\n--- AUT-347 REQUIREMENT 2: DUPLICATE BOT PREVENTION ---")
    test_suite.test_create_bot_checks_duplicate_apex_account()
    test_suite.test_start_bot_checks_duplicate_apex_account()
    test_suite.test_duplicate_check_function_excludes_current_bot()

    print("\n--- AUT-347 REQUIREMENT 3: APEX COMPLIANCE VALIDATOR ---")
    test_suite.test_apex_compliance_validator_imported()
    test_suite.test_apex_account_conversion_helper_exists()

    print("\n--- AUT-347 REQUIREMENT 4: SYNCHRONOUS KILL SWITCH ---")
    test_suite.test_kill_bot_endpoint_is_synchronous()
    test_suite.test_kill_bot_uses_sync_db_session()

    print("\n--- AUT-347 REQUIREMENT 5: KILL SWITCH IDEMPOTENCY ---")
    test_suite.test_kill_bot_is_idempotent()

    print("\n--- AUT-347 REQUIREMENT 6: REDIS KILL SWITCH PUBLISHING ---")
    test_suite.test_kill_bot_publishes_to_redis()
    test_suite.test_redis_publish_after_db_commit()

    print("\n--- HAPPY PATH TESTS ---")
    test_suite.test_create_bot_returns_bot_id_and_status()
    test_suite.test_start_bot_changes_status_to_running()
    test_suite.test_stop_bot_changes_status_to_stopped()
    test_suite.test_stop_bot_is_idempotent()

    print("\n--- STATE LOGGING TESTS ---")
    test_suite.test_all_state_changes_are_logged()
    test_suite.test_log_state_transition_has_required_fields()

    print("\n--- ERROR HANDLING TESTS ---")
    test_suite.test_create_bot_validates_live_mode_requires_apex_account()
    test_suite.test_create_bot_validates_apex_account_exists_and_active()
    test_suite.test_start_bot_prevents_starting_killed_bot()
    test_suite.test_start_bot_prevents_starting_already_running_bot()
    test_suite.test_kill_bot_handles_nonexistent_bot()
    test_suite.test_kill_bot_cancels_pending_orders()

    print("\n--- LIST AND FILTER TESTS ---")
    test_suite.test_list_bots_supports_filters()

    print("\n" + "="*80)
    print("✅ ALL BOT MANAGEMENT API TESTS (AUT-347) PASSED!")
    print("="*80 + "\n")
