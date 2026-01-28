"""
Web Search Tool

This module provides a web search tool using SerpAPI for finding CFL player information.
"""

import json
import logging
from strands import tool

from src.core.config import get_settings
from src.core.exceptions import WebSearchError

logger = logging.getLogger(__name__)


@tool
def web_search_tool(query: str) -> str:
    """Search the web using Google Search to find information.
    
    Args:
        query: The search query string
        
    Returns:
        str: JSON string containing search results with titles, snippets, and links
    """
    logger.debug(f"[web_search_tool] Query: {query}")
    
    settings = get_settings()
    serp_api_key = settings.serp_api_key
    
    if not serp_api_key or serp_api_key == "your_serpapi_key_here":
        error_result = json.dumps({
            "error": "SERP_API_KEY not found in environment variables",
            "results": []
        })
        logger.debug("[web_search_tool] ERROR: No API key")
        return error_result
    
    try:
        from serpapi.google_search import GoogleSearch
        
        params = {
            "q": query,
            "api_key": serp_api_key,
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
