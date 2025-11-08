# ABOUTME: Pytest configuration and shared fixtures for A2A MCP Framework tests
# ABOUTME: Provides reusable test fixtures, mocks, and utilities

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (medium speed, some dependencies)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow, full system)")
    config.addinivalue_line("markers", "slow: Tests that take more than 1 second")
    config.addinivalue_line("markers", "requires_api_key: Tests that need GOOGLE_API_KEY")
    config.addinivalue_line("markers", "requires_network: Tests that need network access")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# ENVIRONMENT & CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "GOOGLE_API_KEY": "test_api_key_123456789",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GOOGLE_CLOUD_LOCATION": "us-central1",
        "MCP_HOST": "localhost",
        "MCP_PORT": "8080",
        "MCP_TRANSPORT": "stdio",
        "AGENT_CARDS_DIR": "agent_cards",
        "LOG_LEVEL": "DEBUG",
        "TESTING_MODE": "true"
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


@pytest.fixture
def mock_config():
    """Mock framework configuration."""
    return {
        "framework_version": "2.0",
        "environment": "testing",
        "log_level": "DEBUG",
        "mcp_server": {
            "host": "localhost",
            "port": 8080,
            "transport": "sse",
            "url": "http://localhost:8080/sse"
        },
        "connection_pool": {
            "enabled": True,
            "max_connections_per_host": 10,
            "keepalive_timeout": 30
        },
        "quality": {
            "domain": "GENERIC",
            "validation_enabled": True,
            "thresholds": {
                "accuracy": 0.8,
                "completeness": 0.9,
                "relevance": 0.85
            }
        }
    }


# ============================================================================
# AGENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_agent_config():
    """Mock agent configuration."""
    return {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "port": 11001,
        "tier": 1,
        "description": "Test agent for unit tests",
        "instructions": "You are a test agent.",
        "capabilities": ["test", "mock"],
        "quality_domain": "GENERIC",
        "temperature": 0.0,
        "model": "gemini-2.0-flash-test",
        "mcp_tools_enabled": True,
        "a2a_enabled": True
    }


@pytest.fixture
def mock_google_adk_agent():
    """Mock Google ADK Agent."""
    agent = Mock()
    agent.name = "Test Agent"
    agent.description = "Mock agent for testing"

    # Mock async generator response
    async def mock_generate():
        yield {"type": "text", "content": "Test response"}

    agent.generate = Mock(return_value=mock_generate())
    return agent


@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools."""
    tools = []

    # Mock search tool
    search_tool = Mock()
    search_tool.name = "search_web"
    search_tool.description = "Search the web"
    search_tool.parameters = {"query": "string"}
    tools.append(search_tool)

    # Mock database tool
    db_tool = Mock()
    db_tool.name = "query_database"
    db_tool.description = "Query the database"
    db_tool.parameters = {"sql": "string"}
    tools.append(db_tool)

    return tools


# ============================================================================
# A2A PROTOCOL FIXTURES
# ============================================================================

@pytest.fixture
def sample_a2a_request():
    """Sample A2A protocol request."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request-001",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Test query"}],
                "messageId": "msg-001",
                "kind": "message"
            },
            "metadata": {
                "session_id": "session-001",
                "source_agent": "test_client",
                "timestamp": datetime.now().isoformat()
            }
        }
    }


@pytest.fixture
def sample_a2a_response():
    """Sample A2A protocol response."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request-001",
        "result": {
            "message": {
                "role": "assistant",
                "parts": [{"kind": "text", "text": "Test response"}],
                "messageId": "msg-002",
                "kind": "message"
            },
            "metadata": {
                "agent_id": "test_agent",
                "quality_score": 0.95,
                "timestamp": datetime.now().isoformat()
            }
        }
    }


@pytest.fixture
async def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    session = AsyncMock()

    # Mock POST request
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"result": "success"})
    response.text = AsyncMock(return_value='{"result": "success"}')

    session.post = AsyncMock(return_value=response)
    session.get = AsyncMock(return_value=response)
    session.close = AsyncMock()

    return session


# ============================================================================
# QUALITY FRAMEWORK FIXTURES
# ============================================================================

@pytest.fixture
def sample_quality_metrics():
    """Sample quality metrics for testing."""
    return {
        "accuracy": 0.92,
        "completeness": 0.88,
        "relevance": 0.95,
        "confidence": 0.85
    }


@pytest.fixture
def sample_quality_thresholds():
    """Sample quality thresholds."""
    return {
        "accuracy": {
            "min_value": 0.8,
            "max_value": 1.0,
            "weight": 2.0,
            "required": True
        },
        "completeness": {
            "min_value": 0.9,
            "max_value": 1.0,
            "weight": 1.5,
            "required": True
        },
        "relevance": {
            "min_value": 0.85,
            "max_value": 1.0,
            "weight": 1.0,
            "required": False
        }
    }


@pytest.fixture
def sample_quality_report():
    """Sample quality validation report."""
    return {
        "agent_id": "test_agent",
        "overall_score": 0.91,
        "passed": True,
        "metrics": [
            {"name": "accuracy", "value": 0.92, "threshold": 0.8, "passed": True},
            {"name": "completeness", "value": 0.88, "threshold": 0.9, "passed": False},
            {"name": "relevance", "value": 0.95, "threshold": 0.85, "passed": True}
        ],
        "issues": [
            {
                "level": "WARNING",
                "metric": "completeness",
                "message": "Below optimal threshold",
                "details": {"expected": 0.9, "actual": 0.88}
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# MEMORY & SESSION FIXTURES
# ============================================================================

@pytest.fixture
def sample_session():
    """Sample session object."""
    return {
        "id": "session-001",
        "app_name": "test_app",
        "user_id": "user-001",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "state": {
            "conversation_history": [],
            "user_preferences": {},
            "context": {}
        },
        "events": []
    }


@pytest.fixture
def sample_memory_entry():
    """Sample memory entry."""
    return {
        "content": "User prefers technical explanations",
        "memory_type": "PREFERENCE",
        "agent_id": "test_agent",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "session_id": "session-001",
            "user_id": "user-001"
        },
        "tags": ["preference", "technical"],
        "importance": 0.8,
        "ttl_seconds": 86400
    }


# ============================================================================
# WORKFLOW & ORCHESTRATION FIXTURES
# ============================================================================

@pytest.fixture
def sample_task_list():
    """Sample task list for orchestration."""
    return {
        "tasks": [
            {
                "task_id": "task-001",
                "description": "Analyze user requirements",
                "agent_type": "analyzer",
                "priority": "high",
                "dependencies": [],
                "estimated_time": 30
            },
            {
                "task_id": "task-002",
                "description": "Generate solution proposal",
                "agent_type": "planner",
                "priority": "high",
                "dependencies": ["task-001"],
                "estimated_time": 60
            },
            {
                "task_id": "task-003",
                "description": "Validate solution",
                "agent_type": "validator",
                "priority": "medium",
                "dependencies": ["task-002"],
                "estimated_time": 20
            }
        ],
        "coordination_strategy": "sequential",
        "total_estimated_time": 110
    }


@pytest.fixture
def sample_workflow_graph():
    """Sample workflow graph structure."""
    return {
        "nodes": {
            "node-001": {
                "task_id": "task-001",
                "state": "PENDING",
                "agent_assigned": None,
                "result": None
            },
            "node-002": {
                "task_id": "task-002",
                "state": "PENDING",
                "agent_assigned": None,
                "result": None
            }
        },
        "edges": [
            {"from": "node-001", "to": "node-002", "dependency_type": "sequence"}
        ]
    }


# ============================================================================
# CONNECTION POOL FIXTURES
# ============================================================================

@pytest.fixture
def mock_connection_pool():
    """Mock A2A connection pool."""
    pool = AsyncMock()
    pool.get_session = AsyncMock()
    pool.metrics = {
        "connections_created": 0,
        "connections_reused": 0,
        "health_checks_performed": 0,
        "total_requests": 0
    }
    return pool


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_test_data(filename: str) -> Any:
    """Load test data from fixtures directory."""
    filepath = os.path.join(TEST_DATA_DIR, filename)
    with open(filepath, 'r') as f:
        if filename.endswith('.json'):
            return json.load(f)
        return f.read()


@pytest.fixture
def assert_valid_json():
    """Fixture that provides JSON validation helper."""
    def _validate(data: str) -> Dict:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON: {e}")
    return _validate


@pytest.fixture
def assert_valid_a2a_message():
    """Fixture that validates A2A protocol compliance."""
    def _validate(message: Dict) -> bool:
        required_fields = ["jsonrpc", "id", "method", "params"]
        for field in required_fields:
            assert field in message, f"Missing required field: {field}"
        assert message["jsonrpc"] == "2.0", "Invalid JSON-RPC version"
        assert message["method"] in ["message/send", "message/stream"], "Invalid method"
        return True
    return _validate


# ============================================================================
# PARAMETRIZED TEST DATA
# ============================================================================

@pytest.fixture(params=[
    "BUSINESS",
    "ACADEMIC",
    "SERVICE",
    "GENERIC"
])
def quality_domain(request):
    """Parametrized quality domains for testing."""
    return request.param


@pytest.fixture(params=[1, 2, 3])
def agent_tier(request):
    """Parametrized agent tiers for testing."""
    return request.param


@pytest.fixture(params=[
    {"accuracy": 0.95, "completeness": 0.92, "relevance": 0.88},  # All pass
    {"accuracy": 0.75, "completeness": 0.92, "relevance": 0.88},  # Accuracy fails
    {"accuracy": 0.95, "completeness": 0.85, "relevance": 0.88},  # Completeness fails
    {"accuracy": 0.70, "completeness": 0.80, "relevance": 0.75},  # All fail
])
def parametrized_quality_metrics(request):
    """Parametrized quality metrics for edge case testing."""
    return request.param


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatically clean up after each test."""
    # Setup (runs before test)
    yield
    # Teardown (runs after test)
    # Clean up any test artifacts
    pass


@pytest.fixture
def temp_test_data_dir(tmp_path):
    """Create temporary directory for test data."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir
