# Troubleshooting Guide

## JSON Parsing Errors

### Problem
You see errors like: `'Failed to parse agent response: Expecting value: line 3 column 1 (char 2)'`

This means the LLM (Language Model) is not returning valid JSON that can be parsed.

### What I Fixed

1. **Enhanced Error Handling**: 
   - Added robust JSON parsing that handles common LLM mistakes
   - Automatically strips markdown code blocks (```json...```)
   - Extracts JSON from text-wrapped responses
   - Logs detailed error messages at ERROR level (visible without --verbose)

2. **Improved Prompts**:
   - Made both Agent 1 and Agent 2 prompts more explicit about JSON-only output
   - Added clear instructions: "Do NOT wrap JSON in ```json code blocks"
   - Emphasized: "Your ENTIRE response must be valid JSON"

3. **Better Logging**:
   - Shows first 500 characters of raw response when parsing fails
   - Indicates which recovery method was used (if successful)
   - Suggests enabling --verbose mode for full debugging

### How to Debug

#### Step 1: Run with Verbose Mode
```bash
# Streamlit
uv run streamlit run app.py -- --verbose

# CLI
uv run main.py --verbose
```

This will show you the exact raw response from the LLM at DEBUG level.

#### Step 2: Check the Logs
Look for these log messages:

**Success with recovery:**
```
[Agent 2] Initial JSON parse failed, attempting to extract JSON from response
[Agent 2] Successfully parsed JSON after removing markdown code blocks
```

**Complete failure:**
```
[Agent 2] Failed to parse agent response as JSON
[Agent 2] Raw response (first 500 chars): ...
```

#### Step 3: Common Issues & Solutions

**Issue 1: LLM wraps JSON in markdown**
```
The LLM returns:
```json
{
  "player_name": "John Doe",
  ...
}
```

**Solution**: The code now automatically removes these code blocks.

**Issue 2: LLM adds explanatory text**
```
Here's the player information:
{
  "player_name": "John Doe",
  ...
}
```

**Solution**: The code now extracts JSON between `{` and `}`.

**Issue 3: LLM returns plain text**
```
I couldn't find any information about this player.
```

**Solution**: This will fail. The prompt needs to be followed. If this happens:
1. Check if the web search is working (`web_search_tool`)
2. Verify the SERP_API_KEY is configured
3. The model may need better instructions or a different model

### Understanding the Data Flow

```
Image URL
    ↓
Agent 1 (Vision Model) - Extracts team & jersey number
    ↓ (Returns JSON)
utils.py processes JSON
    ↓
Agent 2 (Web Search) - Finds player name
    ↓ (Returns JSON)
utils.py processes JSON
    ↓
main.py filters high-confidence players
    ↓
main.py verifies against database
    ↓
app.py displays results
```

**Both Agent 1 and Agent 2 must return valid JSON.**

### If JSON Parsing Still Fails

1. **Check the model**: Some models are better at following JSON output instructions than others.

2. **Verify the prompt**: Make sure the prompts in `prompt.py` haven't been modified.

3. **Check for network issues**: If web search fails, Agent 2 may return incomplete data.

4. **Review the raw response**: With `--verbose`, look at exactly what the LLM is returning.

5. **Test with a simpler case**: Try with a clearer image or a well-known player.

### Example: What Good Output Looks Like

**Agent 1 (Vision) should return:**
```json
{
  "image_analysis": {...},
  "players": [
    {
      "player_id": 1,
      "jersey_number": {"value": 10, "confidence": "high"},
      "team": {"name": "Alouettes", "confidence": "high"},
      ...
    }
  ]
}
```

**Agent 2 (Search) should return:**
```json
{
  "player_name": "Cody Fajardo",
  "confidence": "high",
  "reasoning": "Multiple sources confirm...",
  "sources": ["cfl.ca", "wikipedia.org"]
}
```

### Still Having Issues?

Enable verbose mode and check:
1. The exact raw response from the agent
2. Which recovery method was attempted
3. Any error messages in the logs
4. Whether web search is returning results (for Agent 2)

The enhanced error handling should now catch most common JSON formatting issues automatically.
