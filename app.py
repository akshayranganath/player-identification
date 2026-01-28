"""
Streamlit app for CFL Player Identification.
Takes an image URL, identifies players using AI, and displays results.

This is the production-ready version using the refactored modular architecture.

Usage:
    uv run streamlit run app.py               # Normal mode (INFO level)
    uv run streamlit run app.py -- --verbose  # Verbose mode (DEBUG level)
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import from refactored modules
from src.core.config import Settings
from src.core.logging_config import configure_logging, get_logger
from src.services.player_service import PlayerIdentificationService
from src.services.image_service import ImageService
from src.repositories.player_repository import PlayerRepository
from src.agents.vision_agent import VisionAgent
from src.agents.search_agent import SearchAgent
from src.core.exceptions import (
    PlayerIdentificationError,
    ImageDownloadError,
    ConfigurationError,
)
from prompt import get_prompt, get_player_search_prompt

# Parse command line arguments for verbose flag
verbose_mode = False
if '--verbose' in sys.argv or '-v' in sys.argv:
    verbose_mode = True

# Setup logging
log_level = "DEBUG" if verbose_mode else "INFO"
log_format = "console"  # Use console format for Streamlit
configure_logging(log_level=log_level, log_format=log_format)
logger = get_logger(__name__)

if verbose_mode:
    logger.info("Verbose logging enabled (DEBUG level)")
else:
    logger.info("Standard logging enabled (INFO level)")


# Initialize services (cached for performance)
@st.cache_resource
def get_services():
    """
    Initialize and cache all services.
    Uses Streamlit's cache to avoid recreating services on every interaction.
    
    Returns:
        Tuple of (settings, player_service, image_service)
    """
    try:
        # Load configuration
        settings = Settings()
        logger.info(f"Configuration loaded for environment: {settings.environment}")
        
        # Initialize repository
        repository = PlayerRepository(db_path=settings.player_db_path)
        
        # Initialize agents with system prompts
        vision_agent = VisionAgent(system_prompt=get_prompt())
        search_agent = SearchAgent(system_prompt=get_player_search_prompt())
        
        # Initialize services
        player_service = PlayerIdentificationService(
            vision_agent=vision_agent,
            search_agent=search_agent,
            player_repository=repository,
        )
        
        image_service = ImageService()
        
        logger.info("All services initialized successfully")
        return settings, player_service, image_service
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        st.error(f"⚠️ Configuration Error: {e}")
        st.stop()
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        st.error(f"⚠️ Failed to initialize application: {e}")
        st.stop()


def identify_players(image_url: str, player_service: PlayerIdentificationService, image_service: ImageService) -> tuple[str | None, list[dict], dict]:
    """
    Process an image URL and identify players.
    
    Args:
        image_url: URL of the image to analyze
        player_service: Player identification service
        image_service: Image handling service
        
    Returns:
        Tuple of (image_path, list of verified players, telemetry dict)
    """
    logger.info(f"Starting player identification for image URL: {image_url}")
    
    image_path = None
    try:
        # Download and validate image
        image_path = image_service.download_image(image_url)
        logger.debug(f"Image downloaded to: {image_path}")
        
        # Identify players using the service (returns tuple)
        verified_players_list, combined_telemetry = player_service.identify_players(image_path)
        
        # Convert to format expected by UI
        verified_players = [
            {
                "player_name": player.player_name,
                "player_number": player.player_number,
                "player_team": player.player_team,
            }
            for player in verified_players_list
        ]
        
        # Extract telemetry (use to_dict() method for convenience)
        telemetry = combined_telemetry.to_dict()
        
        logger.info(f"Identified {len(verified_players)} players")
        return image_path, verified_players, telemetry
        
    except ImageDownloadError as e:
        logger.warning(f"Image download failed: {e}")
        st.error(f"Failed to download image: {e}")
        return None, [], {}
    except PlayerIdentificationError as e:
        logger.error(f"Player identification failed: {e}")
        st.error(f"Player identification error: {e}")
        return None, [], {}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        st.error(f"An unexpected error occurred: {e}")
        return None, [], {}
    finally:
        # Always cleanup the temporary image, even if there was an error
        if image_path:
            cleanup_temp_image(image_path, image_service)


def cleanup_temp_image(image_path: str, image_service: ImageService) -> None:
    """Remove temporary downloaded image."""
    try:
        if image_path:
            image_service.cleanup_temp_image(image_path)
            logger.debug(f"Cleaned up temporary image: {image_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary image {image_path}: {str(e)}")


# ============================================================================
# Streamlit UI
# ============================================================================

# Page config
st.set_page_config(
    page_title="CFL Player Identification",
    page_icon="🏈",
    layout="centered",
)

# Initialize services
settings, player_service, image_service = get_services()

# Title
st.title("🏈 CFL Player Identification")
st.markdown("Enter an image URL to identify CFL players in the photo.")

# Show environment info in sidebar
with st.sidebar:
    st.subheader("ℹ️ System Info")
    st.caption(f"Environment: `{settings.environment}`")
    st.caption(f"Log Level: `{settings.log_level}`")
    st.caption(f"AWS Region: `{settings.aws_region}`")
    
    if verbose_mode:
        st.success("🔍 Verbose mode enabled")
    
    st.markdown("---")
    st.caption("🛠️ **Architecture:** Production-ready modular design")
    st.caption("🤖 **AI Model:** AWS Bedrock Claude Sonnet")
    st.caption("🔍 **Search:** SerpAPI")

# Input
image_url = st.text_input(
    "Image URL",
    placeholder="https://example.com/cfl-player-image.jpg",
    help="Enter the URL of an image containing CFL players",
)

# Sample images
with st.expander("📸 Try a sample image"):
    st.markdown("""
    Click to copy a sample image URL:
    ```
    https://res.cloudinary.com/dbmataac4/image/upload/v1765486287/ghgewenoaznomnmsutrv.jpg
    ```
    """)

# Process button
if st.button("Identify Players", type="primary", disabled=not image_url):
    if image_url:
        with st.spinner("Analyzing image..."):
            try:
                image_path, players, telemetry = identify_players(
                    image_url, player_service, image_service
                )
                
                # Show the image
                st.subheader("📷 Image")
                try:
                    st.image(image_url, width=400)
                except Exception as e:
                    logger.warning(f"Failed to display image: {e}")
                    st.caption("_Image preview unavailable_")
                
                # Show results
                st.subheader("🎯 Identified Players")
                
                if players:
                    # Create table data
                    table_data = {
                        "Player Name": [p.get("player_name", "Unknown") for p in players],
                        "Number": [p.get("player_number", "?") for p in players],
                        "Team": [p.get("player_team", "Unknown") for p in players],
                    }
                    
                    # Display as DataFrame
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.success(f"✅ Successfully identified {len(players)} player(s)")
                else:
                    st.info("ℹ️ No players identified with high confidence.")
                    st.caption("Try adjusting the image or use a different photo.")
                
                # Show telemetry information
                if telemetry:
                    st.subheader("📊 Token Usage")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Agent 1 (Vision)",
                            f"{telemetry['agent_1']['output_tokens']} out",
                            delta=f"{telemetry['agent_1']['input_tokens']} in",
                        )
                    
                    with col2:
                        st.metric(
                            "Agent 2 (Search)",
                            f"{telemetry['agent_2']['output_tokens']} out",
                            delta=f"{telemetry['agent_2']['input_tokens']} in",
                        )
                    
                    with col3:
                        st.metric(
                            "Total",
                            f"{telemetry['total']['output_tokens']} out",
                            delta=f"{telemetry['total']['input_tokens']} in",
                        )
                    
                    # Detailed table
                    with st.expander("📈 Detailed Token Usage"):
                        telemetry_data = {
                            "Agent": ["Agent 1 (Vision)", "Agent 2 (Search)", "Total"],
                            "Input Tokens": [
                                telemetry["agent_1"]["input_tokens"],
                                telemetry["agent_2"]["input_tokens"],
                                telemetry["total"]["input_tokens"],
                            ],
                            "Output Tokens": [
                                telemetry["agent_1"]["output_tokens"],
                                telemetry["agent_2"]["output_tokens"],
                                telemetry["total"]["output_tokens"],
                            ],
                        }
                        telemetry_df = pd.DataFrame(telemetry_data)
                        st.table(telemetry_df)
                
                # Cleanup temp file
                cleanup_temp_image(image_path, image_service)
                
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}", exc_info=True)
                st.error(f"❌ Error: {str(e)}")
                if verbose_mode:
                    st.exception(e)

# Footer
st.markdown("---")
st.caption("⚡ Powered by AWS Bedrock & Strands Agents | 🏗️ Production-ready architecture")
st.caption("📖 [Documentation](docs/architecture.md) | 🐳 [Deployment Guide](docs/deployment.md)")
