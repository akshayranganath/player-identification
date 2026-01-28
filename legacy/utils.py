from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import image_reader
from prompt import get_prompt, get_player_search_prompt
import json
import os
import re
import traceback
import logging
from dotenv import load_dotenv
from serpapi.google_search import GoogleSearch
from typing import Any

# Configure logging (only if not already configured by parent app)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# configure the model
bedrock_model = BedrockModel(model_id='anthropic.claude-3-sonnet-20240229-v1:0')
MULTIMODAL_SYSTEM_PROMPT = get_prompt()

# Get SerpAPI key
SERP_API_KEY = os.getenv('SERP_API_KEY')


@tool
def web_search_tool(query: str) -> str:
    """
    Search the web using Google Search to find information.
    
    Args:
        query: The search query string
        
    Returns:
        str: JSON string containing search results with titles, snippets, and links
    """
    logger.debug(f"[web_search_tool] Query: {query}")
    
    if not SERP_API_KEY:
        error_result = json.dumps({
            "error": "SERP_API_KEY not found in environment variables",
            "results": []
        })
        logger.debug("[web_search_tool] ERROR: No API key")
        return error_result
    
    try:
        params = {
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "num": 10  # Get top 10 results for better analysis
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "organic_results" not in results or len(results["organic_results"]) == 0:
            no_results = json.dumps({
                "message": "No search results found",
                "results": []
            })
            logger.debug("[web_search_tool] No organic results found")
            return no_results
        
        # Format results for the LLM
        formatted_results = []
        for idx, result in enumerate(results["organic_results"][:10]):
            formatted_results.append({
                "rank": idx + 1,
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "link": result.get("link", "")
            })
        
        logger.debug(f"[web_search_tool] Found {len(formatted_results)} results")
        logger.debug("[web_search_tool] Top 3 results:")
        for i, r in enumerate(formatted_results[:3]):
            logger.debug(f"  {i+1}. {r['title']}")
            logger.debug(f"     Link: {r['link']}")
            logger.debug(f"     Snippet: {r['snippet'][:100]}...")
        
        search_result = json.dumps({
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results
        }, indent=2)
        
        return search_result
        
    except Exception as e:
        error_result = json.dumps({
            "error": f"Search failed: {str(e)}",
            "results": []
        })
        logger.debug(f"[web_search_tool] Exception: {str(e)}")
        return error_result


def agent_1_extract_team_and_jersey(image_path: str) -> tuple[dict, dict]:
    """
    Agent 1: Extracts team name and jersey number from image using vision model.
    
    Args:
        image_path: Path to the player image
        
    Returns:
        tuple: (player_data dict, telemetry dict with input_tokens and output_tokens)
    """
    agent = Agent(
        system_prompt=MULTIMODAL_SYSTEM_PROMPT,
        tools=[image_reader],
        model=bedrock_model
    )

    result = agent(f"Can you describe this image: {image_path}")
    
    # Extract telemetry information from result.metrics
    telemetry = {
        "input_tokens": result.metrics.accumulated_usage.get('inputTokens', 0),
        "output_tokens": result.metrics.accumulated_usage.get('outputTokens', 0)
    }
    
    logger.info(f"[Agent 1] Telemetry: Input tokens: {telemetry['input_tokens']}, Output tokens: {telemetry['output_tokens']}")
    
    # Get raw response
    raw_response = str(result)
    logger.debug(f"[Agent 1] Raw response (first 200 chars): {raw_response[:200]}")
    
    # Parse the agent's response with robust error handling
    try:
        result_dict = json.loads(raw_response)
    except json.JSONDecodeError as json_error:
        logger.warning(f"[Agent 1] Initial JSON parse failed, attempting to extract JSON from response")
        
        # Try to remove markdown code blocks
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', raw_response.strip())
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response.strip())
        
        try:
            result_dict = json.loads(cleaned_response)
            logger.info("[Agent 1] Successfully parsed JSON after removing markdown code blocks")
        except json.JSONDecodeError:
            # Look for JSON between curly braces
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                try:
                    result_dict = json.loads(json_match.group(0))
                    logger.info("[Agent 1] Successfully extracted JSON from wrapped response")
                except json.JSONDecodeError:
                    logger.error(f"[Agent 1] Failed to parse agent response as JSON")
                    logger.error(f"[Agent 1] Raw response (first 500 chars): {raw_response[:500]}")
                    return {
                        "error": "Failed to parse vision model response",
                        "reason": str(json_error)
                    }, telemetry
            else:
                logger.error(f"[Agent 1] No JSON found in response")
                logger.error(f"[Agent 1] Raw response (first 500 chars): {raw_response[:500]}")
                return {
                    "error": "No valid JSON found in vision model response",
                    "reason": str(json_error)
                }, telemetry
    
    return result_dict, telemetry


def agent_2_find_player_name(team_name: str, jersey_number: str) -> tuple[dict, dict]:
    """
    Agent 2: Uses a strands agent with web search tool to find player name based on team and jersey number.
    
    Args:
        team_name: Name of the CFL team
        jersey_number: Player's jersey number
        
    Returns:
        tuple: (player_data dict, telemetry dict with input_tokens and output_tokens)
        
    Confidence Guidelines:
        - HIGH: Multiple authoritative sources confirm the same player name
        - MEDIUM: Search results suggest a player name but with some ambiguity or fewer authoritative sources
        - LOW: Very few results, conflicting information, or unclear matches
    """
    logger.debug(f"[Agent 2] Starting search for Team={team_name}, Jersey={jersey_number}")
    
    telemetry = {
        "input_tokens": 0,
        "output_tokens": 0
    }
    
    if not SERP_API_KEY:
        logger.debug("[Agent 2] ERROR: SERP_API_KEY not found")
        return {
            "player_name": "Unknown",
            "confidence": "low",
            "error": "SERP_API_KEY not found in environment variables",
            "reasoning": "Cannot perform web search without API key",
            "sources": []
        }, telemetry
    
    try:
        # Create agent with web search tool
        logger.debug("[Agent 2] Creating agent with web_search_tool")
        agent = Agent(
            system_prompt=get_player_search_prompt(),
            tools=[web_search_tool],
            model=bedrock_model
        )
        
        # Ask agent to find the player
        query = f"Find the name of the CFL player who plays for {team_name} and wears jersey number {jersey_number}"
        logger.debug(f"[Agent 2] Sending query to agent: {query}")
        
        result = agent(query)
        
        # Extract telemetry information from result.metrics
        telemetry["input_tokens"] = result.metrics.accumulated_usage.get('inputTokens', 0)
        telemetry["output_tokens"] = result.metrics.accumulated_usage.get('outputTokens', 0)
        
        logger.info(f"[Agent 2] Telemetry: Input tokens: {telemetry['input_tokens']}, Output tokens: {telemetry['output_tokens']}")
        
        # Get raw response as string
        raw_response = str(result)
        logger.debug(f"[Agent 2] Raw agent response:")
        logger.debug(f"[Agent 2] {raw_response}")
        logger.debug(f"[Agent 2] Response type: {type(result)}")
        
        # Parse the agent's response
        try:
            result_dict = json.loads(raw_response)
        except json.JSONDecodeError as json_error:
            # Try to extract JSON from the response (sometimes LLMs wrap JSON in text or markdown)
            logger.warning(f"[Agent 2] Initial JSON parse failed, attempting to extract JSON from response")
            
            # First, try to remove markdown code blocks (```json ... ```)
            cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', raw_response.strip())
            cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response.strip())
            
            # Try parsing the cleaned response
            try:
                result_dict = json.loads(cleaned_response)
                logger.info("[Agent 2] Successfully parsed JSON after removing markdown code blocks")
            except json.JSONDecodeError:
                # Look for JSON between curly braces as last resort
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    try:
                        result_dict = json.loads(json_match.group(0))
                        logger.info("[Agent 2] Successfully extracted JSON from wrapped response")
                    except json.JSONDecodeError:
                        # Re-raise original error with more context
                        logger.error(f"[Agent 2] Failed to parse agent response as JSON")
                        logger.error(f"[Agent 2] Raw response (first 500 chars): {raw_response[:500]}")
                        raise json_error
                else:
                    logger.error(f"[Agent 2] No JSON found in response")
                    logger.error(f"[Agent 2] Raw response (first 500 chars): {raw_response[:500]}")
                    raise json_error
        
        logger.debug("[Agent 2] Parsed response:")
        logger.debug(f"[Agent 2]   Player Name: {result_dict.get('player_name', 'N/A')}")
        logger.debug(f"[Agent 2]   Confidence: {result_dict.get('confidence', 'N/A')}")
        logger.debug(f"[Agent 2]   Reasoning: {result_dict.get('reasoning', 'N/A')}")
        logger.debug(f"[Agent 2]   Sources: {result_dict.get('sources', [])}")
        
        # Ensure all expected fields are present
        if "player_name" not in result_dict:
            result_dict["player_name"] = "Unknown"
        if "confidence" not in result_dict:
            result_dict["confidence"] = "low"
        if "reasoning" not in result_dict:
            result_dict["reasoning"] = "No reasoning provided"
        if "sources" not in result_dict:
            result_dict["sources"] = []
            
        return result_dict, telemetry
        
    except json.JSONDecodeError as e:
        logger.error(f"[Agent 2] JSON Parse Error: {str(e)}")
        logger.error(f"[Agent 2] This usually means the LLM didn't follow the prompt format")
        logger.error(f"[Agent 2] Enable --verbose mode to see the full raw response")
        return {
            "player_name": "Unknown",
            "confidence": "low",
            "error": f"Failed to parse agent response: {str(e)}",
            "reasoning": "Agent returned invalid JSON",
            "sources": []
        }, telemetry
    except Exception as e:
        logger.error(f"[Agent 2] Exception: {str(e)}")
        logger.debug("[Agent 2] Traceback:", exc_info=True)
        return {
            "player_name": "Unknown",
            "confidence": "low",
            "error": f"Search failed: {str(e)}",
            "reasoning": "An error occurred during the search",
            "sources": []
        }, telemetry


def process_player_identification(image_path: str) -> tuple[dict, dict]:
    """
    Main orchestration function that runs both agents in sequence.
    
    Args:
        image_path: Path to the player image
        
    Returns:
        tuple: (player_data dict, telemetry dict with agent breakdown)
    """
    logger.info(f"{'='*60}")
    logger.info(f"Processing image: {image_path}")
    logger.info(f"{'='*60}")
    
    # Initialize telemetry tracking
    telemetry = {
        "agent_1": {"input_tokens": 0, "output_tokens": 0},
        "agent_2": {"input_tokens": 0, "output_tokens": 0},
        "total": {"input_tokens": 0, "output_tokens": 0}
    }
    
    # Agent 1: Extract team name and jersey number
    logger.info("[Agent 1] Extracting team name and jersey number from image...")
    vision_results, agent_1_telemetry = agent_1_extract_team_and_jersey(image_path)
    
    # Update telemetry for Agent 1
    telemetry["agent_1"] = agent_1_telemetry
    telemetry["total"]["input_tokens"] += agent_1_telemetry["input_tokens"]
    telemetry["total"]["output_tokens"] += agent_1_telemetry["output_tokens"]
    
    if "error" in vision_results:
        logger.error(f"[Agent 1] Error: {vision_results['error']}")
        return vision_results, telemetry
    
    logger.info("[Agent 1] Extraction complete!")
    
    # Process each player found in the image
    enhanced_results = vision_results.copy()
    
    if "players" in vision_results:
        for player in enhanced_results["players"]:
            player_id = player.get("player_id", "Unknown")
            team_name = player.get("team", {}).get("name", "Unknown")
            jersey_number = player.get("jersey_number", {}).get("value", "-1")
                        
            
            logger.info(f"[Agent 2] Searching for player {player_id}: Team={team_name}, Jersey={jersey_number}")
            
            # Agent 2: Search for player name
            if team_name != "Unknown" and jersey_number != -1:
                search_results, agent_2_telemetry = agent_2_find_player_name(team_name, jersey_number)
                
                # Update telemetry for Agent 2 (accumulate if multiple players)
                telemetry["agent_2"]["input_tokens"] += agent_2_telemetry["input_tokens"]
                telemetry["agent_2"]["output_tokens"] += agent_2_telemetry["output_tokens"]
                telemetry["total"]["input_tokens"] += agent_2_telemetry["input_tokens"]
                telemetry["total"]["output_tokens"] += agent_2_telemetry["output_tokens"]
                
                # Add player_name field with structured confidence
                player["player_name"] = {
                    "value": search_results.get("player_name", "Unknown"),
                    "confidence": search_results.get("confidence", "low")
                }
                
                # Store full web search details for reference
                player["web_search"] = search_results
                
                logger.info(f"[Agent 2] Found: {player['player_name']['value']} (confidence: {player['player_name']['confidence']})")
                if search_results.get("reasoning"):
                    logger.info(f"[Agent 2] Reasoning: {search_results['reasoning']}")
            else:
                player["player_name"] = {
                    "value": "Unknown",
                    "confidence": "low"
                }
                player["web_search"] = {
                    "player_name": "Unknown",
                    "confidence": "low",
                    "error": "Insufficient information for web search (team or jersey number missing)",
                    "reasoning": "Team name or jersey number not available",
                    "sources": []
                }
                logger.info("[Agent 2] Skipped - insufficient information")
    
    return enhanced_results, telemetry


if __name__=="__main__":
    # Test with a sample image
    test_image = "/Users/akshayranganath/Projects/aws-hackathon/player-identification/data/5.jpg"
    result, telemetry = process_player_identification(test_image)
    
    logger.info('\n' + '='*60)
    logger.info('**** Final Results ****')
    logger.info('='*60)
    logger.info(json.dumps(result, indent=2))
    
    logger.info('\n' + '='*60)
    logger.info('**** Telemetry ****')
    logger.info('='*60)
    logger.info(f"Agent 1: Input tokens: {telemetry['agent_1']['input_tokens']}, Output tokens: {telemetry['agent_1']['output_tokens']}")
    logger.info(f"Agent 2: Input tokens: {telemetry['agent_2']['input_tokens']}, Output tokens: {telemetry['agent_2']['output_tokens']}")
    logger.info(f"Total: Input tokens: {telemetry['total']['input_tokens']}, Output tokens: {telemetry['total']['output_tokens']}")