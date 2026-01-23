"""
Streamlit app for CFL Player Identification.
Takes an image URL, identifies players using AI, and displays results.

Usage:
    uv run streamlit run app.py               # Normal mode (INFO level)
    uv run streamlit run app.py -- --verbose  # Verbose mode (DEBUG level)
"""

import streamlit as st
import pandas as pd
import logging
import sys
from main import (
    download_image,
    load_player_data,
    filter_high_confidence_players,
    verify_players_in_database,
)
from utils import process_player_identification
import os

# Parse command line arguments for verbose flag
verbose_mode = False
if '--verbose' in sys.argv or '-v' in sys.argv:
    verbose_mode = True

# Configure logging based on verbose flag
log_level = logging.DEBUG if verbose_mode else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration if already configured
)
logger = logging.getLogger(__name__)

if verbose_mode:
    logger.info("Verbose logging enabled (DEBUG level)")
else:
    logger.info("Standard logging enabled (INFO level)")


def identify_players(image_url: str) -> tuple[str | None, list[dict], dict]:
    """
    Process an image URL and identify players.
    
    Args:
        image_url: URL of the image to analyze
        
    Returns:
        Tuple of (image_path, list of verified players, telemetry dict)
    """
    logger.info(f"Starting player identification for image URL: {image_url}")
    
    # Download the image
    image_path = download_image(image_url)
    if not image_path:
        logger.warning("Failed to download image")
        return None, [], {}
    
    logger.debug(f"Image downloaded to: {image_path}")
    
    # Load player database
    player_data = load_player_data()
    if not player_data:
        logger.warning("Failed to load player database")
        return image_path, [], {}
    
    # Get player details from AI (Agent 1 + Agent 2)
    result, telemetry = process_player_identification(image_path)
    
    # Filter high confidence players
    filtered_players = filter_high_confidence_players(result)
    logger.info(f"Filtered {len(filtered_players)} high-confidence players")
    
    # Verify against database
    verified_players = verify_players_in_database(filtered_players, player_data)
    logger.info(f"Verified {len(verified_players)} players against database")
    
    return image_path, verified_players, telemetry


def cleanup_temp_image(image_path: str) -> None:
    """Remove temporary downloaded image."""
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            logger.debug(f"Cleaned up temporary image: {image_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary image {image_path}: {str(e)}")


# Page config
st.set_page_config(
    page_title="CFL Player Identification",
    page_icon="🏈",
    layout="centered",
)

# Title
st.title("🏈 CFL Player Identification")
st.markdown("Enter an image URL to identify CFL players in the photo.")

# Input
image_url = st.text_input(
    "Image URL",
    placeholder="https://example.com/image.jpg",
    help="Enter the URL of an image containing CFL players",
)

# Process button
if st.button("Identify Players", type="primary", disabled=not image_url):
    if image_url:
        with st.spinner("Analyzing image..."):
            try:
                image_path, players, telemetry = identify_players(image_url)
                
                # Show the image thumbnail
                st.subheader("Image")
                st.image(image_url, width=300)
                
                # Show results
                st.subheader("Identified Players")
                
                if players:
                    # Create table data with explicit headers
                    table_data = {
                        "Player Name": [],
                        "Number": [],
                        "Team": []
                    }
                    
                    for player in players:
                        table_data["Player Name"].append(player.get("player_name", "Unknown"))
                        table_data["Number"].append(player.get("player_number", "?"))
                        table_data["Team"].append(player.get("player_team", "Unknown"))
                    
                    # Display as DataFrame table
                    df = pd.DataFrame(table_data)
                    st.table(df)
                else:
                    st.info("No players identified with high confidence.")
                
                # Show telemetry information
                if telemetry:
                    st.subheader("Token Usage")
                    telemetry_data = {
                        "Agent": ["Agent 1", "Agent 2", "Total"],
                        "Input Tokens": [
                            telemetry.get("agent_1", {}).get("input_tokens", 0),
                            telemetry.get("agent_2", {}).get("input_tokens", 0),
                            telemetry.get("total", {}).get("input_tokens", 0)
                        ],
                        "Output Tokens": [
                            telemetry.get("agent_1", {}).get("output_tokens", 0),
                            telemetry.get("agent_2", {}).get("output_tokens", 0),
                            telemetry.get("total", {}).get("output_tokens", 0)
                        ]
                    }
                    telemetry_df = pd.DataFrame(telemetry_data)
                    st.table(telemetry_df)
                
                # Cleanup temp file
                cleanup_temp_image(image_path)
                
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}", exc_info=True)
                st.error(f"Error processing image: {str(e)}")

# Footer
st.markdown("---")
st.caption("Powered by AWS Bedrock & Strands Agents")

