# ABOUTME: Unified MCP tool ecosystem implementing FastMCP server pattern
# ABOUTME: Consolidates tool registration and management for standardized agent architecture

import logging
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.logging import get_logger

# Import existing helper functions from solopreneur tools
try:
    from a2a_mcp.mcp.server import (
        monitor_arxiv, monitor_github, calculate_relevance_score,
        store_technical_intelligence, generate_schedule_recommendations,
        optimize_by_energy, optimize_by_deadline, optimize_by_complexity,
        calculate_learning_velocity, generate_learning_recommendations,
        identify_workflow_optimizations
    )
except ImportError as e:
    logging.warning(f"Could not import helper functions: {e}")
    # Provide stub functions if import fails
    def monitor_arxiv(*args, **kwargs):
        return []
    def monitor_github(*args, **kwargs):
        return []
    def store_technical_intelligence(*args, **kwargs):
        pass
    # ... other stubs would go here

logger = get_logger(__name__)

# Database configurations
# SQLite databases - use data directory for better organization
SOLOPRENEUR_DB = os.getenv('SOLOPRENEUR_DB', './data/solopreneur.db')
TRAVEL_DB = os.getenv('TRAVEL_DB', './data/travel_agency.db')

# Neo4j configuration - require explicit setup via environment variables
# These should be set in .env file - no defaults for security
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# GitHub integration (optional)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')


class UnifiedMCPToolServer:
    """
    Unified MCP tool server implementing FastMCP pattern.
    
    Consolidates all tools from different agent implementations into
    a single, well-organized tool ecosystem with proper categorization
    and health monitoring.
    """

    def __init__(self, host: str = "localhost", port: int = 10100):
        """Initialize unified MCP tool server."""
        self.host = host
        self.port = port
        self.mcp = FastMCP('unified-tools', host=host, port=port)
        self.tool_registry = {}
        self.health_stats = {
            "tools_registered": 0,
            "tools_called": 0,
            "tools_failed": 0,
            "last_health_check": None
        }
        
        # Register all tool categories
        self._register_agent_discovery_tools()
        self._register_travel_tools()
        self._register_solopreneur_tools()
        self._register_system_tools()
        
        logger.info(f"Unified MCP tool server initialized with {len(self.tool_registry)} tools")

    def _register_agent_discovery_tools(self):
        """Register agent discovery and card management tools."""
        
        @self.mcp.tool(
            name='find_agent',
            description='Find and recommend the most suitable agent for a given query using semantic similarity.',
        )
        def find_agent(query: str) -> str:
            """Find relevant agents based on query similarity."""
            try:
                self._update_tool_stats('find_agent', 'called')
                
                # Import agent finding logic from existing server
                from a2a_mcp.mcp.server import find_relevant_agent_cards
                
                result = find_relevant_agent_cards(query)
                return json.dumps(result)
                
            except Exception as e:
                self._update_tool_stats('find_agent', 'failed')
                logger.error(f'Error in find_agent: {e}')
                return json.dumps({'error': str(e)})

        @self.mcp.tool(
            name='list_available_agents',
            description='List all available agents with their capabilities and descriptions.',
        )
        def list_available_agents() -> str:
            """List all available agents in the system."""
            try:
                self._update_tool_stats('list_available_agents', 'called')
                
                # Load agent cards and return summary
                from a2a_mcp.mcp.server import load_agent_cards
                
                _, agent_cards = load_agent_cards()
                agent_summary = []
                
                for card in agent_cards:
                    agent_summary.append({
                        'id': card.get('id', 'unknown'),
                        'name': card.get('name', 'Unknown'),
                        'description': card.get('description', ''),
                        'url': card.get('url', ''),
                        'capabilities': card.get('capabilities', {}),
                        'skills': [skill.get('name', '') for skill in card.get('skills', [])]
                    })
                
                return json.dumps({
                    'total_agents': len(agent_summary),
                    'agents': agent_summary
                })
                
            except Exception as e:
                self._update_tool_stats('list_available_agents', 'failed')
                logger.error(f'Error in list_available_agents: {e}')
                return json.dumps({'error': str(e)})

        self.tool_registry['agent_discovery'] = ['find_agent', 'list_available_agents']

    def _register_travel_tools(self):
        """Register travel planning and booking tools."""
        
        @self.mcp.tool(
            name='query_places_data',
            description='Query Google Places API for location information and travel planning.',
        )
        def query_places_data(query: str, fields: str = 'ALL') -> str:
            """Query Google Places API for travel planning."""
            try:
                self._update_tool_stats('query_places_data', 'called')
                
                # Import places query logic from existing server
                from a2a_mcp.mcp.server import query_google_places
                
                result = query_google_places(query, fields)
                return json.dumps(result)
                
            except Exception as e:
                self._update_tool_stats('query_places_data', 'failed')
                logger.error(f'Error in query_places_data: {e}')
                return json.dumps({'error': str(e)})

        @self.mcp.tool(
            name='query_travel_data',
            description='Query travel database for booking information and travel history.',
        )
        def query_travel_data(query: str, table: str = 'bookings') -> str:
            """Query travel database for booking information."""
            try:
                self._update_tool_stats('query_travel_data', 'called')
                
                # Import travel database query logic
                from a2a_mcp.mcp.server import query_database
                
                result = query_database(query, table, TRAVEL_DB)
                return json.dumps(result)
                
            except Exception as e:
                self._update_tool_stats('query_travel_data', 'failed')
                logger.error(f'Error in query_travel_data: {e}')
                return json.dumps({'error': str(e)})

        self.tool_registry['travel'] = ['query_places_data', 'query_travel_data']

    def _register_solopreneur_tools(self):
        """Register solopreneur-specific productivity and optimization tools."""
        
        @self.mcp.tool(
            name='query_solopreneur_metrics',
            description='Query personal optimization metrics from the database (energy, focus, productivity, stress).',
        )
        def query_solopreneur_metrics(
            metric_type: str,
            user_id: str = "default",
            time_range: str = "day", 
            aggregation: str = "avg"
        ) -> str:
            """Query personal optimization metrics."""
            try:
                self._update_tool_stats('query_solopreneur_metrics', 'called')
                logger.info(f'Query solopreneur metrics: {metric_type} for {time_range}')
                
                # Calculate date range
                end_date = datetime.now()
                if time_range == 'day':
                    start_date = end_date - timedelta(days=1)
                elif time_range == 'week':
                    start_date = end_date - timedelta(weeks=1)
                elif time_range == 'month':
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=7)
                
                with sqlite3.connect(SOLOPRENEUR_DB) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    query = f"""
                    SELECT 
                        DATE(timestamp) as date,
                        {aggregation}(value) as {aggregation}_value,
                        COUNT(*) as data_points,
                        MIN(value) as min_value,
                        MAX(value) as max_value
                    FROM personal_metrics
                    WHERE user_id = ? 
                        AND metric_type = ?
                        AND timestamp BETWEEN ? AND ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                    """
                    
                    cursor.execute(query, (user_id, metric_type, start_date, end_date))
                    rows = cursor.fetchall()
                    
                    results = {
                        'metric_type': metric_type,
                        'time_range': time_range,
                        'aggregation': aggregation,
                        'data': [dict(row) for row in rows],
                        'summary': {
                            'total_data_points': sum(row['data_points'] for row in rows),
                            'overall_avg': sum(row[f'{aggregation}_value'] * row['data_points'] for row in rows) / sum(row['data_points'] for row in rows) if rows else 0
                        }
                    }
                    
                    return json.dumps(results)
                    
            except Exception as e:
                self._update_tool_stats('query_solopreneur_metrics', 'failed')
                logger.error(f'Error querying metrics: {e}')
                return json.dumps({'error': str(e)})

        @self.mcp.tool(
            name='monitor_technical_trends',
            description='Monitor technical trends from various sources like ArXiv and GitHub repositories.',
        )
        def monitor_technical_trends(
            research_areas: str,
            sources: str = "arxiv,github",
            limit: int = 10
        ) -> str:
            """Monitor technical trends from multiple sources."""
            try:
                self._update_tool_stats('monitor_technical_trends', 'called')
                
                # Parse inputs
                areas_list = [area.strip() for area in research_areas.split(',')]
                sources_list = [source.strip() for source in sources.split(',')]
                
                logger.info(f'Monitor technical trends: {areas_list} from {sources_list}')
                
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'research_areas': areas_list,
                    'sources': {}
                }
                
                # Monitor ArXiv
                if 'arxiv' in sources_list:
                    results['sources']['arxiv'] = monitor_arxiv(areas_list, limit)
                
                # Monitor GitHub
                if 'github' in sources_list and GITHUB_TOKEN:
                    results['sources']['github'] = monitor_github(areas_list, limit)
                
                # Store results
                store_technical_intelligence(results)
                logger.info(f'Stored technical intelligence data from {len(results["sources"])} sources')
                
                return json.dumps(results)
                
            except Exception as e:
                self._update_tool_stats('monitor_technical_trends', 'failed')
                logger.error(f'Error monitoring trends: {e}')
                return json.dumps({'error': str(e)})

        @self.mcp.tool(
            name='optimize_task_schedule',
            description='Optimize task scheduling based on energy patterns and task requirements.',
        )
        def optimize_task_schedule(
            tasks_json: str,
            user_id: str = "default",
            optimization_strategy: str = "energy_aware"
        ) -> str:
            """Optimize task scheduling based on personal energy patterns."""
            try:
                self._update_tool_stats('optimize_task_schedule', 'called')
                
                # Parse tasks JSON
                tasks = json.loads(tasks_json)
                logger.info(f'Optimize task schedule with strategy: {optimization_strategy}')
                
                # Get user's energy patterns
                with sqlite3.connect(SOLOPRENEUR_DB) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                    SELECT 
                        hour,
                        AVG(energy_level) as avg_energy,
                        AVG(cognitive_capacity) as avg_cognitive
                    FROM energy_patterns
                    WHERE user_id = ?
                    GROUP BY hour
                    ORDER BY hour
                    """, (user_id,))
                    
                    energy_patterns = {row['hour']: {
                        'energy': row['avg_energy'],
                        'cognitive': row['avg_cognitive']
                    } for row in cursor.fetchall()}
                
                # Optimize based on strategy
                if optimization_strategy == 'energy_aware':
                    optimized_schedule = optimize_by_energy(tasks, energy_patterns)
                elif optimization_strategy == 'deadline_first':
                    optimized_schedule = optimize_by_deadline(tasks, energy_patterns)
                elif optimization_strategy == 'complexity_based':
                    optimized_schedule = optimize_by_complexity(tasks, energy_patterns)
                else:
                    optimized_schedule = tasks
                
                return json.dumps({
                    'strategy': optimization_strategy,
                    'original_tasks': tasks,
                    'optimized_schedule': optimized_schedule,
                    'energy_patterns_available': len(energy_patterns) > 0
                })
                
            except Exception as e:
                self._update_tool_stats('optimize_task_schedule', 'failed')
                logger.error(f'Error optimizing schedule: {e}')
                return json.dumps({'error': str(e)})

        @self.mcp.tool(
            name='analyze_workflow_patterns',
            description='Analyze workflow patterns to identify optimization opportunities over a time period.',
        )
        def analyze_workflow_patterns(
            user_id: str = "default",
            time_period: int = 30
        ) -> str:
            """Analyze workflow patterns for optimization opportunities."""
            try:
                self._update_tool_stats('analyze_workflow_patterns', 'called')
                logger.info(f'Analyze workflow patterns for user: {user_id}')
                
                with sqlite3.connect(SOLOPRENEUR_DB) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Analyze task completion patterns
                    cursor.execute("""
                    SELECT 
                        task_type,
                        AVG(actual_hours / NULLIF(estimated_hours, 0)) as estimation_accuracy,
                        AVG(actual_hours) as avg_duration,
                        COUNT(*) as task_count,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
                    FROM project_tasks
                    WHERE assigned_date >= date('now', '-{} days')
                    GROUP BY task_type
                    """.format(time_period))
                    
                    task_patterns = [dict(row) for row in cursor.fetchall()]
                    
                    # Analyze productivity by time of day
                    cursor.execute("""
                    SELECT 
                        strftime('%H', start_time) as hour,
                        AVG(productivity_score) as avg_productivity,
                        AVG(focus_score) as avg_focus,
                        COUNT(*) as session_count
                    FROM focus_sessions
                    WHERE user_id = ? 
                        AND start_time >= date('now', '-{} days')
                    GROUP BY hour
                    ORDER BY hour
                    """.format(time_period), (user_id,))
                    
                    productivity_patterns = [dict(row) for row in cursor.fetchall()]
                    
                    # Calculate best and worst productivity hours
                    sorted_hours = sorted(productivity_patterns, key=lambda x: x['avg_productivity'] or 0, reverse=True)
                    best_hours = [h['hour'] for h in sorted_hours[:1]] if sorted_hours else []
                    worst_hours = [h['hour'] for h in sorted_hours[-1:]] if sorted_hours else []
                    
                    # Identify optimization opportunities
                    optimizations = identify_workflow_optimizations(task_patterns, productivity_patterns)
                    
                    return json.dumps({
                        'analysis_period_days': time_period,
                        'task_patterns': task_patterns,
                        'productivity_patterns': productivity_patterns,
                        'optimization_opportunities': optimizations,
                        'summary': {
                            'best_productivity_hours': best_hours,
                            'worst_productivity_hours': worst_hours,
                            'total_tasks_analyzed': sum(p.get('task_count', 0) for p in task_patterns),
                            'total_focus_sessions': sum(p.get('session_count', 0) for p in productivity_patterns)
                        }
                    })
                    
            except Exception as e:
                self._update_tool_stats('analyze_workflow_patterns', 'failed')
                logger.error(f'Error analyzing workflow: {e}')
                return json.dumps({'error': str(e)})

        self.tool_registry['solopreneur'] = [
            'query_solopreneur_metrics', 'monitor_technical_trends', 
            'optimize_task_schedule', 'analyze_workflow_patterns'
        ]

    def _register_system_tools(self):
        """Register system monitoring and health check tools."""
        
        @self.mcp.tool(
            name='mcp_server_health',
            description='Get health status and statistics for the MCP tool server.',
        )
        def mcp_server_health() -> str:
            """Get comprehensive health status of the MCP server."""
            try:
                self._update_tool_stats('mcp_server_health', 'called')
                
                # Update health check timestamp
                self.health_stats['last_health_check'] = datetime.now().isoformat()
                
                # Calculate success rate
                total_calls = self.health_stats['tools_called']
                success_rate = (
                    (total_calls - self.health_stats['tools_failed']) / total_calls * 100
                    if total_calls > 0 else 100
                )
                
                # Check database connectivity
                db_status = {}
                for db_name, db_path in [('solopreneur', SOLOPRENEUR_DB), ('travel', TRAVEL_DB)]:
                    try:
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute("SELECT 1")
                            db_status[db_name] = 'connected'
                    except Exception as e:
                        db_status[db_name] = f'error: {str(e)}'
                
                return json.dumps({
                    'server_status': 'healthy',
                    'tool_statistics': self.health_stats,
                    'tool_categories': {
                        category: len(tools) for category, tools in self.tool_registry.items()
                    },
                    'success_rate_percent': round(success_rate, 2),
                    'database_status': db_status,
                    'environment': {
                        'github_token_configured': bool(GITHUB_TOKEN),
                        'neo4j_configured': bool(NEO4J_URI and NEO4J_USER),
                        'solopreneur_db': SOLOPRENEUR_DB,
                        'travel_db': TRAVEL_DB
                    }
                })
                
            except Exception as e:
                self._update_tool_stats('mcp_server_health', 'failed')
                logger.error(f'Error in health check: {e}')
                return json.dumps({'error': str(e), 'server_status': 'unhealthy'})

        @self.mcp.tool(
            name='list_tool_categories',
            description='List all available tool categories and their tools.',
        )
        def list_tool_categories() -> str:
            """List all tool categories and available tools."""
            try:
                self._update_tool_stats('list_tool_categories', 'called')
                
                return json.dumps({
                    'total_categories': len(self.tool_registry),
                    'total_tools': sum(len(tools) for tools in self.tool_registry.values()),
                    'categories': self.tool_registry,
                    'tool_descriptions': {
                        'agent_discovery': 'Tools for finding and managing AI agents',
                        'travel': 'Tools for travel planning and booking management',
                        'solopreneur': 'Tools for personal productivity and optimization',
                        'system': 'Tools for system monitoring and health checks'
                    }
                })
                
            except Exception as e:
                self._update_tool_stats('list_tool_categories', 'failed')
                logger.error(f'Error listing categories: {e}')
                return json.dumps({'error': str(e)})

        self.tool_registry['system'] = ['mcp_server_health', 'list_tool_categories']

    def _update_tool_stats(self, tool_name: str, event_type: str):
        """Update tool usage statistics."""
        if event_type == 'called':
            self.health_stats['tools_called'] += 1
        elif event_type == 'failed':
            self.health_stats['tools_failed'] += 1

    def get_server(self) -> FastMCP:
        """Get the FastMCP server instance."""
        return self.mcp

    def run(self):
        """Run the unified MCP tool server."""
        logger.info(f"🚀 Starting Unified MCP Tool Server...")
        logger.info(f"   Host: {self.host}")
        logger.info(f"   Port: {self.port}")
        logger.info(f"   Total Tools: {sum(len(tools) for tools in self.tool_registry.values())}")
        
        for category, tools in self.tool_registry.items():
            logger.info(f"   {category.title()}: {', '.join(tools)}")
        
        self.mcp.run()


def create_unified_mcp_server(host: str = "localhost", port: int = 10100) -> UnifiedMCPToolServer:
    """
    Factory function to create unified MCP tool server.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Configured unified MCP tool server
    """
    return UnifiedMCPToolServer(host, port)


if __name__ == "__main__":
    # Run the unified MCP tool server
    server = create_unified_mcp_server()
    server.run()