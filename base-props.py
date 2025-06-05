import requests
import pandas as pd
from datetime import datetime, timedelta
from fuzzywuzzy import process
import statsapi  # Add MLB-StatsAPI import
import re  # Add re module import for regex operations

# Function to get MLB games on a specific date
# def get_games_on_date(date="2025-06-02"):
#     url = f"https://statsapi.mlb.com/api/v1/schedule?date={date}&sportId=1"
#     try:
#         response = requests.get(url).json()
#         games = response.get("dates", [{}])[0].get("games", [])
#         return [{"gamePk": game["gamePk"], "teams": game["teams"]} for game in games]
#     except:
#         print(f"Error fetching games for {date}.")
#         return []

# Function to get active players for a game
# def get_game_players(game_pk):
#     url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/roster"
#     try:
#         response = requests.get(url).json()
#         players = []
#         for team in response.get("rosters", []):
#             for player in team.get("roster", []):
#                 if player["person"]["primaryPosition"]["type"] != "Pitcher":  # Exclude pitchers
#                     players.append(player["person"]["id"])
#         return list(set(players))  # Remove duplicates
#     except:
#         print(f"Error fetching roster for game {game_pk}.")
#         return []

# Function to get player stats (recent game logs or season)
# def get_player_stats(player_id, date="2025-06-02", use_game_log=True):
#     stats_data = None
#     source = None
#     season_year = date.split("-")[0] # Dynamically determine season year

#     if use_game_log:
#         # Use game log for last 7 days
#         start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
#         url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&group=hitting&startDate={start_date}&endDate={date}"
#         try:
#             response = requests.get(url).json()
#             stats_splits = response.get("stats", [{}])[0].get("splits", [])
#             if stats_splits:
#                 # Aggregate recent stats
#                 hits = sum(int(s["stat"].get("hits", 0)) for s in stats_splits)
#                 at_bats = sum(int(s["stat"].get("atBats", 0)) for s in stats_splits)
#                 home_runs = sum(int(s["stat"].get("homeRuns", 0)) for s in stats_splits)
#                 rbis = sum(int(s["stat"].get("rbi", 0)) for s in stats_splits)
#                 batting_avg = hits / at_bats if at_bats > 0 else 0.0
#                 stats_data = {
#                     "player_id": player_id,
#                     "name": stats_splits[0]["player"]["fullName"],
#                     "games": len(stats_splits), # Number of games in the log period
#                     "atBats": at_bats,
#                     "hits": hits,
#                     "batting_avg": round(batting_avg, 3),
#                     "home_runs": home_runs,
#                     "rbis": rbis
#                 }
#                 source = "game_log"
#         except requests.exceptions.RequestException as e:
#             print(f"Network error fetching game log for player {player_id}: {e}")
#         except (KeyError, IndexError, ValueError, TypeError) as e:
#             print(f"Error processing game log data for player {player_id}: {e}")

#     if stats_data is None: # Either use_game_log was false, or it was true but failed/yielded no data
#         # Fallback to season stats or primary if use_game_log is false
#         url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting&season={season_year}"
#         try:
#             response = requests.get(url).json()
#             stats_splits = response.get("stats", [{}])[0].get("splits", [])
#             if stats_splits:
#                 split_stat = stats_splits[0]["stat"]
#                 player_info = stats_splits[0]["player"]
#                 stats_data = {
#                     "player_id": player_id,
#                     "name": player_info["fullName"],
#                     "games": split_stat.get("gamesPlayed", 0), # Season games played
#                     "atBats": split_stat.get("atBats", 0),
#                     "hits": split_stat.get("hits", 0),
#                     "batting_avg": float(split_stat.get("avg", ".000")),
#                     "home_runs": split_stat.get("homeRuns", 0),
#                     "rbis": split_stat.get("rbi", 0)
#                 }
#                 source = "season"
#         except requests.exceptions.RequestException as e:
#             print(f"Network error fetching season stats for player {player_id}: {e}")
#         except (KeyError, IndexError, ValueError, TypeError) as e:
#             print(f"Error processing season stats data for player {player_id}: {e}")

#     if stats_data:
#         stats_data["stats_source"] = source
#     return stats_data

# Function to get FanDuel odds from The Odds API
def get_fanduel_odds(api_key, prop_type="batter_hits", date="2025-06-02"):
    sport_key = "baseball_mlb" 
    regions = "us"
    odds_format = "american"

    # The Odds API supports these main markets for MLB
    # We use h2h as it's the most reliable for getting all available props
    query_markets_for_api_call = "h2h" 

    # Map of our prop types to FanDuel's market keys
    # This helps ensure we're using the correct market keys when filtering
    prop_type_mapping = {
        "batter_hits": "player_props_hits",
        "batter_home_runs": "player_props_home_runs",
        "batter_rbis": "player_props_rbis",
        "batter_total_bases": "player_props_total_bases",
        "batter_runs_scored": "player_props_runs",
        "batter_hits_runs_rbis": "player_props_hits_runs_rbis",
        "batter_strikeouts": "player_props_strikeouts",
        "pitcher_strikeouts": "player_props_pitcher_strikeouts",
        "pitcher_hits_allowed": "player_props_pitcher_hits_allowed",
        "pitcher_walks": "player_props_pitcher_walks",
        "pitcher_earned_runs": "player_props_pitcher_earned_runs",
        "pitcher_outs": "player_props_pitcher_outs",
        "batter_first_home_run": "player_props_first_home_run",
        "pitcher_record_a_win": "player_props_pitcher_win"
    }

    # Get the FanDuel market key for our prop type
    fanduel_market_key = prop_type_mapping.get(prop_type, prop_type)

    base_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'api_key': api_key,
        'regions': regions,
        'markets': query_markets_for_api_call,
        'oddsFormat': odds_format,
        'date': date
    }

    print(f"  [get_fanduel_odds] Requesting URL: {base_url} with params: {params}")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Log the raw response only if debug is needed
        # print(f"  [get_fanduel_odds] Raw API Response for {date}:\n{data}")
        
        odds_data = []
        for event in data:
            event_id = event.get("id")
            event_teams = [team.get("name") for team in event.get("teams", [])]
            event_start_time = event.get("commence_time")
            
            for bookmaker in event.get("bookmakers", []):
                if bookmaker["key"] == "fanduel":
                    for market in bookmaker["markets"]:
                        if market["key"] == fanduel_market_key:
                            for outcome in market["outcomes"]:
                                # Handle both Over/Under and Yes/No props
                                if "Over" in outcome["description"] or "Yes" in outcome["description"]:
                                    player_name = outcome["description"].split(" Over")[0].split(" Yes")[0]
                                    odds_data.append({
                                        "event_id": event_id,
                                        "teams": " vs ".join(event_teams),
                                        "start_time": event_start_time,
                                        "player_name": player_name,
                                        "prop_type": prop_type,
                                        "odds": outcome["price"],
                                        "line": outcome.get("point", 0.5),
                                        "market_key": market["key"],
                                        "outcome_type": "Over" if "Over" in outcome["description"] else "Yes"
                                    })
        
        # Log usage quota
        if 'x-requests-remaining' in response.headers:
            remaining = response.headers['x-requests-remaining']
            used = response.headers.get('x-requests-used', 'unknown')
            print(f"  [get_fanduel_odds] API Usage - Remaining: {remaining}, Used: {used}")
            
            # Warn if running low on requests
            if int(remaining) < 10:
                print(f"  [get_fanduel_odds] WARNING: Low on API requests ({remaining} remaining)")
        
        return pd.DataFrame(odds_data)
    except requests.exceptions.HTTPError as http_err:
        print(f"  [get_fanduel_odds] HTTP error occurred: {http_err} - Status Code: {response.status_code}")
        if response.status_code == 422:
            print(f"  [get_fanduel_odds] 422 Error: Often means no data for the requested date/market or date is too far out/in past. Response text: {response.text}")
        return pd.DataFrame() # Ensure DataFrame is returned on HTTPError
    except requests.exceptions.RequestException as e:
        print(f"  [get_fanduel_odds] Error fetching odds: {e}")
        return pd.DataFrame() # Ensure DataFrame is returned on RequestException
    except ValueError as json_err: # Catches JSON decoding errors
        print(f"  [get_fanduel_odds] Error decoding JSON response: {json_err}. Response text: {response.text}")
        return pd.DataFrame()

# Function to fuzzy match player names
# def fuzzy_match_names(stats_df, odds_df):
#     matches = []
#     for name in stats_df["name"]:
#         match = process.extractOne(name, odds_df["player_name"], score_cutoff=80)
#         if match:
#             matches.append({"name": name, "player_name": match[0], "score": match[1]})
#         else:
#             matches.append({"name": name, "player_name": None, "score": None})
#     match_df = pd.DataFrame(matches)
#     return stats_df.merge(match_df, on="name").merge(odds_df, on="player_name", how="left")

# Main function to analyze players for prop bets on a specific date
# def analyze_prop_bets(prop_type="batter_hits", api_key="09314257ea26c706e582794ed5e084cd", date_for_odds=None):
#     # --- Date Setup ---
#     base_target_date_str = None
#     if date_for_odds:
#         base_target_date_str = date_for_odds
#         print(f"--- Base target date for odds specified: {base_target_date_str} ---")
#     else:
#         today = datetime.now()
#         tomorrow_dt = today + timedelta(days=1)
#         base_target_date_str = tomorrow_dt.strftime("%Y-%m-%d")
#         print(f"--- Base target date for odds (tomorrow): {base_target_date_str} ---")
#
#     # Create a list of dates to try: base_target_date and 2 days prior
#     dates_to_try = []
#     try:
#         base_date_dt = datetime.strptime(base_target_date_str, "%Y-%m-%d")
#         for i in range(3): # 0 (base date), 1 (1 day prior), 2 (2 days prior)
#             current_try_date_dt = base_date_dt - timedelta(days=i)
#             dates_to_try.append(current_try_date_dt.strftime("%Y-%m-%d"))
#     except ValueError:
#         print(f"Error: Invalid date format for base_target_date_str ('{base_target_date_str}'). Please use YYYY-MM-DD. Exiting.")
#         return
#
#     print(f"Analyzing for prop type: {prop_type}")
#
#     # --- Fetch Odds, trying the list of dates ---
#     odds_df = pd.DataFrame()
#     successful_odds_date_str = None
#
#     print(f"--- Starting attempts to fetch odds for up to {len(dates_to_try)} dates ---")
#     for date_str_to_try in dates_to_try:
#         print(f"Attempting to fetch odds for {prop_type} for games on: {date_str_to_try}")
#         current_odds_df = get_fanduel_odds(api_key, prop_type, date_str_to_try)
#         if not current_odds_df.empty:
#             odds_df = current_odds_df
#             successful_odds_date_str = date_str_to_try
#             print(f"Successfully fetched odds for {successful_odds_date_str}.")
#             break
#         else:
#             print(f"-> No odds successfully processed or returned for {date_str_to_try}.")
#
#     print(f"--- Finished attempts to fetch odds ---")
#     if odds_df.empty:
#         print(f"No FanDuel odds found for {prop_type} for any of the tried dates: {dates_to_try}. Exiting.")
#         return
#     
#     print(f"--- Found {len(odds_df)} betting opportunities from The Odds API for {prop_type} on {successful_odds_date_str} ---")
#
#     # --- Process and Display Data ---
#     # Format the start time to be more readable
#     if 'start_time' in odds_df.columns:
#         odds_df['start_time'] = pd.to_datetime(odds_df['start_time']).dt.strftime('%I:%M %p ET')
#     
#     # Group by game and find best odds for each game
#     game_summary = odds_df.groupby(['teams', 'start_time']).agg({
#         'odds': 'min',  # Best (lowest) odds for each game
#         'player_name': lambda x: list(x),  # List of players with props
#         'line': lambda x: list(x) if prop_type not in ["batter_first_home_run", "pitcher_record_a_win"] else None
#     }).reset_index()
#     
#     # Sort games by best odds (ascending)
#     game_summary = game_summary.sort_values('odds')
#     
#     # Print games sorted by best odds
#     print(f"\nGames Available for {prop_type.replace('_', ' ').title()} on {successful_odds_date_str}:")
#     print("\nGames are sorted by best available odds (lowest to highest):")
#     print("=" * 80)
#     
#     for _, game in game_summary.iterrows():
#         print(f"\n{game['teams']} - {game['start_time']}")
#         print(f"Best Available Odds: {game['odds']}")
#         print("-" * 40)
#         
#         # Get all props for this game
#         game_props = odds_df[odds_df['teams'] == game['teams']].sort_values('odds')
#         
#         # Print each prop for this game
#         for _, prop in game_props.iterrows():
#             if prop_type in ["batter_first_home_run", "pitcher_record_a_win"]:
#                 print(f"{prop['player_name']}: {prop['odds']} ({prop['outcome_type']})")
#             else:
#                 print(f"{prop['player_name']}: {prop['odds']} ({prop['outcome_type']} {prop['line']})")
#     
#     # Print summary statistics
#     print("\n" + "=" * 80)
#     print("\nSummary Statistics:")
#     print(f"Total Games: {len(game_summary)}")
#     print(f"Total Props: {len(odds_df)}")
#     print(f"Best Odds Available: {odds_df['odds'].min()}")
#     print(f"Worst Odds Available: {odds_df['odds'].max()}")
#     print(f"Average Odds: {odds_df['odds'].mean():.2f}")
#     if 'line' in odds_df.columns and prop_type not in ["batter_first_home_run", "pitcher_record_a_win"]:
#         print(f"Line Range: {odds_df['line'].min()} to {odds_df['line'].max()}")

# Example usage:
# analyze_prop_bets(prop_type="batter_home_runs", api_key="YOUR_API_KEY")
# analyze_prop_bets(prop_type="batter_rbis", api_key="YOUR_API_KEY", date_for_odds="2025-06-03")
# analyze_prop_bets(prop_type="batter_first_home_run", api_key="YOUR_API_KEY")

def get_league_leaders(stat_type='hitting', stat='avg', limit=5):
    """Get league leaders for hitting or pitching statistics using MLB Data API"""
    base_url = "http://lookup-service-prod.mlb.com/json/named"
    endpoint = f"leader_{stat_type}_repeater.bam"
    
    # Format parameters according to API docs
    params = {
        'sport_code': "'mlb'",  # Note the single quotes
        'results': f"'{limit}'",  # Note the single quotes
        'game_type': "'R'",  # Regular season
        'season': "'2024'",  # Current season
        'sort_column': f"'{stat}'",  # Note the single quotes
        f'leader_{stat_type}_repeater.col_in': f"'name_display_first_last,{stat}'"  # Note the single quotes
    }
    
    try:
        # Construct URL with proper format
        url = f"{base_url}/{endpoint}"
        print(f"Requesting URL: {url} with params: {params}")  # Debug print
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Debug print
        print(f"Response status: {response.status_code}")
        print(f"Response data: {data}")
        
        leaders = []
        if f'leader_{stat_type}_repeater' in data:
            leader_data = data[f'leader_{stat_type}_repeater']
            if 'leader_' + stat_type + '_mux' in leader_data:
                mux_data = leader_data['leader_' + stat_type + '_mux']
                if 'queryResults' in mux_data:
                    results = mux_data['queryResults']
                    if results.get('totalSize') != '0':
                        rows = results.get('row', [])
                        if not isinstance(rows, list):
                            rows = [rows]  # Handle single result case
                        for row in rows:
                            leaders.append({
                                'name': row['name_display_first_last'],
                                stat: row[stat]
                            })
        return leaders
    except Exception as e:
        print(f"Error fetching {stat_type} leaders: {e}")
        if 'response' in locals():
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return []

def get_moneyline_odds(api_key, date):
    sport_key = "baseball_mlb"
    regions = "us"
    odds_format = "american"
    market = "h2h"
    base_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        'api_key': api_key,
        'regions': regions,
        'markets': market,
        'oddsFormat': odds_format,
        'date': date
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        odds_data = []
        for event in data:
            event_id = event.get("id")
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            event_start_time = event.get("commence_time")
            if not home_team or not away_team:
                continue
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market["outcomes"]:
                            odds_data.append({
                                "event_id": event_id,
                                "home_team": home_team,
                                "away_team": away_team,
                                "start_time": event_start_time,
                                "bookmaker": bookmaker["title"],
                                "team": outcome["name"],
                                "odds": outcome["price"]
                            })
        return pd.DataFrame(odds_data)
    except Exception as e:
        print(f"Error fetching moneyline odds: {e}")
        if 'response' in locals():
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return pd.DataFrame()

def american_odds_to_pct(odds):
    try:
        odds = float(odds)
        if odds > 0:
            pct = 100 / (odds + 100)
        else:
            pct = abs(odds) / (abs(odds) + 100)
        return round(pct * 100, 1)
    except Exception:
        return None

def get_current_leaders(stat_type='hitting', stat=None, limit=5, season=None):
    """Get league leaders using MLB-StatsAPI"""
    # Map our stat names to MLB-StatsAPI stat IDs
    stat_mapping = {
        'hitting': {
            'avg': 'avg',
            'hr': 'homeRuns',
            'rbi': 'rbi',
            'obp': 'obp',
            'slg': 'slg'
        },
        'pitching': {
            'era': 'era',
            'so': 'strikeOuts',
            'whip': 'whip',
            'w': 'wins',
            'sv': 'saves'
        }
    }
    if stat is None:
        stat = 'avg' if stat_type == 'hitting' else 'era'
    mlb_stat = stat_mapping[stat_type].get(stat, stat)
    try:
        if season:
            leaders = statsapi.league_leaders(mlb_stat, season=season, limit=limit)
        else:
            leaders = statsapi.league_leaders(mlb_stat, limit=limit)
        return leaders
    except Exception as e:
        print(f"Error fetching {stat_type} leaders: {e}")
        return []

def get_player_id(player_name, stat_type):
    """Get player ID using MLB-StatsAPI"""
    try:
        # Use MLB-StatsAPI's lookup_player function
        player = statsapi.lookup_player(player_name)
        if player:
            return player[0]['id']
        return None
    except Exception as e:
        print(f"Error fetching player ID for {player_name}: {e}")
        return None

def get_current_stats(player_id, stat_type='hitting'):
    """Get current season stats for a player using MLB-StatsAPI"""
    try:
        # Use MLB-StatsAPI's player_stats function
        stats = statsapi.player_stats(player_id, type=stat_type)
        return stats
    except Exception as e:
        print(f"Error fetching current stats for player {player_id}: {e}")
        return None

def get_projected_stats(player_id, stat_type='hitting'):
    """Get projected stats for a player using MLB-StatsAPI"""
    try:
        # Use MLB-StatsAPI's player_stats function with projection type
        stats = statsapi.player_stats(player_id, type=stat_type, projection=True)
        return stats
    except Exception as e:
        print(f"Error fetching projected stats for player {player_id}: {e}")
        return None

def calculate_betting_value(current_stats, projected_stats, stat_type='hitting'):
    """Calculate betting value based on current and projected stats"""
    if not current_stats or not projected_stats:
        return None
        
    if stat_type == 'hitting':
        # For hitters, we look at positive trends (increasing stats)
        value_stats = {
            'avg': 1.5,    # Weight for batting average
            'hr': 2.0,     # Weight for home runs
            'rbi': 1.8,    # Weight for RBIs
            'obp': 1.3,    # Weight for on-base percentage
            'slg': 1.7     # Weight for slugging percentage
        }
    else:
        # For pitchers, we look at positive trends (decreasing ERA, increasing Ks)
        value_stats = {
            'era': -2.0,   # Negative weight for ERA (lower is better)
            'so': 1.5,     # Weight for strikeouts
            'whip': -1.8,  # Negative weight for WHIP (lower is better)
            'w': 1.2,      # Weight for wins
            'sv': 1.0      # Weight for saves
        }
    
    value_score = 0
    for stat, weight in value_stats.items():
        if stat in current_stats and stat in projected_stats:
            try:
                current = float(current_stats[stat])
                projected = float(projected_stats[stat])
                # Calculate trend (positive for improving stats)
                trend = (projected - current) * weight
                value_score += trend
            except (ValueError, TypeError):
                continue
    
    return value_score

def parse_leader_data(leader_str):
    """Parse the string output from league_leaders into a list of dictionaries with correct name/team split"""
    players = []
    if not leader_str:
        return players
    
    # Skip the header line
    lines = leader_str.strip().split('\n')[1:]
    
    for line in lines:
        if not line.strip():
            continue
        try:
            # Example line: 1   Bobby Witt Jr.       Kansas City Royals      .332
            # We'll split by two or more spaces to separate columns
            import re
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 4:
                rank = parts[0]
                name = parts[1]
                team = parts[2]
                value = parts[3]
                players.append({
                    'rank': int(rank),
                    'name': name,
                    'team': team,
                    'value': float(value) if value.replace('.', '', 1).isdigit() or value.replace('.', '', 1).replace('-', '', 1).isdigit() else value
                })
            elif len(parts) == 3:
                # Sometimes value is missing
                rank = parts[0]
                name = parts[1]
                team = parts[2]
                players.append({
                    'rank': int(rank),
                    'name': name,
                    'team': team,
                    'value': None
                })
        except Exception as e:
            print(f"Error parsing line '{line}': {e}")
            continue
    
    return players

def get_player_stats_for_value_analysis():
    """Get current season stats for value analysis (compare to league averages)"""
    print("\nMLB Player Value Analysis (Current Season vs. League Averages):\n")
    
    # Hitting Analysis
    print("Hitting Value Analysis:")
    print("-" * 60)
    
    # Get leaders for key hitting stats
    hitting_stats = ['avg', 'homeRuns', 'rbi', 'obp', 'slg']
    current_hitters = {stat: [] for stat in hitting_stats}
    all_hitters = {}
    
    for stat in hitting_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=10, statGroup='hitting')
            if leaders_str:
                players = parse_leader_data(leaders_str)
                current_hitters[stat] = players
                for player in players:
                    if player['name'] not in all_hitters:
                        all_hitters[player['name']] = {
                            'name': player['name'],
                            'team': player['team'],
                            'stats': {}
                        }
                    all_hitters[player['name']]['stats'][stat] = player['value']
        except Exception as e:
            print(f"Error fetching hitting leaders for {stat}: {e}")
    
    # Calculate league averages for each stat
    league_averages = {}
    for stat, players in current_hitters.items():
        values = [p['value'] for p in players if isinstance(p['value'], (int, float))]
        if values:
            league_averages[stat] = sum(values) / len(values)
        else:
            league_averages[stat] = 0
    
    # Calculate value scores for hitters (distance from league average, weighted)
    hitter_values = []
    weights = {
        'avg': 1.5,
        'homeRuns': 2.0,
        'rbi': 1.8,
        'obp': 1.3,
        'slg': 1.7
    }
    for name, data in all_hitters.items():
        value_score = 0
        stat_count = 0
        for stat, weight in weights.items():
            if stat in data['stats'] and league_averages[stat] != 0:
                try:
                    player_val = float(data['stats'][stat])
                    avg_val = float(league_averages[stat])
                    value_score += (player_val - avg_val) * weight
                    stat_count += 1
                except (ValueError, TypeError):
                    continue
        if stat_count > 0:
            hitter_values.append({
                'name': name,
                'team': data['team'],
                'current_stats': data['stats'],
                'value_score': value_score
            })
    
    # Sort and display top hitters
    if hitter_values:
        hitter_values.sort(key=lambda x: x['value_score'], reverse=True)
        print("\nTop 5 Hitting Value Picks (vs. League Avg):")
        for i, player in enumerate(hitter_values[:5], 1):
            print(f"\n{i}. {player['name']} ({player['team']}) - Value Score: {player['value_score']:.2f}")
            print("   Current Stats:", " | ".join(f"{k.upper()}: {v}" for k, v in player['current_stats'].items()))
    else:
        print("\nNo valid hitting value picks found.")
    
    print("\n" + "=" * 60)
    
    # Pitching Analysis
    print("\nPitching Value Analysis:")
    print("-" * 60)
    
    pitching_stats = ['era', 'strikeOuts', 'wins', 'saves', 'whip']
    current_pitchers = {stat: [] for stat in pitching_stats}
    all_pitchers = {}
    
    for stat in pitching_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=10, statGroup='pitching')
            if leaders_str:
                players = parse_leader_data(leaders_str)
                current_pitchers[stat] = players
                for player in players:
                    if player['name'] not in all_pitchers:
                        all_pitchers[player['name']] = {
                            'name': player['name'],
                            'team': player['team'],
                            'stats': {}
                        }
                    all_pitchers[player['name']]['stats'][stat] = player['value']
        except Exception as e:
            print(f"Error fetching pitching leaders for {stat}: {e}")
    
    # Calculate league averages for each stat
    league_averages_p = {}
    for stat, players in current_pitchers.items():
        values = [p['value'] for p in players if isinstance(p['value'], (int, float))]
        if values:
            league_averages_p[stat] = sum(values) / len(values)
        else:
            league_averages_p[stat] = 0
    
    # Calculate value scores for pitchers (distance from league average, weighted)
    pitcher_values = []
    weights_p = {
        'era': -2.0,    # Negative weight for ERA (lower is better)
        'strikeOuts': 1.5,
        'wins': 1.2,
        'saves': 1.0,
        'whip': -1.8    # Negative weight for WHIP (lower is better)
    }
    for name, data in all_pitchers.items():
        value_score = 0
        stat_count = 0
        for stat, weight in weights_p.items():
            if stat in data['stats'] and league_averages_p[stat] != 0:
                try:
                    player_val = float(data['stats'][stat])
                    avg_val = float(league_averages_p[stat])
                    value_score += (player_val - avg_val) * weight
                    stat_count += 1
                except (ValueError, TypeError):
                    continue
        if stat_count > 0:
            pitcher_values.append({
                'name': name,
                'team': data['team'],
                'current_stats': data['stats'],
                'value_score': value_score
            })
    
    # Sort and display top pitchers
    if pitcher_values:
        pitcher_values.sort(key=lambda x: x['value_score'], reverse=True)
        print("\nTop 5 Pitching Value Picks (vs. League Avg):")
        for i, player in enumerate(pitcher_values[:5], 1):
            print(f"\n{i}. {player['name']} ({player['team']}) - Value Score: {player['value_score']:.2f}")
            print("   Current Stats:", " | ".join(f"{k.upper()}: {v}" for k, v in player['current_stats'].items()))
    else:
        print("\nNo valid pitching value picks found.")

def show_moneyline_for_today(api_key):
    """Show moneyline odds and value analysis for today's games"""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    
    print(f"\nFetching MLB moneyline odds for {tomorrow_str}...")
    df = get_moneyline_odds(api_key, tomorrow_str)
    if df.empty:
        print("No moneyline odds found for tomorrow.")
        return

    # Format start time and convert to datetime for proper sorting
    df['start_time'] = pd.to_datetime(df['start_time'])
    # Convert UTC to MST (UTC-7) for display
    df['start_time_mst'] = df['start_time'].dt.tz_convert('America/Denver')
    df['start_time_fmt'] = df['start_time_mst'].dt.strftime('%Y-%m-%d %I:%M %p MT')
    
    # Filter for only tomorrow's games by comparing the date part only
    tomorrow_date = pd.Timestamp(tomorrow_str).date()
    df['game_date'] = df['start_time_mst'].dt.date
    df = df[df['game_date'] == tomorrow_date]
    
    if df.empty:
        print("No games scheduled for tomorrow.")
        return
    
    # Group by event (game) and get best odds for each team
    games = []
    for (event_id, start_time), group in df.groupby(['event_id', 'start_time']):
        home_team = group.iloc[0]['home_team']
        away_team = group.iloc[0]['away_team']
        start_time_fmt = group.iloc[0]['start_time_fmt']
        
        # For each team, get the best (highest) odds (most favorable for bettor)
        best_team_odds = []
        for team in [home_team, away_team]:
            # Get all odds for this team and sort by most favorable (highest) odds
            team_odds = group[group['team'] == team].sort_values('odds', ascending=False)
            if not team_odds.empty:
                best_odds = team_odds.iloc[0]
                pct = american_odds_to_pct(best_odds['odds'])
                best_team_odds.append({
                    'team': team,
                    'odds': best_odds['odds'],
                    'bookmaker': best_odds['bookmaker'],
                    'pct': pct,
                    'is_favorite': best_odds['odds'] < 0  # True if negative odds (favorite)
                })
        
        # Sort teams: favorites first (negative odds), then by absolute value of odds
        best_team_odds.sort(key=lambda x: (not x['is_favorite'], abs(x['odds'])))
        
        # Calculate the best odds for this game (highest absolute value)
        best_game_odds = max(abs(odds['odds']) for odds in best_team_odds)
        
        games.append({
            'home_team': home_team,
            'away_team': away_team,
            'start_time': start_time,
            'start_time_fmt': start_time_fmt,
            'odds': best_team_odds,
            'best_game_odds': best_game_odds
        })
    
    # Sort games by best odds (highest absolute value first)
    games.sort(key=lambda x: x['best_game_odds'], reverse=True)
    
    # Print moneyline odds
    print(f"\nMLB Moneyline Odds for {tomorrow_str} (Best Odds First):\n")
    for game in games:
        print(f"{game['away_team']} @ {game['home_team']} - {game['start_time_fmt']}")
        for team_odds in game['odds']:
            print(f"  {team_odds['team']}: {team_odds['pct']}% ({team_odds['odds']}) - {team_odds['bookmaker']}")
        print("-" * 60)
    
    # Get player stats and value analysis
    get_player_stats_for_value_analysis()

def show_current_leaders():
    """Display current season leaders for both hitting and pitching stats"""
    print("\nMLB 2024 Season Leaders")
    print("=" * 60)
    
    # Hitting Leaders
    print("\nHITTING LEADERS")
    print("-" * 60)
    hitting_stats = {
        'avg': 'Batting Average',
        'homeRuns': 'Home Runs',
        'rbi': 'RBI',
        'obp': 'On-Base %',
        'slg': 'Slugging %',
        'ops': 'OPS',
        'hits': 'Hits',
        'doubles': 'Doubles',
        'triples': 'Triples',
        'stolenBases': 'Stolen Bases'
    }
    
    for stat, stat_name in hitting_stats.items():
        try:
            # Get leaders as a string and parse it
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=5, statGroup='hitting')
            if leaders_str:
                print(f"\n{stat_name} Leaders:")
                # Split the string into lines and process each line
                for line in leaders_str.split('\n'):
                    if line.strip():  # Skip empty lines
                        print(line.strip())
        except Exception as e:
            print(f"Error fetching {stat_name} leaders: {e}")
    
    # Pitching Leaders
    print("\nPITCHING LEADERS")
    print("-" * 60)
    pitching_stats = {
        'era': 'ERA',
        'strikeOuts': 'Strikeouts',
        'wins': 'Wins',
        'saves': 'Saves',
        'whip': 'WHIP',
        'inningsPitched': 'Innings Pitched',
        'hitsAllowed': 'Hits Allowed',
        'earnedRuns': 'Earned Runs',
        'walks': 'Walks',
        'qualityStarts': 'Quality Starts'
    }
    
    for stat, stat_name in pitching_stats.items():
        try:
            # Get leaders as a string and parse it
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=5, statGroup='pitching')
            if leaders_str:
                print(f"\n{stat_name} Leaders:")
                # Split the string into lines and process each line
                for line in leaders_str.split('\n'):
                    if line.strip():  # Skip empty lines
                        print(line.strip())
        except Exception as e:
            print(f"Error fetching {stat_name} leaders: {e}")

def generate_html_report(leaders_data, moneyline_data, value_analysis_data, moneyline_summary=None):
    """Generate a fancy HTML report with all MLB stats and odds"""
    html_template = """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>MLB Daily Report</title>
        <style>
            :root {{
                --primary-color: #002D72;
                --secondary-color: #D50032;
                --background-color: #f5f5f5;
                --card-background: #ffffff;
                --text-color: #333333;
                --border-color: #e0e0e0;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: var(--background-color);
                color: var(--text-color);
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            .header {{
                text-align: center;
                padding: 20px;
                background-color: var(--primary-color);
                color: white;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            
            .section {{
                background-color: var(--card-background);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .section-title {{
                color: var(--primary-color);
                border-bottom: 2px solid var(--secondary-color);
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            
            .stat-card {{
                background-color: var(--card-background);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 15px;
            }}
            
            .stat-title {{
                color: var(--secondary-color);
                font-weight: bold;
                margin-bottom: 10px;
            }}
            
            .leader-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            
            .leader-table th, .leader-table td {{
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
            }}
            
            .leader-table th {{
                background-color: var(--primary-color);
                color: white;
            }}
            
            .leader-table tr:nth-child(even) {{
                background-color: #f8f8f8;
            }}
            
            .game-card {{
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }}
            
            .game-header {{
                font-weight: bold;
                color: var(--primary-color);
                margin-bottom: 10px;
            }}
            
            .odds-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
            .odds-table th, .odds-table td {{ padding: 6px; border-bottom: 1px solid var(--border-color); }}
            .odds-table th {{ background-color: #e8e8e8; }}
            .favorite {{ color: var(--secondary-color); font-weight: bold; }}
            .value-score {{ font-weight: bold; color: var(--secondary-color); }}
            .timestamp {{ text-align: center; color: #666; font-size: 0.9em; margin-top: 20px; }}
            .summary-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .summary-table th, .summary-table td {{ padding: 6px; border-bottom: 1px solid var(--border-color); }}
            .summary-table th {{ background-color: #e8e8e8; }}
        </style>
    </head>
    <body>
        <div class=\"container\">
            <div class=\"header\">
                <h1>MLB Daily Report</h1>
                <p>Generated on {timestamp}</p>
            </div>
            
            <div class=\"section\">
                <h2 class=\"section-title\">Today's Games</h2>
                {moneyline_section}
                {moneyline_summary_section}
            </div>
            
            <div class=\"section\">
                <h2 class=\"section-title\">League Leaders</h2>
                <div class=\"stats-grid\">
                    <div class=\"stat-card\">
                        <h3 class=\"stat-title\">Hitting Leaders</h3>
                        {hitting_leaders}
                    </div>
                    <div class=\"stat-card\">
                        <h3 class=\"stat-title\">Pitching Leaders</h3>
                        {pitching_leaders}
                    </div>
                </div>
            </div>
            
            <div class=\"section\">
                <h2 class=\"section-title\">Value Analysis</h2>
                <div class=\"stats-grid\">
                    <div class=\"stat-card\">
                        <h3 class=\"stat-title\">Top Hitting Value Picks</h3>
                        {hitting_value}
                    </div>
                    <div class=\"stat-card\">
                        <h3 class=\"stat-title\">Top Pitching Value Picks</h3>
                        {pitching_value}
                    </div>
                </div>
            </div>
            
            <div class=\"timestamp\">
                Last updated: {timestamp}
            </div>
        </div>
    </body>
    </html>
    """
    
    def format_leaders_table(leaders_str):
        if not leaders_str:
            return "<p>No data available</p>"
        
        lines = leaders_str.strip().split('\n')
        if len(lines) <= 1:
            return "<p>No data available</p>"
        
        html = '<table class="leader-table">'
        # Header row
        html += '<tr><th>Rank</th><th>Player</th><th>Team</th><th>Value</th></tr>'
        
        # Data rows
        for line in lines[1:]:  # Skip header line
            if not line.strip():
                continue
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 4:
                html += f'<tr><td>{parts[0]}</td><td>{parts[1]}</td><td>{parts[2]}</td><td>{parts[3]}</td></tr>'
        
        html += '</table>'
        return html
    
    def format_moneyline_section(games):
        if not games:
            return "<p>No moneyline odds found for tomorrow.</p>"
        html = ''
        for game in games:
            html += f'<div class="game-card">'
            html += f'<div class="game-header">{game["away_team"]} @ {game["home_team"]} - {game["start_time_fmt"]}</div>'
            html += '<table class="odds-table">'
            html += '<tr><th>Team</th><th>Bookmaker</th><th>Odds</th><th>Win Probability</th><th>Favorite?</th></tr>'
            for team in game['teams']:
                for odds in team['odds']:
                    html += f'<tr>'
                    html += f'<td>{team["team"]}</td>'
                    html += f'<td>{odds["bookmaker"]}</td>'
                    html += f'<td>{odds["odds"]}</td>'
                    html += f'<td>{odds["pct"]}%</td>'
                    html += f'<td>{"<span class=\"favorite\">Yes</span>" if odds["is_favorite"] else "No"}</td>'
                    html += '</tr>'
            html += '</table>'
            html += '</div>'
        return html
    
    def format_moneyline_summary(summary):
        if not summary:
            return ''
        html = '<table class="summary-table">'
        html += '<tr><th>Total Games</th><td>{}</td></tr>'.format(summary.get('total_games', ''))
        html += '<tr><th>Total Props</th><td>{}</td></tr>'.format(summary.get('total_props', ''))
        html += '<tr><th>Best Odds Available</th><td>{}</td></tr>'.format(summary.get('best_odds', ''))
        html += '<tr><th>Worst Odds Available</th><td>{}</td></tr>'.format(summary.get('worst_odds', ''))
        html += '<tr><th>Average Odds</th><td>{:.2f}</td></tr>'.format(summary.get('avg_odds', 0))
        if summary.get('line_range'):
            html += '<tr><th>Line Range</th><td>{}</td></tr>'.format(summary['line_range'])
        html += '</table>'
        return html
    
    def format_value_analysis(players, stat_type):
        if not players:
            return "<p>No value picks available</p>"
        
        html = '<table class="leader-table">'
        html += '<tr><th>Rank</th><th>Player</th><th>Team</th><th>Value Score</th><th>Stats</th></tr>'
        
        for i, player in enumerate(players[:5], 1):
            stats_str = " | ".join(f"{k.upper()}: {v}" for k, v in player['current_stats'].items())
            html += f'''
            <tr>
                <td>{i}</td>
                <td>{player['name']}</td>
                <td>{player['team']}</td>
                <td class="value-score">{player['value_score']:.2f}</td>
                <td>{stats_str}</td>
            </tr>
            '''
        
        html += '</table>'
        return html
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format moneyline section
    moneyline_section = format_moneyline_section(moneyline_data)
    moneyline_summary_section = format_moneyline_summary(moneyline_summary)
    
    # Format leaders sections
    hitting_leaders = format_leaders_table(leaders_data.get('hitting', {}).get('avg', ''))
    pitching_leaders = format_leaders_table(leaders_data.get('pitching', {}).get('era', ''))
    
    # Format value analysis sections
    hitting_value = format_value_analysis(value_analysis_data.get('hitting', []), 'hitting')
    pitching_value = format_value_analysis(value_analysis_data.get('pitching', []), 'pitching')
    
    # Fill in the template
    html_content = html_template.format(
        timestamp=timestamp,
        moneyline_section=moneyline_section,
        moneyline_summary_section=moneyline_summary_section,
        hitting_leaders=hitting_leaders,
        pitching_leaders=pitching_leaders,
        hitting_value=hitting_value,
        pitching_value=pitching_value
    )
    
    # Write to file
    with open('mlb_daily_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return 'mlb_daily_report.html'

def collect_report_data():
    """Collect all data needed for the HTML report"""
    # Get leaders data
    leaders_data = {
        'hitting': {},
        'pitching': {}
    }
    
    # Collect hitting leaders
    hitting_stats = ['avg', 'homeRuns', 'rbi', 'obp', 'slg']
    for stat in hitting_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=5, statGroup='hitting')
            leaders_data['hitting'][stat] = leaders_str
        except Exception as e:
            print(f"Error fetching hitting leaders for {stat}: {e}")
    
    # Collect pitching leaders
    pitching_stats = ['era', 'strikeOuts', 'wins', 'saves', 'whip']
    for stat in pitching_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=5, statGroup='pitching')
            leaders_data['pitching'][stat] = leaders_str
        except Exception as e:
            print(f"Error fetching pitching leaders for {stat}: {e}")
    
    # Get moneyline data
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    df = get_moneyline_odds("09314257ea26c706e582794ed5e084cd", tomorrow)
    
    # Process moneyline data
    moneyline_data = []
    all_odds = []
    if not df.empty:
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['start_time_mst'] = df['start_time'].dt.tz_convert('America/Denver')
        df['start_time_fmt'] = df['start_time_mst'].dt.strftime('%Y-%m-%d %I:%M %p MT')
        for (event_id, start_time), group in df.groupby(['event_id', 'start_time']):
            home_team = group.iloc[0]['home_team']
            away_team = group.iloc[0]['away_team']
            start_time_fmt = group.iloc[0]['start_time_fmt']
            teams = []
            for team in [home_team, away_team]:
                team_odds_rows = group[group['team'] == team]
                team_odds = []
                for _, row in team_odds_rows.iterrows():
                    pct = american_odds_to_pct(row['odds'])
                    team_odds.append({
                        'bookmaker': row['bookmaker'],
                        'odds': row['odds'],
                        'pct': pct,
                        'is_favorite': row['odds'] < 0
                    })
                    all_odds.append(row['odds'])
                teams.append({'team': team, 'odds': team_odds})
            moneyline_data.append({
                'home_team': home_team,
                'away_team': away_team,
                'start_time_fmt': start_time_fmt,
                'teams': teams
            })
    # Moneyline summary
    moneyline_summary = None
    if all_odds:
        moneyline_summary = {
            'total_games': len(moneyline_data),
            'total_props': len(all_odds),
            'best_odds': min(all_odds),
            'worst_odds': max(all_odds),
            'avg_odds': sum(all_odds) / len(all_odds),
            'line_range': None  # Could be filled if line info is available
        }
    
    # Get value analysis data
    value_analysis_data = {
        'hitting': [],
        'pitching': []
    }
    
    # Collect hitting value analysis
    hitting_stats = ['avg', 'homeRuns', 'rbi', 'obp', 'slg']
    current_hitters = {stat: [] for stat in hitting_stats}
    all_hitters = {}
    
    for stat in hitting_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=10, statGroup='hitting')
            if leaders_str:
                players = parse_leader_data(leaders_str)
                current_hitters[stat] = players
                for player in players:
                    if player['name'] not in all_hitters:
                        all_hitters[player['name']] = {
                            'name': player['name'],
                            'team': player['team'],
                            'stats': {}
                        }
                    all_hitters[player['name']]['stats'][stat] = player['value']
        except Exception as e:
            print(f"Error fetching hitting leaders for {stat}: {e}")
    
    # Calculate league averages and value scores for hitters
    league_averages = {}
    for stat, players in current_hitters.items():
        values = [p['value'] for p in players if isinstance(p['value'], (int, float))]
        if values:
            league_averages[stat] = sum(values) / len(values)
        else:
            league_averages[stat] = 0
    
    weights = {
        'avg': 1.5,
        'homeRuns': 2.0,
        'rbi': 1.8,
        'obp': 1.3,
        'slg': 1.7
    }
    
    for name, data in all_hitters.items():
        value_score = 0
        stat_count = 0
        for stat, weight in weights.items():
            if stat in data['stats'] and league_averages[stat] != 0:
                try:
                    player_val = float(data['stats'][stat])
                    avg_val = float(league_averages[stat])
                    value_score += (player_val - avg_val) * weight
                    stat_count += 1
                except (ValueError, TypeError):
                    continue
        if stat_count > 0:
            value_analysis_data['hitting'].append({
                'name': name,
                'team': data['team'],
                'current_stats': data['stats'],
                'value_score': value_score
            })
    
    # Sort hitting value picks
    value_analysis_data['hitting'].sort(key=lambda x: x['value_score'], reverse=True)
    
    # Similar process for pitchers
    pitching_stats = ['era', 'strikeOuts', 'wins', 'saves', 'whip']
    current_pitchers = {stat: [] for stat in pitching_stats}
    all_pitchers = {}
    
    for stat in pitching_stats:
        try:
            leaders_str = statsapi.league_leaders(stat, season=2024, limit=10, statGroup='pitching')
            if leaders_str:
                players = parse_leader_data(leaders_str)
                current_pitchers[stat] = players
                for player in players:
                    if player['name'] not in all_pitchers:
                        all_pitchers[player['name']] = {
                            'name': player['name'],
                            'team': player['team'],
                            'stats': {}
                        }
                    all_pitchers[player['name']]['stats'][stat] = player['value']
        except Exception as e:
            print(f"Error fetching pitching leaders for {stat}: {e}")
    
    # Calculate league averages and value scores for pitchers
    league_averages_p = {}
    for stat, players in current_pitchers.items():
        values = [p['value'] for p in players if isinstance(p['value'], (int, float))]
        if values:
            league_averages_p[stat] = sum(values) / len(values)
    else: 
            league_averages_p[stat] = 0
    
    weights_p = {
        'era': -2.0,
        'strikeOuts': 1.5,
        'wins': 1.2,
        'saves': 1.0,
        'whip': -1.8
    }
    
    for name, data in all_pitchers.items():
        value_score = 0
        stat_count = 0
        for stat, weight in weights_p.items():
            if stat in data['stats'] and league_averages_p[stat] != 0:
                try:
                    player_val = float(data['stats'][stat])
                    avg_val = float(league_averages_p[stat])
                    value_score += (player_val - avg_val) * weight
                    stat_count += 1
                except (ValueError, TypeError):
                    continue
        if stat_count > 0:
            value_analysis_data['pitching'].append({
                'name': name,
                'team': data['team'],
                'current_stats': data['stats'],
                'value_score': value_score
            })
    
    # Sort pitching value picks
    value_analysis_data['pitching'].sort(key=lambda x: x['value_score'], reverse=True)
    
    return leaders_data, moneyline_data, value_analysis_data, moneyline_summary

if __name__ == "__main__":
    # Collect all data for the report
    leaders_data, moneyline_data, value_analysis_data, moneyline_summary = collect_report_data()
    
    # Generate the HTML report
    report_file = generate_html_report(leaders_data, moneyline_data, value_analysis_data, moneyline_summary)
    print(f"\nHTML report generated: {report_file}")
    
    # Also show the data in the console
    show_current_leaders()
    show_moneyline_for_today(api_key="09314257ea26c706e582794ed5e084cd")