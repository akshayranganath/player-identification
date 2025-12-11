"""
Streamlit app for CFL Player Identification.
Takes an image URL, identifies players using AI, and displays results.
"""

import streamlit as st
from main import (
    download_image,
    load_player_data,
    filter_high_confidence_players,
    verify_players_in_database,
)
from utils import get_player_details
import os


def identify_players(image_url: str) -> tuple[str | None, list[dict]]:
    """
    Process an image URL and identify players.
    
    Args:
        image_url: URL of the image to analyze
        
    Returns:
        Tuple of (image_path, list of verified players)
    """
    # Download the image
    image_path = download_image(image_url)
    if not image_path:
        return None, []
    
    # Load player database
    player_data = load_player_data()
    if not player_data:
        return image_path, []
    
    # Get player details from AI
    result = get_player_details(image_path)
    
    # Filter high confidence players
    filtered_players = filter_high_confidence_players(result)
    
    # Verify against database
    verified_players = verify_players_in_database(filtered_players, player_data)
    
    return image_path, verified_players


def cleanup_temp_image(image_path: str) -> None:
    """Remove temporary downloaded image."""
    try:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
    except Exception:
        pass


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
                image_path, players = identify_players(image_url)
                
                # Show the image thumbnail
                st.subheader("Image")
                st.image(image_url, width=300)
                
                # Show results
                st.subheader("Identified Players")
                
                if players:
                    for player in players:
                        name = player.get("player_name", "Unknown")
                        team = player.get("player_team", "Unknown")
                        number = player.get("player_number", "?")
                        
                        st.markdown(f"**{name}** — #{number}, {team}")
                else:
                    st.info("No players identified with high confidence.")
                
                # Cleanup temp file
                cleanup_temp_image(image_path)
                
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

# Footer
st.markdown("---")
st.caption("Powered by AWS Bedrock & Strands Agents")

