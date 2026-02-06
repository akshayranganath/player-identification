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
from pathlib import Path

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


def load_css():
    """Load custom CSS styles from external file."""
    css_file = Path(__file__).parent / "static" / "styles.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found: {css_file}")


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
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load custom CSS
load_css()

# Header Section
st.markdown('<h1 class="main-title">🏈 CFL Player Identification</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by AI - Identify Canadian Football League players from any image</p>', unsafe_allow_html=True)

# Hero Section - Input Card
#st.markdown('<div class="cfl-card hero-card">', unsafe_allow_html=True)
st.markdown("### Enter Image URL")
st.markdown("Provide a URL to an image containing CFL players to identify them automatically.")

image_url = st.text_input(
    "Image URL",
    placeholder="https://example.com/cfl-game-photo.jpg",
    help="Enter the URL of an image containing CFL players",
    label_visibility="collapsed",
)

# Center the button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    process_button = st.button("Identify Players ▶", type="primary", disabled=not image_url)

st.markdown('</div>', unsafe_allow_html=True)

# Instructions section (shown before processing)
if not process_button:
    st.markdown('<br>', unsafe_allow_html=True)    
    st.markdown("### 📋 How It Works")
    
    col_inst1, col_inst2, col_inst3 = st.columns(3)
    
    with col_inst1:
        st.markdown("**1️⃣ Enter Image URL**")
        st.markdown("Provide a direct link to an image containing CFL players in action.")
    
    with col_inst2:
        st.markdown("**2️⃣ AI Analysis**")
        st.markdown("Our AI agents analyze the image to detect player jerseys and numbers.")
    
    with col_inst3:
        st.markdown("**3️⃣ Get Results**")
        st.markdown("View identified players with their names, numbers, and teams instantly.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sample images section
    st.markdown('<br>', unsafe_allow_html=True)    
    st.markdown("### 💡 Tips for Best Results")
    st.markdown("""
    - Use images with clear, visible player jerseys
    - Ensure jersey numbers are readable
    - Works best with front-facing or side-view shots
    - Higher resolution images yield better results
    - Multiple players can be identified in a single image
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Process button
if process_button:
    if image_url:
        with st.spinner("🔍 Analyzing image and identifying players..."):
            try:
                image_path, players, telemetry = identify_players(image_url)
                
                # Divider
                st.markdown('<hr class="cfl-divider">', unsafe_allow_html=True)
                
                # Results Section with Columns
                st.markdown('<div class="fade-in">', unsafe_allow_html=True)
                
                # Create two-column layout
                col_img, col_results = st.columns([1, 2], gap="large")
                
                with col_img:
                    # Image Card
                    
                    st.markdown('<h2 class="result-header">Image</h2>', unsafe_allow_html=True)
                    st.image(image_url, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_results:
                    # Players Card
                    
                    
                    if players:
                        player_count = len(players)
                        st.markdown(
                            f'<h2 class="result-header">Identified Players <span class="player-count-badge">{player_count} Found</span></h2>', 
                            unsafe_allow_html=True
                        )
                        
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
                        st.markdown('<h2 class="result-header">Identified Players</h2>', unsafe_allow_html=True)
                        st.info("⚠️ No players identified with high confidence. Try an image with clearer player jerseys and numbers.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Telemetry Section (Collapsible)
                if telemetry:
                    #st.markdown('<br>', unsafe_allow_html=True)
                    with st.expander("📊 Token Usage & Performance Metrics", expanded=False):
                        # Create metrics in columns
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        
                        with metric_col1:
                            #st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{telemetry.get("total", {}).get("input_tokens", 0):,}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">Total Input Tokens</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with metric_col2:
                            #st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{telemetry.get("total", {}).get("output_tokens", 0):,}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">Total Output Tokens</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with metric_col3:
                            total_tokens = (
                                telemetry.get("total", {}).get("input_tokens", 0) + 
                                telemetry.get("total", {}).get("output_tokens", 0)
                            )
                            #st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-value">{total_tokens:,}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-label">Total Tokens</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Detailed breakdown table
                        st.markdown("#### Detailed Breakdown by Agent")
                        telemetry_data = {
                            "Agent": ["Agent 1 (Image Analysis)", "Agent 2 (Validation)", "Total"],
                            "Input Tokens": [
                                f"{telemetry.get('agent_1', {}).get('input_tokens', 0):,}",
                                f"{telemetry.get('agent_2', {}).get('input_tokens', 0):,}",
                                f"{telemetry.get('total', {}).get('input_tokens', 0):,}"
                            ],
                            "Output Tokens": [
                                f"{telemetry.get('agent_1', {}).get('output_tokens', 0):,}",
                                f"{telemetry.get('agent_2', {}).get('output_tokens', 0):,}",
                                f"{telemetry.get('total', {}).get('output_tokens', 0):,}"
                            ]
                        }
                        telemetry_df = pd.DataFrame(telemetry_data)
                        st.table(telemetry_df)
                
                # Cleanup temp file
                cleanup_temp_image(image_path)
                
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}", exc_info=True)
                st.error(f"❌ Error processing image: {str(e)}")

# Footer
st.markdown('<hr class="footer-divider">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="custom-footer">
        <strong>Powered by AWS Bedrock & Strands Agents</strong><br>
        CFL Player Identification System © 2026
    </div>
    """,
    unsafe_allow_html=True
)

