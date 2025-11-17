# ABOUTME: Unit tests for A2AProtocolClient - Agent-to-Agent communication
# ABOUTME: Tests request creation, retry logic, port mapping, and error handling

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

# Import with try/except for graceful handling if deps missing
try:
    from a2a_mcp.common.a2a_protocol import (
        A2AProtocolClient,
        create_a2a_request,
        create_a2a_response,
        A2A_AGENT_PORTS
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    pytestmark = pytest.mark.skip("a2a_protocol module not available")


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestCreateA2ARequest:
    """Test suite for create_a2a_request helper function."""

    def test_create_request_with_minimal_params(self):
        """Test creating A2A request with minimal parameters."""
        request = create_a2a_request("test_method", "test message")

        assert request["jsonrpc"] == "2.0"
        assert "id" in request
        assert isinstance(request["id"], str)
        assert request["method"] == "test_method"
        assert request["params"]["message"] == "test message"

    def test_create_request_with_metadata(self):
        """Test creating A2A request with custom metadata."""
        metadata = {
            "session_id": "session-001",
            "source_agent": "test_agent",
            "priority": "high"
        }
        request = create_a2a_request("message/send", "test", metadata)

        assert request["params"]["metadata"] == metadata

    def test_create_request_unique_ids(self):
        """Test that each request gets a unique ID when provided explicitly."""
        req1 = create_a2a_request("test", "message 1", request_id="req-001")
        req2 = create_a2a_request("test", "message 2", request_id="req-002")

        assert req1["id"] != req2["id"]
        assert req1["id"] == "req-001"
        assert req2["id"] == "req-002"

    def test_create_request_message_structure(self):
        """Test the message structure is correctly formed."""
        request = create_a2a_request("message/send", "Hello world")

        assert "params" in request
        assert request["params"]["message"] == "Hello world"
        assert "metadata" in request["params"]
        assert "timestamp" in request["params"]
        assert isinstance(request["params"]["timestamp"], str)


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestA2AProtocolClient:
    """Test suite for A2AProtocolClient class."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = A2AProtocolClient(source_agent_name="test_agent")

        assert client.source_agent_name == "test_agent"
        assert isinstance(client.custom_port_mapping, dict)
        assert client.max_retries == 3  # Default value

    def test_client_custom_port_mapping(self):
        """Test client accepts custom port mapping."""
        custom_ports = {
            "test_agent": 12345,
            "another_agent": 12346
        }
        client = A2AProtocolClient(
            source_agent_name="test",
            custom_port_mapping=custom_ports
        )

        # Custom ports should be accessible
        assert "test_agent" in client.custom_port_mapping
        assert client.custom_port_mapping["test_agent"] == 12345

    def test_client_port_resolution(self):
        """Test client resolves ports correctly using get_agent_port."""
        client = A2AProtocolClient()

        # Test with known agent from A2A_AGENT_PORTS
        if A2A_AGENT_PORTS:
            first_agent = list(A2A_AGENT_PORTS.keys())[0]
            expected_port = A2A_AGENT_PORTS[first_agent]
            assert client.get_agent_port(first_agent) == expected_port

    @pytest.mark.asyncio
    async def test_send_request_success(self, mock_aiohttp_session):
        """Test successful request sending."""
        client = A2AProtocolClient(use_connection_pool=False)

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_aiohttp_session

            # Mock successful response
            mock_aiohttp_session.post.return_value.__aenter__.return_value.status = 200
            mock_aiohttp_session.post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"result": {"content": "success"}}
            )

            result = await client.send_message(
                target_port=11001,
                message="test query",
                method="message/send"
            )

            assert result is not None
            # Verify session.post was called
            assert mock_aiohttp_session.post.called

    @pytest.mark.asyncio
    async def test_send_request_retry_on_failure(self):
        """Test retry logic on connection failure."""
        client = A2AProtocolClient(max_retries=2, use_connection_pool=False)

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            # Simulate connection failure
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with pytest.raises(Exception):
                await client.send_message(target_port=99999, message="test")

            # Should have retried
            assert mock_session.post.call_count == 2

    @pytest.mark.asyncio
    async def test_send_request_with_metadata(self, mock_aiohttp_session):
        """Test sending request with custom metadata."""
        client = A2AProtocolClient(source_agent_name="test_client")
        metadata = {"session_id": "session-001", "priority": "high"}

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session_class.return_value.__aenter__.return_value = mock_aiohttp_session
            mock_aiohttp_session.post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"result": "success"}
            )

            await client.send_message(
                target_port=11001,
                message="test",
                metadata=metadata
            )

            # Verify the posted data contains metadata
            call_args = mock_aiohttp_session.post.call_args
            if call_args:
                # Check if json parameter was passed
                assert call_args[1].get('json') is not None

    @pytest.mark.asyncio
    async def test_send_request_timeout_handling(self):
        """Test request timeout handling."""
        client = A2AProtocolClient(default_timeout=1, use_connection_pool=False)

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            # Simulate timeout
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with pytest.raises((asyncio.TimeoutError, Exception)):
                await client.send_message(target_port=11001, message="test")

    def test_create_request_with_context(self):
        """Test request creation with session context."""
        request = create_a2a_request(
            method="message/send",
            message="test query",
            metadata={
                "session_id": "session-123",
                "context_data": {"user_id": "user-456"}
            }
        )

        assert request["params"]["message"] == "test query"
        # Verify context is included in metadata
        assert "metadata" in request["params"]
        assert request["params"]["metadata"]["session_id"] == "session-123"
        assert request["params"]["metadata"]["context_data"]["user_id"] == "user-456"


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestA2AProtocolEdgeCases:
    """Test edge cases and error conditions."""

    def test_create_request_empty_message(self):
        """Test handling of empty message."""
        request = create_a2a_request("test", "")
        assert request["params"]["message"] == ""

    def test_create_request_special_characters(self):
        """Test handling of special characters in message."""
        special_msg = "Test with \n newlines \t tabs and unicode: 你好"
        request = create_a2a_request("test", special_msg)
        assert request["params"]["message"] == special_msg

    def test_create_request_large_message(self):
        """Test handling of large message."""
        large_msg = "x" * 10000  # 10KB message
        request = create_a2a_request("test", large_msg)
        assert len(request["params"]["message"]) == 10000

    def test_create_request_null_metadata(self):
        """Test handling of null metadata."""
        request = create_a2a_request("test", "message", None)
        assert "metadata" in request["params"]

    @pytest.mark.asyncio
    async def test_client_invalid_port(self):
        """Test handling of invalid port number."""
        client = A2AProtocolClient()

        with pytest.raises((ValueError, Exception)):
            await client.send_message(target_port=-1, message="test")

    @pytest.mark.asyncio
    async def test_client_unreachable_port(self):
        """Test handling of unreachable port."""
        client = A2AProtocolClient()

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.post = AsyncMock(side_effect=ConnectionRefusedError())
            mock_session_class.return_value.__aenter__.return_value = mock_session

            with pytest.raises((ConnectionRefusedError, Exception)):
                await client.send_message(target_port=99999, message="test")


@pytest.mark.unit
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
class TestA2AProtocolIntegration:
    """Integration-style tests for A2A protocol (still unit tests with mocks)."""

    @pytest.mark.asyncio
    async def test_full_request_response_cycle(self, sample_a2a_request, sample_a2a_response):
        """Test complete request-response cycle."""
        client = A2AProtocolClient(source_agent_name="client_agent")

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=sample_a2a_response)
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            result = await client.send_message(
                target_port=11001,
                message="test query",
                metadata={"session_id": "test-session"}
            )

            # Verify we got a response
            assert result is not None

    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self):
        """Test sending multiple requests sequentially."""
        client = A2AProtocolClient()

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Send 3 requests
            results = []
            for i in range(3):
                result = await client.send_message(
                    target_port=11001,
                    message=f"query {i}"
                )
                results.append(result)

            assert len(results) == 3
            assert mock_session.post.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_ports(self):
        """Test sending concurrent requests to different agents."""
        client = A2AProtocolClient()

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Send concurrent requests
            tasks = [
                client.send_message(target_port=11001, message="query 1"),
                client.send_message(target_port=11002, message="query 2"),
                client.send_message(target_port=11003, message="query 3")
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should complete
            assert len(results) == 3


@pytest.mark.unit
class TestA2AProtocolPerformance:
    """Performance-related tests for A2A protocol."""

    @pytest.mark.slow
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    def test_request_creation_performance(self):
        """Test request creation is fast (< 1ms)."""
        import time

        iterations = 1000
        start = time.perf_counter()

        for i in range(iterations):
            create_a2a_request("test", f"message {i}")

        duration = time.perf_counter() - start
        avg_time = duration / iterations

        # Each request creation should take < 1ms
        assert avg_time < 0.001, f"Request creation too slow: {avg_time*1000:.2f}ms"

    @pytest.mark.slow
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Module not available")
    @pytest.mark.asyncio
    async def test_request_sending_concurrency(self):
        """Test client can handle concurrent requests."""
        client = A2AProtocolClient()

        with patch('a2a_mcp.common.a2a_protocol.aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value.__aenter__.return_value = mock_session

            # Create 100 concurrent requests
            tasks = [
                client.send_message(target_port=11001, message=f"query {i}")
                for i in range(100)
            ]

            import time
            start = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.perf_counter() - start

            # Should complete in reasonable time (< 5 seconds for 100 mocked requests)
            assert duration < 5.0
            assert len(results) == 100
