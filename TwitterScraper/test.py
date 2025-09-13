#TwitterScraper/test.py
import os
import time
import json
import argparse
from typing import List, Dict
import tweepy


def auth_from_env():
    """
    Requires these environment variables:
      TWITTER_API_KEY, TWITTER_API_SECRET,
      TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
    """
    api_key = os.getenv("TWITTER_API_KEY", api_key)
    api_secret = os.getenv("TWITTER_API_SECRET", api_secret)
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", access_token)
    access_secret = os.getenv("TWITTER_ACCESS_SECRET", access_secret)

    if not all([api_key, api_secret, access_token, access_secret]):
        raise EnvironmentError(
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET"
        )
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    return api

def get_trends(api: tweepy.API, woeid: int = 1, top_n: int = 10):
    # woeid=1 -> Worldwide. Use another WOEID for specific countries/places.
    places = api.get_place_trends(id=woeid)
    if not places:
        return []
    trends = places[0].get("trends", [])
    # sort by tweet_volume (may be None) and take top_n
    trends_sorted = sorted(trends, key=lambda t: (t.get("tweet_volume") or 0), reverse=True)
    return trends_sorted[:top_n]

def fetch_tweets_for_query(api: tweepy.API, query: str, count: int = 20) -> List[Dict]:
    # Use search_tweets (v1.1). Exclude retweets for cleaner results.
    q = f"{query} -filter:retweets"
    results = []
    try:
        for status in tweepy.Cursor(api.search_tweets, q=q, lang="en", tweet_mode="extended").items(count):
            results.append({
                "id": status.id_str,
                "created_at": str(status.created_at),
                "user": {"id": status.user.id_str, "screen_name": status.user.screen_name},
                "text": status.full_text,
                "retweet_count": status.retweet_count,
                "favorite_count": getattr(status, "favorite_count", None)
            })
    except tweepy.TweepyException as e:
        print("Tweepy error when fetching tweets for query:", query, e)
        # If v1.1 access is restricted (403), try v2 bearer-token search as a fallback.
        client = _get_v2_client()
        if client is None:
            print("No TWITTER_BEARER_TOKEN found; cannot fallback to v2 API.")
            return results
        try:
            return fetch_tweets_for_query_v2(client, query, count)
        except Exception as e2:
            print("v2 fallback also failed:", e2)
            return results
    return results

def build_output(trends: List[Dict], api: tweepy.API, tweets_per_trend: int) -> Dict:
    output = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "trends": []}
    for t in trends:
        name = t.get("name")
        volume = t.get("tweet_volume")
        print(f"Fetching tweets for trend: {name} (volume: {volume})")
        tweets = fetch_tweets_for_query(api, name, tweets_per_trend)
        output["trends"].append({
            "name": name,
            "query": name,
            "tweet_volume": volume,
            "tweets": tweets
        })
        # small pause to be polite to rate limits
        time.sleep(1.0)
    return output

def main():
    parser = argparse.ArgumentParser(description="Search Twitter/X for a keyword/phrase (requires dev credentials).")
    parser.add_argument("--query", "-q", required=True, help="Keyword or phrase to search for (will exclude retweets).")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of tweets to fetch (default: 100).")
    parser.add_argument("--out", "-o", default="search_results.json", help="Output JSON file path.")
    args = parser.parse_args()

    api = auth_from_env()
    tweets = fetch_tweets_for_query(api, args.query, count=args.count)
    output = {
        "queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query": args.query,
        "requested_count": args.count,
        "returned_count": len(tweets),
        "tweets": tweets
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Saved output to", args.out)

# New helper: create a tweepy.Client if bearer token is present
def _get_v2_client():
    bearer = "<TWITTER_BEARER_TOKEN>"
    if not bearer:
        return None
    try:
        return tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)
    except Exception:
        return None

# New helper: use tweepy.Client.search_recent_tweets and map to the same result shape
def fetch_tweets_for_query_v2(client: tweepy.Client, query: str, count: int = 20) -> List[Dict]:
    q = f"{query} -is:retweet lang:en"
    results: List[Dict] = []
    max_per_request = 100  # API v2 max
    next_token = None
    remaining = count

    user_map = {}
    while remaining > 0:
        per_request = min(remaining, max_per_request)
        resp = client.search_recent_tweets(query=q,
                                          max_results=per_request,
                                          tweet_fields=["created_at", "public_metrics", "author_id", "text"],
                                          expansions=["author_id"],
                                          user_fields=["username"],
                                          next_token=next_token)
        if resp.data is None:
            break

        # build user map from includes
        includes = resp.includes or {}
        users = includes.get("users", [])
        for u in users:
            user_map[str(u.id)] = u.username

        for t in resp.data:
            pm = getattr(t, "public_metrics", {}) or {}
            author_id = getattr(t, "author_id", None)
            results.append({
                "id": str(t.id),
                "created_at": str(getattr(t, "created_at", "")),
                "user": {"id": str(author_id) if author_id is not None else None, "screen_name": user_map.get(str(author_id))},
                "text": getattr(t, "text", ""),
                "retweet_count": pm.get("retweet_count"),
                "favorite_count": pm.get("like_count")
            })
        remaining -= len(resp.data)
        meta = getattr(resp, "meta", {}) or {}
        next_token = meta.get("next_token")
        if not next_token:
            break

    return results

if __name__ == "__main__":
    main()