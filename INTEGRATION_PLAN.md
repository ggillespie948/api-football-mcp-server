# MCP Integration Plan - Use Supabase Cache in soccer_server.py

## Current Problem
- ❌ **soccer_server.py**: Direct API calls (costs requests)
- ❌ **Enhanced tools**: Separate system (not integrated)
- ❌ **Hardcoded seasons**: 2024 in scrapers, should use global setting

## Goal
✅ **soccer_server.py MCP tools** → **read from Supabase cache** → **zero API calls**

## Simple Integration Steps

### Step 1: Fix Global Settings
**Current**: Hardcoded seasons in scrapers  
**Fix**: Use `settings.DEFAULT_SEASON` everywhere

```python
# OLD (in scrapers):
params={'league': 39, 'season': 2024}

# NEW (using global settings):
settings = get_settings()
params={'league': settings.PREMIER_LEAGUE_ID, 'season': settings.DEFAULT_SEASON}
```

### Step 2: Update soccer_server.py Tools
**Keep same tool names and signatures, just change data source:**

```python
# BEFORE (direct API):
@mcp.tool()
def get_league_fixtures(league_id: int, season: int) -> Dict[str, Any]:
    response = requests.get(fixtures_url, headers=headers, params=fixtures_params)
    return response.json()

# AFTER (Supabase cache):
@mcp.tool()  
def get_league_fixtures(league_id: int, season: int) -> Dict[str, Any]:
    # Try cache first
    cached = get_cached_fixtures(league_id, season)
    if cached:
        return {"response": cached, "source": "cache"}
    
    # Fallback to API if cache miss
    response = requests.get(fixtures_url, headers=headers, params=fixtures_params)
    store_in_cache(response.json())
    return response.json()
```

### Step 3: Integration Result
✅ **Same MCP server** (soccer_server.py)  
✅ **Same tool names** (get_league_fixtures, get_standings, etc.)  
✅ **Same parameters** (league_id, season)  
✅ **Cached responses** (90% faster, zero API calls for cached data)  
✅ **Global season setting** (settings.DEFAULT_SEASON = 2025)

## What You Get
- **Your common use case**: `get_league_fixtures(39, 2025)` returns gameweek data instantly
- **Zero API calls**: For cached data (fixtures, teams, standings)
- **Smart fallback**: API calls only when cache is stale
- **Request tracking**: Never exceed 1,000/day limit
- **Same interface**: No changes to how you call MCP tools

**Ready to integrate?**
