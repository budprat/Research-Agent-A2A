# ABOUTME: Centralized configuration management for Framework V2.0
# ABOUTME: Provides unified config loading, validation, and environment variable management

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List, Union, Type
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent-specific configuration."""
    agent_id: str
    name: str
    port: int
    tier: int = 1
    description: str = ""
    instructions: str = ""
    capabilities: List[str] = field(default_factory=list)
    quality_domain: str = "SERVICE"
    temperature: float = 0.0
    model: str = "gemini-2.0-flash"
    mcp_tools_enabled: bool = True
    a2a_enabled: bool = True
    memory: Optional[Dict[str, Any]] = None  # Memory configuration
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityConfig:
    """Quality framework configuration."""
    domain: str = "GENERIC"
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "accuracy": 0.8,
        "completeness": 0.9,
        "relevance": 0.85
    })
    validation_enabled: bool = True
    strict_mode: bool = False


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration."""
    enabled: bool = True
    max_connections_per_host: int = 10
    max_keepalive_connections: int = 5
    keepalive_timeout: int = 30
    connection_timeout: int = 10
    total_timeout: int = 60
    health_check_interval: int = 300
    cleanup_interval: int = 600


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    host: str = "localhost"
    port: int = 10099
    transport: str = "sse"
    url: Optional[str] = None
    
    def __post_init__(self):
        """Generate URL if not provided."""
        if not self.url:
            if self.transport == "sse":
                self.url = f"http://{self.host}:{self.port}/sse"
            else:
                self.url = f"http://{self.host}:{self.port}"


@dataclass
class MetricsConfig:
    """Metrics and monitoring configuration."""
    enabled: bool = False
    prometheus_port: int = 9090
    export_interval: int = 30
    include_system_metrics: bool = True
    custom_labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class FrameworkConfig:
    """Complete Framework V2.0 configuration."""
    # Core settings
    framework_version: str = "2.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # Component configs
    mcp_server: MCPServerConfig = field(default_factory=MCPServerConfig)
    connection_pool: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = field(default_factory=dict)
    
    # Paths
    agent_cards_dir: str = "agent_cards"
    config_dir: str = "configs"
    logs_dir: str = "logs"
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "response_formatting_v2": True,
        "connection_pooling": True,
        "quality_validation": True,
        "prometheus_metrics": False,
        "advanced_routing": False
    })


class ConfigManager:
    """
    Centralized configuration manager for Framework V2.0.
    
    Provides:
    - Environment variable resolution
    - Multi-format config loading (JSON, YAML, env)
    - Configuration validation
    - Dynamic reload support
    - Type-safe access patterns
    """
    
    # Environment variable prefix
    ENV_PREFIX = "A2A_MCP_"
    
    # Config file search paths
    DEFAULT_CONFIG_PATHS = [
        "configs/framework.yaml",
        "configs/framework.json",
        ".a2a-mcp-config.yaml",
        ".a2a-mcp-config.json",
        os.path.expanduser("~/.a2a-mcp/config.yaml"),
        "/etc/a2a-mcp/config.yaml"
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Explicit path to config file (overrides search)
        """
        self._config: Optional[FrameworkConfig] = None
        self._config_path: Optional[Path] = None
        self._env_overrides: Dict[str, Any] = {}
        self._load_time: Optional[datetime] = None
        
        # Load configuration
        self.load_config(config_path)
        
    def load_config(self, config_path: Optional[str] = None) -> FrameworkConfig:
        """
        Load configuration from files and environment.
        
        Args:
            config_path: Explicit config file path
            
        Returns:
            Loaded FrameworkConfig instance
        """
        # Start with defaults
        config_dict = {}
        
        # Load from file
        if config_path:
            config_dict = self._load_config_file(Path(config_path))
            self._config_path = Path(config_path)
        else:
            # Search default paths
            for path_str in self.DEFAULT_CONFIG_PATHS:
                path = Path(path_str)
                if path.exists():
                    logger.info(f"Loading config from: {path}")
                    config_dict = self._load_config_file(path)
                    self._config_path = path
                    break
        
        # Apply environment overrides
        config_dict = self._apply_env_overrides(config_dict)
        
        # Convert to FrameworkConfig
        self._config = self._dict_to_config(config_dict)
        self._load_time = datetime.now()
        
        logger.info(f"Configuration loaded (environment: {self._config.environment})")
        return self._config
    
    def _load_config_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
            
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            elif path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}")
    
    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # Scan for A2A_MCP_* environment variables
        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                # Convert A2A_MCP_LOG_LEVEL to log_level
                config_key = key[len(self.ENV_PREFIX):].lower()
                
                # Handle nested keys (A2A_MCP_MCP_SERVER_PORT -> mcp_server.port)
                keys = config_key.split('_')
                self._set_nested_value(config_dict, keys, self._parse_env_value(value))
                self._env_overrides[config_key] = value
        
        # Legacy environment variables
        legacy_mappings = {
            "MCP_SERVER_HOST": ["mcp_server", "host"],
            "MCP_SERVER_PORT": ["mcp_server", "port"],
            "AGENT_CARDS_DIR": ["agent_cards_dir"],
            "A2A_LOG_LEVEL": ["log_level"],
            "GOOGLE_API_KEY": ["google_api_key"],  # Store but don't expose
        }
        
        for env_key, config_keys in legacy_mappings.items():
            if env_key in os.environ:
                self._set_nested_value(
                    config_dict, 
                    config_keys, 
                    self._parse_env_value(os.environ[env_key])
                )
        
        return config_dict
    
    def _set_nested_value(self, d: Dict[str, Any], keys: List[str], value: Any):
        """Set a value in nested dictionary using list of keys."""
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Integer
        if value.isdigit():
            return int(value)
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON (list/dict)
        if value.startswith('[') or value.startswith('{'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # String
        return value
    
    def _dict_to_config(self, d: Dict[str, Any]) -> FrameworkConfig:
        """Convert dictionary to FrameworkConfig."""
        # Extract sub-configs
        mcp_config = d.get('mcp_server', {})
        pool_config = d.get('connection_pool', {})
        quality_config = d.get('quality', {})
        metrics_config = d.get('metrics', {})
        
        # Load agent configs
        agents = {}
        agents_data = d.get('agents', {})
        for agent_id, agent_dict in agents_data.items():
            agents[agent_id] = AgentConfig(
                agent_id=agent_id,
                **agent_dict
            )
        
        return FrameworkConfig(
            framework_version=d.get('framework_version', '2.0'),
            environment=d.get('environment', 'development'),
            log_level=d.get('log_level', 'INFO'),
            mcp_server=MCPServerConfig(**mcp_config),
            connection_pool=ConnectionPoolConfig(**pool_config),
            quality=QualityConfig(**quality_config),
            metrics=MetricsConfig(**metrics_config),
            agents=agents,
            agent_cards_dir=d.get('agent_cards_dir', 'agent_cards'),
            config_dir=d.get('config_dir', 'configs'),
            logs_dir=d.get('logs_dir', 'logs'),
            features=d.get('features', {})
        )
    
    @property
    def config(self) -> FrameworkConfig:
        """Get current configuration."""
        if not self._config:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent."""
        return self.config.agents.get(agent_id)
    
    def add_agent_config(self, agent: AgentConfig):
        """Add or update agent configuration."""
        self.config.agents[agent.agent_id] = agent
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.config.features.get(feature, False)
    
    def get_env_overrides(self) -> Dict[str, Any]:
        """Get all environment variable overrides."""
        return self._env_overrides.copy()
    
    def reload(self) -> FrameworkConfig:
        """Reload configuration from disk."""
        logger.info("Reloading configuration")
        return self.load_config(str(self._config_path) if self._config_path else None)
    
    def save(self, path: Optional[Union[str, Path]] = None):
        """Save current configuration to file."""
        save_path = Path(path) if path else self._config_path
        if not save_path:
            raise ValueError("No save path specified")
        
        # Convert to dictionary
        config_dict = self._config_to_dict(self.config)
        
        # Save based on extension
        with open(save_path, 'w') as f:
            if save_path.suffix in ['.yaml', '.yml']:
                yaml.safe_dump(config_dict, f, default_flow_style=False)
            else:
                json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to: {save_path}")
    
    def _config_to_dict(self, config: FrameworkConfig) -> Dict[str, Any]:
        """Convert FrameworkConfig to dictionary."""
        d = asdict(config)
        
        # Convert agent configs
        if 'agents' in d:
            agents_dict = {}
            for agent_id, agent_config in d['agents'].items():
                # Remove agent_id from dict (redundant)
                agent_dict = dict(agent_config)
                agent_dict.pop('agent_id', None)
                agents_dict[agent_id] = agent_dict
            d['agents'] = agents_dict
        
        return d
    
    def validate(self) -> List[str]:
        """Validate current configuration."""
        issues = []
        
        # Check required directories
        for dir_attr in ['agent_cards_dir', 'config_dir', 'logs_dir']:
            dir_path = getattr(self.config, dir_attr)
            if not os.path.exists(dir_path):
                issues.append(f"Directory does not exist: {dir_path}")
        
        # Validate agent configs
        for agent_id, agent in self.config.agents.items():
            if not agent.name:
                issues.append(f"Agent {agent_id} missing name")
            if agent.port < 1024 or agent.port > 65535:
                issues.append(f"Agent {agent_id} has invalid port: {agent.port}")
            if agent.tier not in [1, 2, 3]:
                issues.append(f"Agent {agent_id} has invalid tier: {agent.tier}")
        
        # Check port conflicts
        ports = {}
        for agent_id, agent in self.config.agents.items():
            if agent.port in ports:
                issues.append(
                    f"Port conflict: {agent_id} and {ports[agent.port]} "
                    f"both use port {agent.port}"
                )
            ports[agent.port] = agent_id
        
        return issues


# Global configuration instance
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create global configuration manager."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_config() -> FrameworkConfig:
    """Get current framework configuration."""
    return get_config_manager().config


def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for specific agent."""
    return get_config_manager().get_agent_config(agent_id)


def reload_config() -> FrameworkConfig:
    """Reload configuration from disk."""
    return get_config_manager().reload()


# Convenience exports
__all__ = [
    'ConfigManager',
    'FrameworkConfig',
    'AgentConfig',
    'QualityConfig',
    'ConnectionPoolConfig',
    'MCPServerConfig',
    'MetricsConfig',
    'get_config_manager',
    'get_config',
    'get_agent_config',
    'reload_config'
]