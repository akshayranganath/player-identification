"""
Robust JSON Parsing Utilities

This module provides utilities for parsing JSON responses from LLMs,
which may include markdown code blocks, explanatory text, or other formatting.
"""

import json
import re
import logging
from typing import Any, Optional

from src.core.exceptions import JSONParsingError

logger = logging.getLogger(__name__)


def parse_json_response(raw_response: str, context: str = "response") -> dict:
    """Parse JSON from LLM response with robust error recovery.
    
    This function handles common LLM response formats:
    - Plain JSON
    - JSON wrapped in markdown code blocks (```json ... ```)
    - JSON surrounded by explanatory text
    - JSON with leading/trailing whitespace
    
    Args:
        raw_response: Raw response string from LLM
        context: Context for error messages (e.g., "Agent 1", "Agent 2")
    
    Returns:
        Parsed JSON as dictionary
    
    Raises:
        JSONParsingError: If JSON cannot be parsed
    
    Examples:
        >>> parse_json_response('{"key": "value"}')
        {'key': 'value'}
        >>> parse_json_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        >>> parse_json_response('Here is the data:\\n{"key": "value"}')
        {'key': 'value'}
    """
    if not raw_response:
        raise JSONParsingError(
            f"Empty response from {context}",
            details={"context": context}
        )
    
    # Try direct parsing first (fastest path)
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        logger.debug(f"[{context}] Initial JSON parse failed, attempting recovery...")
    
    # Try removing markdown code blocks
    cleaned = _remove_markdown_code_blocks(raw_response)
    try:
        result = json.loads(cleaned)
        logger.info(f"[{context}] Successfully parsed JSON after removing markdown code blocks")
        return result
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON from wrapped text
    extracted = _extract_json_from_text(raw_response)
    if extracted:
        try:
            result = json.loads(extracted)
            logger.info(f"[{context}] Successfully extracted JSON from wrapped response")
            return result
        except json.JSONDecodeError:
            pass
    
    # All recovery attempts failed
    logger.error(f"[{context}] Failed to parse JSON after all recovery attempts")
    logger.error(f"[{context}] Raw response (first 500 chars): {raw_response[:500]}")
    
    raise JSONParsingError(
        f"Failed to parse JSON from {context}",
        details={
            "context": context,
            "raw_response_preview": raw_response[:200],
            "attempted_recovery": True
        }
    )


def _remove_markdown_code_blocks(text: str) -> str:
    """Remove markdown code block markers from text.
    
    Handles formats like:
    - ```json ... ```
    - ``` ... ```
    - ```\n...\n```
    
    Args:
        text: Text potentially containing markdown code blocks
    
    Returns:
        Text with code block markers removed
    """
    # Remove opening markers: ```json or ```
    text = re.sub(r'^```(?:json)?\s*\n?', '', text.strip(), flags=re.MULTILINE)
    
    # Remove closing markers: ```
    text = re.sub(r'\n?```\s*$', '', text.strip(), flags=re.MULTILINE)
    
    return text.strip()


def _extract_json_from_text(text: str) -> Optional[str]:
    """Extract JSON object or array from text containing other content.
    
    Looks for the first complete JSON object {...} or array [...] in the text.
    
    Args:
        text: Text potentially containing JSON
    
    Returns:
        Extracted JSON string, or None if no valid JSON found
    """
    # Try to find JSON object
    obj_match = re.search(r'\{.*\}', text, re.DOTALL)
    if obj_match:
        return obj_match.group(0)
    
    # Try to find JSON array
    arr_match = re.search(r'\[.*\]', text, re.DOTALL)
    if arr_match:
        return arr_match.group(0)
    
    return None


def validate_json_structure(
    data: dict,
    required_fields: list[str],
    context: str = "response"
) -> None:
    """Validate JSON data has required fields.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        context: Context for error messages
    
    Raises:
        JSONParsingError: If validation fails
    """
    if not isinstance(data, dict):
        raise JSONParsingError(
            f"{context} must be a dictionary",
            details={"received_type": type(data).__name__}
        )
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise JSONParsingError(
            f"{context} missing required fields",
            details={
                "missing_fields": missing_fields,
                "present_fields": list(data.keys())
            }
        )


def safe_get_nested(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.
    
    Args:
        data: Dictionary to traverse
        *keys: Sequence of keys to access (e.g., 'player', 'team', 'name')
        default: Default value if key path doesn't exist
    
    Returns:
        Value at key path, or default if not found
    
    Examples:
        >>> data = {"player": {"team": {"name": "Lions"}}}
        >>> safe_get_nested(data, "player", "team", "name")
        'Lions'
        >>> safe_get_nested(data, "player", "missing", default="Unknown")
        'Unknown'
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


if __name__ == "__main__":
    # Test JSON parsing
    test_cases = [
        ('{"key": "value"}', "plain JSON"),
        ('```json\n{"key": "value"}\n```', "markdown code block"),
        ('Here is the data:\n{"key": "value"}', "text with JSON"),
        ('```\n{"key": "value"}\n```', "code block without language"),
    ]
    
    print("JSON Parsing Tests:")
    print("=" * 50)
    for raw, description in test_cases:
        try:
            result = parse_json_response(raw, context="test")
            print(f"✓ {description}: {result}")
        except JSONParsingError as e:
            print(f"✗ {description}: {e}")
