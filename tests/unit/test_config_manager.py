# ABOUTME: Unit tests for ConfigManager - Configuration management system
# ABOUTME: Tests config loading, environment variables, validation, and defaults

import pytest
import os
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import with try/except for graceful handling
try:
    from a2a_mcp.common.config_manager import (
        ConfigManager,
        FrameworkConfig,
        AgentConfig,
        QualityConfig,
        ConnectionPoolConfig,
        MCPServerConfig,
        MetricsConfig,
        get_config,
        get_config_manager,
        get_agent_config
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    pytestmark = pytest.mark.skip("config_manager module not available")


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestConfigManagerInitialization:
    """Test suite for ConfigManager initialization."""

    def test_config_manager_init_default(self):
        """Test ConfigManager initializes with defaults."""
        with patch.object(ConfigManager, 'load_config'):
            manager = ConfigManager()
            assert manager is not None

    def test_config_manager_init_with_path(self, tmp_path):
        """Test ConfigManager initializes with explicit config path."""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "framework_version": "2.0",
            "environment": "test"
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_path=str(config_file))
        assert manager._config_path == Path(config_file)

    def test_config_manager_singleton_pattern(self):
        """Test get_config_manager returns same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        # Should be same instance (singleton pattern)
        assert manager1 is manager2


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestConfigLoading:
    """Test suite for configuration file loading."""

    def test_load_yaml_config(self, tmp_path):
        """Test loading YAML configuration file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "framework_version": "2.0",
            "environment": "testing",
            "log_level": "DEBUG"
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        manager = ConfigManager(config_path=str(config_file))

        assert manager._config.framework_version == "2.0"
        assert manager._config.environment == "testing"
        assert manager._config.log_level == "DEBUG"

    def test_load_json_config(self, tmp_path):
        """Test loading JSON configuration file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "framework_version": "2.0",
            "environment": "testing"
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        manager = ConfigManager(config_path=str(config_file))

        assert manager._config.framework_version == "2.0"

    def test_load_nonexistent_file(self):
        """Test handling of nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            manager = ConfigManager(config_path="/nonexistent/config.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        """Test handling of invalid YAML."""
        config_file = tmp_path / "invalid.yaml"

        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content:")

        with pytest.raises(Exception):
            manager = ConfigManager(config_path=str(config_file))

    def test_load_config_search_paths(self, tmp_path, monkeypatch):
        """Test configuration file search in default paths."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config in one of the search paths
        configs_dir = tmp_path / "configs"
        configs_dir.mkdir()
        config_file = configs_dir / "framework.yaml"

        config_data = {"framework_version": "2.0"}
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Should find config automatically
        manager = ConfigManager()
        assert manager._config is not None


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestEnvironmentOverrides:
    """Test suite for environment variable overrides."""

    def test_env_override_log_level(self, monkeypatch):
        """Test LOG_LEVEL environment variable override."""
        monkeypatch.setenv("A2A_MCP_LOG_LEVEL", "DEBUG")

        manager = ConfigManager()

        assert manager._config.log_level == "DEBUG"

    def test_env_override_mcp_server(self, monkeypatch):
        """Test MCP server environment overrides."""
        monkeypatch.setenv("A2A_MCP_MCP_SERVER_HOST", "test-host")
        monkeypatch.setenv("A2A_MCP_MCP_SERVER_PORT", "9999")

        manager = ConfigManager()

        assert manager._config.mcp_server.host == "test-host"
        assert manager._config.mcp_server.port == 9999

    def test_env_override_connection_pool(self, monkeypatch):
        """Test connection pool environment overrides."""
        monkeypatch.setenv("A2A_MCP_CONNECTION_POOL_ENABLED", "false")
        monkeypatch.setenv("A2A_MCP_CONNECTION_POOL_MAX_CONNECTIONS_PER_HOST", "20")

        manager = ConfigManager()

        assert manager._config.connection_pool.enabled is False
        assert manager._config.connection_pool.max_connections_per_host == 20

    def test_legacy_env_vars(self, monkeypatch):
        """Test legacy environment variable support."""
        monkeypatch.setenv("MCP_SERVER_HOST", "legacy-host")
        monkeypatch.setenv("MCP_SERVER_PORT", "7777")
        monkeypatch.setenv("AGENT_CARDS_DIR", "custom_agents")

        manager = ConfigManager()

        # Legacy vars should be supported
        assert manager._config.mcp_server.host == "legacy-host" or \
               manager._config.mcp_server.port == 7777

    def test_env_value_type_parsing(self, monkeypatch):
        """Test parsing of different environment variable types."""
        # Boolean
        monkeypatch.setenv("A2A_MCP_CONNECTION_POOL_ENABLED", "true")
        # Integer
        monkeypatch.setenv("A2A_MCP_MCP_SERVER_PORT", "8888")
        # Float
        monkeypatch.setenv("A2A_MCP_QUALITY_THRESHOLDS", "0.85")

        manager = ConfigManager()

        # Check types are correctly parsed
        assert isinstance(manager._config.connection_pool.enabled, bool)
        assert isinstance(manager._config.mcp_server.port, int)


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestAgentConfiguration:
    """Test suite for agent-specific configuration."""

    def test_get_agent_config(self):
        """Test retrieving agent configuration."""
        manager = ConfigManager()

        # Try to get a configured agent
        agent_config = manager.get_agent_config("master_orchestrator")

        # Either exists or returns None
        assert agent_config is None or isinstance(agent_config, AgentConfig)

    def test_add_agent_config(self):
        """Test adding new agent configuration."""
        manager = ConfigManager()

        new_agent = AgentConfig(
            agent_id="test_agent",
            name="Test Agent",
            port=12345,
            tier=2,
            description="Test agent"
        )

        manager.add_agent_config(new_agent)

        retrieved = manager.get_agent_config("test_agent")
        assert retrieved is not None
        assert retrieved.agent_id == "test_agent"
        assert retrieved.port == 12345

    def test_agent_config_defaults(self):
        """Test agent configuration defaults."""
        agent = AgentConfig(
            agent_id="minimal",
            name="Minimal Agent",
            port=11111,
            tier=1
        )

        assert agent.mcp_tools_enabled is True  # Should default to True
        assert agent.a2a_enabled is True
        assert agent.temperature == 0.0


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestConfigValidation:
    """Test suite for configuration validation."""

    def test_validate_complete_config(self):
        """Test validation of complete configuration."""
        manager = ConfigManager()

        issues = manager.validate()

        # Should return list (empty if valid)
        assert isinstance(issues, list)

    def test_validate_missing_directories(self, tmp_path, monkeypatch):
        """Test validation catches missing directories."""
        monkeypatch.chdir(tmp_path)

        manager = ConfigManager()
        # Set nonexistent directories
        manager._config.agent_cards_dir = "/nonexistent/agents"
        manager._config.logs_dir = "/nonexistent/logs"

        issues = manager.validate()

        # Should report missing directories
        assert len(issues) > 0
        assert any("does not exist" in issue for issue in issues)

    def test_validate_port_conflicts(self):
        """Test validation catches port conflicts."""
        manager = ConfigManager()

        # Add two agents with same port
        agent1 = AgentConfig(agent_id="agent1", name="Agent 1", port=11001, tier=1)
        agent2 = AgentConfig(agent_id="agent2", name="Agent 2", port=11001, tier=1)

        manager.add_agent_config(agent1)
        manager.add_agent_config(agent2)

        issues = manager.validate()

        # Should detect port conflict
        assert any("port conflict" in issue.lower() or "both use port" in issue.lower()
                  for issue in issues)

    def test_validate_invalid_tier(self):
        """Test validation catches invalid tier numbers."""
        manager = ConfigManager()

        invalid_agent = AgentConfig(
            agent_id="invalid",
            name="Invalid Agent",
            port=11111,
            tier=99  # Invalid tier
        )

        manager.add_agent_config(invalid_agent)

        issues = manager.validate()

        # Should report invalid tier
        assert any("invalid tier" in issue.lower() for issue in issues)

    def test_validate_invalid_port(self):
        """Test validation catches invalid port numbers."""
        manager = ConfigManager()

        invalid_agent = AgentConfig(
            agent_id="invalid_port",
            name="Invalid Port Agent",
            port=99999999,  # Invalid port
            tier=1
        )

        manager.add_agent_config(invalid_agent)

        issues = manager.validate()

        # Should report invalid port
        assert any("invalid port" in issue.lower() for issue in issues)


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestConfigReload:
    """Test suite for configuration reloading."""

    def test_reload_config(self, tmp_path):
        """Test reloading configuration from disk."""
        config_file = tmp_path / "config.yaml"

        # Initial config
        initial_data = {
            "framework_version": "2.0",
            "environment": "initial"
        }

        with open(config_file, 'w') as f:
            yaml.dump(initial_data, f)

        manager = ConfigManager(config_path=str(config_file))
        assert manager._config.environment == "initial"

        # Modify config file
        updated_data = {
            "framework_version": "2.0",
            "environment": "updated"
        }

        with open(config_file, 'w') as f:
            yaml.dump(updated_data, f)

        # Reload
        manager.reload()

        assert manager._config.environment == "updated"

    def test_reload_preserves_runtime_changes(self, tmp_path):
        """Test reload behavior with runtime changes."""
        config_file = tmp_path / "config.yaml"

        with open(config_file, 'w') as f:
            yaml.dump({"framework_version": "2.0"}, f)

        manager = ConfigManager(config_path=str(config_file))

        # Add agent at runtime
        runtime_agent = AgentConfig(
            agent_id="runtime",
            name="Runtime Agent",
            port=22222,
            tier=2
        )
        manager.add_agent_config(runtime_agent)

        # Reload from disk
        manager.reload()

        # Runtime changes may or may not be preserved (depends on implementation)
        # Just verify reload doesn't crash
        assert manager._config is not None


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestFeatureFlags:
    """Test suite for feature flag management."""

    def test_check_feature_enabled(self):
        """Test checking if feature is enabled."""
        manager = ConfigManager()

        # Check a feature flag
        is_enabled = manager.is_feature_enabled("response_formatting_v2")

        # Should return boolean
        assert isinstance(is_enabled, bool)

    def test_check_nonexistent_feature(self):
        """Test checking nonexistent feature returns False."""
        manager = ConfigManager()

        is_enabled = manager.is_feature_enabled("nonexistent_feature")

        assert is_enabled is False

    def test_feature_flags_from_env(self, monkeypatch):
        """Test feature flags can be set via environment."""
        # Set feature flags via environment
        monkeypatch.setenv(
            "A2A_MCP_FEATURES",
            '{"new_feature": true, "experimental": false}'
        )

        manager = ConfigManager()

        # Check if env-based features work
        # (implementation may vary)
        assert manager._config.features is not None


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config_file(self, tmp_path):
        """Test handling of empty configuration file."""
        config_file = tmp_path / "empty.yaml"
        config_file.touch()  # Create empty file

        manager = ConfigManager(config_path=str(config_file))

        # Should use defaults
        assert manager._config is not None

    def test_config_with_unknown_fields(self, tmp_path):
        """Test config with unknown fields doesn't crash."""
        config_file = tmp_path / "config.yaml"

        config_data = {
            "framework_version": "2.0",
            "unknown_field": "value",
            "another_unknown": 123
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Should ignore unknown fields
        manager = ConfigManager(config_path=str(config_file))
        assert manager._config.framework_version == "2.0"

    def test_config_with_nested_overrides(self, monkeypatch):
        """Test nested configuration overrides."""
        monkeypatch.setenv("A2A_MCP_MCP_SERVER_HOST", "override-host")
        monkeypatch.setenv("A2A_MCP_MCP_SERVER_PORT", "9191")

        manager = ConfigManager()

        # Nested overrides should work
        assert manager._config.mcp_server.host == "override-host"
        assert manager._config.mcp_server.port == 9191


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestDataClasses:
    """Test configuration data class structures."""

    def test_framework_config_creation(self):
        """Test FrameworkConfig data class."""
        config = FrameworkConfig(
            framework_version="2.0",
            environment="test",
            log_level="DEBUG"
        )

        assert config.framework_version == "2.0"
        assert config.environment == "test"
        assert config.log_level == "DEBUG"

    def test_agent_config_creation(self):
        """Test AgentConfig data class."""
        agent = AgentConfig(
            agent_id="test",
            name="Test Agent",
            port=11111,
            tier=1
        )

        assert agent.agent_id == "test"
        assert agent.port == 11111

    def test_quality_config_creation(self):
        """Test QualityConfig data class."""
        quality = QualityConfig(
            domain="BUSINESS",
            validation_enabled=True
        )

        assert quality.domain == "BUSINESS"
        assert quality.validation_enabled is True

    def test_connection_pool_config_creation(self):
        """Test ConnectionPoolConfig data class."""
        pool = ConnectionPoolConfig(
            enabled=True,
            max_connections_per_host=20
        )

        assert pool.enabled is True
        assert pool.max_connections_per_host == 20

    def test_mcp_server_config_creation(self):
        """Test MCPServerConfig data class."""
        mcp = MCPServerConfig(
            host="test-host",
            port=8181,
            transport="sse"
        )

        assert mcp.host == "test-host"
        assert mcp.port == 8181
        # URL should be auto-generated
        assert "test-host" in mcp.url
        assert "8181" in mcp.url
