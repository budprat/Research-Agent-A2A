# ABOUTME: Enhanced MCP server using generic template with agent discovery and extensible tool patterns
# ABOUTME: Framework V2.0 server combining agent management with reusable API/database integration patterns

import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

from a2a_mcp.common.utils import init_api_key
from a2a_mcp.common.generic_mcp_server_template import (
    GenericMCPServerTemplate, 
    APIConfig,
    DatabaseConfig
)
from mcp.server.fastmcp.utilities.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Configuration constants
AGENT_CARDS_DIR = os.getenv('AGENT_CARDS_DIR', 'agent_cards')
EMBEDDING_MODEL = 'models/embedding-001'
SYSTEM_DB = os.getenv('SYSTEM_DB', './data/system.db')
PLACES_API_URL = 'https://places.googleapis.com/v1/places:searchText'
SQLLITE_DB = os.getenv('SQLLITE_DB', './data/travel.db')

# Agent card management
agent_embeddings_df = None


def generate_embeddings(text: str) -> List[float]:
    """Generates embeddings for the given text using Google Generative AI.

    Args:
        text: The input string for which to generate embeddings.

    Returns:
        A list of embeddings representing the input text.
    """
    try:
        import google.generativeai as genai
        return genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type='retrieval_document',
        )['embedding']
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}. Using fallback method.")
        # Fallback: simple hash-based pseudo-embedding for demo purposes
        return [float(hash(text + str(i)) % 1000) / 1000 for i in range(768)]


def load_agent_cards() -> tuple[List[str], List[dict]]:
    """Loads agent card data from JSON files within a specified directory.

    Returns:
        A tuple containing:
        - List of agent card URIs
        - List of agent card data dictionaries
    """
    card_uris = []
    agent_cards = []
    dir_path = Path(AGENT_CARDS_DIR)
    
    if not dir_path.is_dir():
        logger.warning(
            f'Agent cards directory not found or is not a directory: {AGENT_CARDS_DIR}'
        )
        return card_uris, agent_cards

    logger.info(f'Loading agent cards from: {AGENT_CARDS_DIR}')

    for filename in os.listdir(AGENT_CARDS_DIR):
        if filename.lower().endswith('.json'):
            file_path = dir_path / filename

            if file_path.is_file():
                logger.info(f'Reading file: {filename}')
                try:
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                        card_uris.append(
                            f'resource://agent_cards/{Path(filename).stem}'
                        )
                        agent_cards.append(data)
                except json.JSONDecodeError as jde:
                    logger.error(f'JSON Decoder Error: {jde}')
                except OSError as e:
                    logger.error(f'Error reading file {filename}: {e}')
                except Exception as e:
                    logger.error(
                        f'Unexpected error processing {filename}: {e}',
                        exc_info=True,
                    )
    
    logger.info(f'Loaded {len(agent_cards)} agent cards')
    return card_uris, agent_cards


def build_agent_card_embeddings() -> Optional[pd.DataFrame]:
    """Loads agent cards, generates embeddings for them, and returns a DataFrame.

    Returns:
        A Pandas DataFrame containing agent card data and embeddings, or None if failed.
    """
    card_uris, agent_cards = load_agent_cards()
    
    if not agent_cards:
        logger.warning('No agent cards loaded')
        return None
    
    logger.info('Generating embeddings for agent cards')
    try:
        df = pd.DataFrame(
            {'card_uri': card_uris, 'agent_card': agent_cards}
        )
        df['card_embeddings'] = df.apply(
            lambda row: generate_embeddings(json.dumps(row['agent_card'])),
            axis=1,
        )
        logger.info('Successfully generated embeddings')
        return df
    except Exception as e:
        logger.error(f'Error generating embeddings: {e}', exc_info=True)
        return None


def create_agent_discovery_tools(server: GenericMCPServerTemplate):
    """Add agent discovery tools to the MCP server."""
    
    def find_agent(query: str) -> Dict[str, Any]:
        """Finds the most relevant agent card based on a query string."""
        if agent_embeddings_df is None or agent_embeddings_df.empty:
            return {
                'error': 'No agent cards loaded',
                'suggestion': 'Ensure agent cards are present in the configured directory'
            }
        
        try:
            # Generate query embedding
            query_embedding = generate_embeddings(query)
            
            # Calculate similarity scores
            dot_products = np.dot(
                np.stack(agent_embeddings_df['card_embeddings']),
                query_embedding
            )
            
            # Find best match
            best_match_index = np.argmax(dot_products)
            best_score = dot_products[best_match_index]
            
            logger.debug(
                f'Found best match at index {best_match_index} with score {best_score}'
            )
            
            result = agent_embeddings_df.iloc[best_match_index]['agent_card']
            result['_match_score'] = float(best_score)
            
            return result
            
        except Exception as e:
            logger.error(f'Error finding agent: {e}', exc_info=True)
            return {
                'error': 'Failed to find matching agent',
                'details': str(e)
            }
    
    def list_available_agents() -> Dict[str, Any]:
        """Lists all available agents with their basic information."""
        if agent_embeddings_df is None or agent_embeddings_df.empty:
            return {
                'agents': [],
                'count': 0,
                'message': 'No agents currently loaded'
            }
        
        try:
            agents_summary = []
            for _, row in agent_embeddings_df.iterrows():
                agent_card = row['agent_card']
                summary = {
                    'uri': row['card_uri'],
                    'name': agent_card.get('name', 'Unknown'),
                    'description': agent_card.get('description', 'No description'),
                    'capabilities': agent_card.get('capabilities', []),
                    'type': agent_card.get('type', 'general')
                }
                agents_summary.append(summary)
            
            return {
                'agents': agents_summary,
                'count': len(agents_summary)
            }
            
        except Exception as e:
            logger.error(f'Error listing agents: {e}', exc_info=True)
            return {
                'error': 'Failed to list agents',
                'details': str(e)
            }
    
    def get_server_config() -> Dict[str, Any]:
        """Gets the current configuration of the MCP server."""
        return {
            'server_name': 'a2a-framework-enhanced',
            'version': '2.0',
            'agent_cards_directory': AGENT_CARDS_DIR,
            'embedding_model': EMBEDDING_MODEL,
            'system_database': SYSTEM_DB,
            'sqllite_database': SQLLITE_DB,
            'places_api_url': PLACES_API_URL,
            'framework_type': 'A2A MCP Framework V2.0',
            'capabilities': [
                'Agent discovery and matching',
                'Extensible API integrations',
                'Database query tools',
                'Custom tool registration',
                'Health monitoring'
            ],
            'environment': {
                'python_version': os.sys.version.split()[0],
                'platform': os.sys.platform
            }
        }
    
    # Add tools to server
    server.add_custom_tool(
        name="find_agent",
        description="Finds the most relevant agent card based on a natural language query string",
        handler_func=find_agent,
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Natural language query to find relevant agent"
                }
            },
            "required": ["query"]
        }
    )
    
    server.add_custom_tool(
        name="list_available_agents",
        description="List all available agents with their basic information",
        handler_func=list_available_agents,
        parameters={}
    )
    
    server.add_custom_tool(
        name="get_server_config",
        description="Get the current configuration and capabilities of the MCP server",
        handler_func=get_server_config,
        parameters={}
    )


def create_example_integrations(server: GenericMCPServerTemplate):
    """Add example API and database integrations using the generic patterns."""
    
    # Example: Google Places API integration (like your example)
    if os.getenv('GOOGLE_PLACES_API_KEY'):
        logger.info("Adding Google Places API integration...")
        places_config = APIConfig(
            name="query_places_data",
            description="Query Google Places API for location and business information",
            base_url=PLACES_API_URL,
            headers={
                'X-Goog-Api-Key': '',  # Will be set from env var
                'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress',
                'Content-Type': 'application/json'
            },
            auth_env_var='GOOGLE_PLACES_API_KEY',
            default_params={
                'languageCode': 'en',
                'maxResultCount': 10
            }
        )
        server.add_api_tool("google_places", places_config)
    
    # Example: SQLite database integration (like your example)
    if os.path.exists(SQLLITE_DB):
        logger.info(f"Adding SQLite database integration: {SQLLITE_DB}")
        travel_db_config = DatabaseConfig(
            name="query_travel_data",
            description="Retrieves the most up-to-date, airline, hotel and car rental availability. Helps with the booking. This tool should be used when a user asks for the airline ticket booking, hotel or accommodation booking, or car rental reservations.",
            connection_string=SQLLITE_DB,
            db_type="sqlite",
            query_whitelist=[
                "SELECT * FROM airlines",
                "SELECT * FROM hotels", 
                "SELECT * FROM car_rentals",
                "SELECT * FROM bookings"
            ],
            max_results=1000
        )
        server.add_database_tool("travel_db", travel_db_config)
    
    # Example: Weather API integration
    if os.getenv('OPENWEATHER_API_KEY'):
        logger.info("Adding OpenWeather API integration...")
        weather_config = APIConfig(
            name="query_weather_data",
            description="Query current weather information for any location",
            base_url="https://api.openweathermap.org/data/2.5/weather",
            headers={'Content-Type': 'application/json'},
            auth_env_var='OPENWEATHER_API_KEY',
            default_params={
                'units': 'metric'
            }
        )
        server.add_api_tool("weather_api", weather_config)


def serve(host: str, port: int, transport: str):
    """Initializes and runs the enhanced Agent-to-Agent MCP server.

    Args:
        host: The hostname or IP address to bind the server to.
        port: The port number to bind the server to.
        transport: The transport mechanism for the MCP server (e.g., 'stdio', 'sse').
    """
    # Initialize API key if needed
    try:
        init_api_key()
    except Exception as e:
        logger.warning(f"API key initialization failed: {e}. Some features may be limited.")
    
    logger.info('Starting Enhanced Agent-to-Agent MCP Server (Framework V2.0)')
    
    # Create enhanced MCP server using generic template
    server = GenericMCPServerTemplate(
        server_name="a2a-framework-enhanced",
        description="A2A Framework V2.0 - Agent discovery with extensible tool integrations",
        host=host,
        port=port,
        transport=transport
    )

    # Build agent embeddings
    global agent_embeddings_df
    agent_embeddings_df = build_agent_card_embeddings()

    # Add agent discovery tools
    logger.info("Adding agent discovery and management tools...")
    create_agent_discovery_tools(server)
    
    # Add example integrations (optional, based on environment)
    logger.info("Adding example API and database integrations...")
    create_example_integrations(server)
    
    # Add MCP resource endpoints for agent cards
    @server.mcp.resource('resource://agent_cards/list', mime_type='application/json')
    def get_agent_cards() -> dict:
        """Retrieves all loaded agent cards for the MCP resource endpoint."""
        if agent_embeddings_df is None or agent_embeddings_df.empty:
            return {'agent_cards': []}
        
        logger.info('Reading agent cards resource list')
        return {'agent_cards': agent_embeddings_df['card_uri'].tolist()}

    @server.mcp.resource(
        'resource://agent_cards/{card_name}', mime_type='application/json'
    )
    def get_agent_card(card_name: str) -> dict:
        """Retrieves a specific agent card for the MCP resource endpoint."""
        if agent_embeddings_df is None or agent_embeddings_df.empty:
            return {'error': 'No agent cards loaded'}
        
        logger.info(f'Reading agent card resource: {card_name}')
        
        card_uri = f'resource://agent_cards/{card_name}'
        matching_cards = agent_embeddings_df.loc[
            agent_embeddings_df['card_uri'] == card_uri, 'agent_card'
        ].tolist()
        
        if matching_cards:
            return {'agent_card': matching_cards[0]}
        else:
            return {'error': f'Agent card not found: {card_name}'}

    logger.info(f"Enhanced A2A MCP Server ready with {len(server.tool_handlers)} tools")
    
    # Environment status
    env_status = []
    if os.getenv('GOOGLE_PLACES_API_KEY'): env_status.append("Google Places API")
    if os.getenv('OPENWEATHER_API_KEY'): env_status.append("Weather API")
    if os.path.exists(SQLLITE_DB): env_status.append("SQLite DB")
    
    if env_status:
        logger.info(f"External integrations available: {', '.join(env_status)}")
    else:
        logger.info("Running with core agent discovery tools only")
    
    logger.info("🚀 Starting enhanced MCP server...")
    
    # Run the server
    server.run()


# Entry point for testing
if __name__ == "__main__":
    # Default configuration for testing
    serve(host="localhost", port=8080, transport="stdio")