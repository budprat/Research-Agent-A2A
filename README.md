# A2A MCP Framework - Agentic Framework Boilerplate

A production-ready framework for building sophisticated multi-agent systems with seamless tool integration via the Model Context Protocol (MCP).

## 🚀 Overview

The A2A MCP Framework provides a structured approach to building collaborative AI agent systems that can work together to solve complex problems. Built with enterprise-grade quality standards, this framework enables developers to create scalable agent systems that integrate with any MCP-compatible tools.

## ✨ Key Features (Framework V2.0)

### 🏗️ Tiered Agent Architecture
- **Tier 1 (Master Orchestrators)**: Enterprise-grade orchestration with 7 enhancement phases
- **Tier 2 (Domain Specialists)**: Quality-validated domain expertise with GenericDomainAgent template
- **Tier 3 (Service Agents)**: High-performance tool integration with connection pooling

### 🔗 Agent-to-Agent (A2A) Protocol
- Standardized JSON-RPC based communication
- **60% performance improvement** via connection pooling
- Asynchronous message passing with SSE support
- Built-in error handling and retry mechanisms
- Full context preservation across interactions

### 🛠️ Model Context Protocol (MCP) Integration
- Connect to any MCP-compatible tool server
- Dynamic tool discovery and registration
- Unified interface for diverse tool ecosystems
- Support for custom MCP implementations
- GenericMCPServerTemplate for easy tool server creation

### 🔍 Enterprise Observability
- **OpenTelemetry Integration**: Distributed tracing across all agents
- **Prometheus Metrics**: Real-time performance monitoring
- **Grafana Dashboards**: Pre-built visualization for key metrics
- **Structured Logging**: JSON logs with trace correlation
- **Health Monitoring**: Comprehensive health checks for all components

### 📊 Quality & Performance
- **Quality Framework**: Domain-specific validation (ANALYSIS, CREATIVE, CODING)
- **Parallel Workflows**: Automatic detection and execution of independent tasks
- **Enhanced Workflows**: Dynamic graph management with runtime modifications
- **Response Formatting**: Standardized responses across all agents
- **Session Isolation**: Advanced context management per session

### 🚀 V2.0 Master Orchestrator Features (7 Phases)
- **PHASE 1**: Dynamic workflow management
- **PHASE 2**: Enhanced planner delegation
- **PHASE 3**: Real-time streaming
- **PHASE 4**: Quality validation integration
- **PHASE 5**: Session-based isolation
- **PHASE 6**: Advanced error handling
- **PHASE 7**: Streaming with artifact events and progress tracking

## 🚦 Quick Start

### Prerequisites
- Python 3.9+
- Git
- Google AI API Key (get one at https://makersuite.google.com/app/apikey)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd agentic-framework-boilerplate

# 2. Set up environment variables (REQUIRED)
cp configs/.env.template .env

# 3. Edit .env and add your Google API key
# Open .env in your editor and set:
# GOOGLE_API_KEY=your_actual_api_key_here

# 4. Run the setup script
./start.sh
```

The setup script will:
- Create a virtual environment
- Install all dependencies
- Set up necessary directories (including `./data/` for databases)
- Validate environment configuration
- Start the MCP server
- Launch example agents

**⚠️ Important:** The framework will **not start** without a valid `GOOGLE_API_KEY` set in your `.env` file. This is a security feature to prevent running with default/insecure configurations.

### Basic Usage

```python
# Example: Using the client to interact with agents
python examples/simple_client.py

# Or run in interactive chat mode
python examples/simple_client.py chat
```

## 📁 Project Structure

```
agentic-framework-boilerplate/
├── src/
│   └── a2a_mcp/
│       ├── common/          # Shared utilities and base classes
│       ├── agents/          # Agent implementations
│       │   ├── example_domain/  # Domain-specific example agents
│       │   └── examples/        # Simple example agents
│       ├── clients/         # Client implementations
│       └── mcp/            # MCP server and integration
├── tests/                   # Test suite
├── examples/               # Example implementations
├── agent_cards/            # Agent capability definitions
├── configs/                # Configuration files
├── docs/                   # Documentation
│   ├── FRAMEWORK_COMPONENTS_AND_ORCHESTRATION_GUIDE.md  # Complete V2.0 reference
│   ├── MULTI_AGENT_WORKFLOW_GUIDE.md  # Step-by-step system creation
│   ├── A2A_MCP_ORACLE_FRAMEWORK.md   # Framework V2.0 reference
│   └── OBSERVABILITY_DEPLOYMENT.md    # Observability setup guide
└── dashboards/             # Grafana dashboard templates
```

## 🔧 Configuration

### Environment Setup

1. **Copy the environment template**:
```bash
cp configs/.env.template .env
```

2. **Configure required API keys**:
```env
# REQUIRED: Google AI API Key for agent models
GOOGLE_API_KEY=your_actual_google_api_key_here

# Optional: Additional AI providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

3. **Configure Google Cloud (if using Vertex AI features)**:
```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_AGENT_ENGINE_ID=your-agent-engine-id
```

4. **Configure databases (if using database features)**:
```env
# SQLite databases (automatically created in ./data/)
SQLLITE_DB=./data/travel.db
SOLOPRENEUR_DB=./data/solopreneur.db
TRAVEL_DB=./data/travel_agency.db

# Neo4j Graph Database (if using graph features)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here

# Supabase (if using Supabase features)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

5. **MCP Server settings** (optional, defaults provided):
```env
MCP_HOST=localhost
MCP_PORT=8080
MCP_TRANSPORT=stdio
```

### 🔒 Security Best Practices

**⚠️ IMPORTANT: Never commit secrets to version control!**

The framework follows security best practices:

1. **No Hardcoded Secrets**: All sensitive credentials must be provided via environment variables
2. **Secure Defaults**: Database files are stored in `./data/` directory (add to `.gitignore`)
3. **Mandatory Credentials**: Critical services like Neo4j require explicit configuration - no default passwords
4. **Environment Validation**: The framework validates required environment variables at startup

**What We've Secured:**
- ✅ Removed all hardcoded database passwords
- ✅ Removed default credentials for Neo4j and other services
- ✅ Centralized all database paths to `./data/` directory
- ✅ Required explicit configuration for all sensitive services
- ✅ Provided comprehensive `.env.template` with clear documentation

**Before Running in Production:**
- [ ] Set strong, unique passwords for all database services
- [ ] Use environment-specific `.env` files (never commit them)
- [ ] Enable encryption for sensitive data at rest
- [ ] Implement API rate limiting and authentication
- [ ] Use secrets management services (AWS Secrets Manager, GCP Secret Manager, etc.)
- [ ] Review and update `DATA_RETENTION_DAYS` and privacy settings

### Environment Variables Reference

For a complete list of all available environment variables, see `configs/.env.template`. Key categories:

- **API Keys & Authentication**: AI provider keys, GitHub tokens
- **Google Cloud Configuration**: Project ID, location, Vertex AI settings
- **MCP Server**: Host, port, transport settings
- **Agent Configuration**: Model settings, temperature, memory configuration
- **Database Configuration**: SQLite paths, Neo4j, Supabase credentials
- **Security & Privacy**: Encryption, data retention, GDPR compliance
- **Monitoring & Observability**: Telemetry, metrics, health checks
- **Development & Testing**: Debug mode, testing flags, feature flags

## 🧪 Testing

Run the test suite with coverage:

```bash
./run_tests.sh
```

## 🏭 Creating Your Own Agents

### 1. Define an Agent Card

Create a JSON file in `agent_cards/`:

```json
{
  "agent_id": "my_agent",
  "name": "My Custom Agent",
  "description": "Description of what your agent does",
  "capabilities": ["capability1", "capability2"],
  "tier": 2,
  "dependencies": {
    "tier_3_agents": ["tool_agent_1", "tool_agent_2"]
  }
}
```

### 2. Implement the Agent (V2.0 Options)

#### Quick Option: Use Generic Domain Agent
```python
from a2a_mcp.common.generic_domain_agent import GenericDomainAgent

# Create specialist instantly
agent = GenericDomainAgent(
    domain="Healthcare",
    specialization="diagnostics",
    capabilities=["analyze symptoms", "suggest treatments"],
    quality_domain=QualityDomain.ANALYSIS
)
```

#### Advanced Option: Custom V2.0 Agent
```python
from a2a_mcp.common.standardized_agent_base import StandardizedAgentBase
from a2a_mcp.common.quality_framework import QualityDomain

class MyDomainSpecialist(StandardizedAgentBase):
    def __init__(self):
        super().__init__(
            agent_name="My Domain Specialist",
            description="Expert in specific domain",
            instructions="Detailed system instructions...",
            quality_config={
                "domain": QualityDomain.ANALYSIS,
                "thresholds": {"completeness": 0.9, "accuracy": 0.95}
            },
            mcp_tools_enabled=True,
            a2a_enabled=True,
            enable_observability=True  # V2.0 feature
        )
    
    async def process_request(self, message: dict) -> dict:
        # Automatic quality validation and tracing
        result = await self._process_with_llm(message.get("query", ""))
        return self.format_response(result)  # V2.0 standardized formatting
```

### 3. Register and Run

Add your agent to the system and start it:

```python
# In your launch script
agent = MyCustomAgent()
await agent.start(port=10201)
```

## 📊 Observability Configuration

### Basic Setup

1. **Enable observability features** in your `.env`:
```env
# OpenTelemetry
OTEL_SERVICE_NAME=a2a-mcp-framework
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
TRACING_ENABLED=true

# Prometheus
METRICS_ENABLED=true
METRICS_PORT=9090

# Structured Logging
JSON_LOGS=true
LOG_LEVEL=INFO
```

2. **Deploy the observability stack**:
```bash
# Start Grafana, Prometheus, Jaeger, and OpenTelemetry Collector
docker-compose -f docker-compose.observability.yml up -d
```

3. **Access monitoring dashboards**:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686

For detailed setup, see [Observability Deployment Guide](docs/OBSERVABILITY_DEPLOYMENT.md)

## 🔌 MCP Tool Integration

The framework supports any MCP-compatible tool. To add a new tool:

1. Ensure the MCP server is configured to access your tool
2. Tools are automatically available to all agents
3. Use the tool through the MCP client interface

Example:
```python
# Tools are accessed through the MCP integration
result = await self.mcp_client.call_tool(
    "tool_name",
    parameters={"param": "value"}
)
```

## 📚 Documentation

### Core V2.0 Documentation
- **[Framework Components & Orchestration Guide](docs/FRAMEWORK_COMPONENTS_AND_ORCHESTRATION_GUIDE.md)** - Comprehensive component reference
- **[Multi-Agent Workflow Guide](docs/MULTI_AGENT_WORKFLOW_GUIDE.md)** - Step-by-step system creation
- **[A2A MCP Oracle Framework](docs/A2A_MCP_ORACLE_FRAMEWORK.md)** - Complete V2.0 reference

### Architecture & Deployment
- [Architecture Overview](docs/ARCHITECTURE.md) - System design patterns
- [Observability Deployment](docs/OBSERVABILITY_DEPLOYMENT.md) - Production monitoring setup
- [Domain Customization Guide](docs/DOMAIN_CUSTOMIZATION_GUIDE.md) - Adapt for your domain

## 📦 Example Agents

The framework includes several example agents to help you get started:

### Simple Examples (`src/a2a_mcp/agents/examples/`)
- **SearchAgent**: Demonstrates web search capabilities using MCP tools
- **SummarizationAgent**: Shows text processing with quality validation
- **DataValidationAgent**: Illustrates data validation with custom rules

### Domain Examples (`src/a2a_mcp/agents/example_domain/`)
- **MasterOracleAgent**: Tier 1 orchestrator showing A2A coordination
- **ResearchSpecialistAgent**: Tier 2 domain expert with quality checks
- **ServiceAgent**: Tier 3 service agent with tool integration

## 🛑 Stopping the System

To gracefully shut down all agents and the MCP server:

```bash
./stop.sh
```

## 🔐 Security & Data Privacy

### Credentials Management

The framework requires explicit configuration for all sensitive services. **No default passwords or credentials are provided** to ensure security by default.

**Critical Security Features:**
- 🔒 **Zero Hardcoded Secrets**: All credentials must be provided via environment variables
- 🔑 **No Default Passwords**: Services like Neo4j require explicit password configuration
- 📁 **Isolated Data Directory**: All databases stored in `./data/` (excluded from version control)
- ✅ **Environment Validation**: Startup checks verify required credentials are set
- 🛡️ **Secure by Default**: Framework fails fast if critical credentials are missing

### Data Privacy Controls

Configure privacy settings in your `.env` file:

```env
# Data Privacy Settings
ANONYMIZE_USER_DATA=true           # Anonymize personally identifiable information
DATA_RETENTION_DAYS=90             # Automatic data cleanup after 90 days
GDPR_COMPLIANCE_MODE=false         # Enable GDPR compliance features
ENCRYPT_SENSITIVE_DATA=true        # Encrypt sensitive data at rest
ENCRYPTION_KEY=your_32_char_key    # Encryption key for sensitive data
```

### API Security

Enable rate limiting and authentication:

```env
# API Security
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_REQUESTS=100        # Max requests per window
API_RATE_LIMIT_WINDOW=3600         # Window size in seconds (1 hour)
```

### Production Security Checklist

Before deploying to production:

- [ ] **Rotate all API keys** and use production-grade credentials
- [ ] **Enable TLS/SSL** for all network communications
- [ ] **Set up secrets management** (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault)
- [ ] **Configure firewall rules** to restrict access to agent ports
- [ ] **Enable audit logging** for all sensitive operations
- [ ] **Review data retention policies** and configure appropriately
- [ ] **Implement backup strategies** for critical data
- [ ] **Set up monitoring alerts** for security events
- [ ] **Regular security audits** and dependency updates
- [ ] **Configure CORS policies** if exposing HTTP endpoints

### Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
- Do NOT open a public issue
- Email security details to [security contact - to be added]
- Allow time for patching before public disclosure

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

Built with the Model Context Protocol (MCP) by Anthropic and inspired by modern agent architectures.