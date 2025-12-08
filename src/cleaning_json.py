import os
import json
import re
from datetime import datetime

def extract_hashtags(text):
    if not text:
        return []
    return re.findall(r"#\w+", text)

def extract_mentions(text):
    if not text:
        return []
    return re.findall(r"@\w+", text)

def unix_to_iso(ts):
    try:
        return datetime.utcfromtimestamp(ts).isoformat()
    except:
        return None

def build_final_json(profile_json, posts_json_list):
    user = profile_json["data"]["user"]

    # -----------------------------
    # Build profile section
    # -----------------------------
    result = {
        "id": user.get("id"),
        "username": user.get("username"),
        "url": f"https://www.instagram.com/{user.get('username')}",
        "fullName": user.get("full_name"),
        "biography": user.get("biography"),
        "externalUrls": [],
        "externalUrl": user.get("external_url"),
        "externalUrlShimmed": user.get("external_lynx_url"),
        "followersCount": user.get("follower_count"),
        "followsCount": user.get("following_count"),
        "isBusinessAccount": user.get("is_business"),
        "businessCategoryName": user.get("category"),
        "private": user.get("is_private"),
        "verified": user.get("is_verified"),
        "profilePicUrl": user.get("profile_pic_url"),
        "profilePicUrlHD": (
            user.get("hd_profile_pic_url_info", {}).get("url")
            if isinstance(user.get("hd_profile_pic_url_info"), dict)
            else None
        ),
        "postsCount": user.get("media_count"),
        "latestPosts": []
    }

    # External URLs
    bio_links = user.get("bio_links") or []
    for link in bio_links:
        result["externalUrls"].append({
            "title": link.get("title"),
            "lynx_url": link.get("lynx_url"),
            "url": link.get("url"),
            "link_type": link.get("link_type")
        })

    # -----------------------------
    # Build posts section
    # -----------------------------
    for posts_json in posts_json_list:
        edges = posts_json["data"]["xdt_api__v1__feed__user_timeline_graphql_connection"].get("edges", [])

        for edge in edges:
            node = edge.get("node", {})
            caption = (node.get("caption") or {}).get("text")

            short_code = node.get("code")

            post_obj = {
                "id": node.get("pk"),
                "shortCode": short_code,
                "caption": caption,
                "hashtags": extract_hashtags(caption),
                "mentions": extract_mentions(caption),
                "url": f"https://www.instagram.com/p/{short_code}/" if short_code else None,
                "commentsCount": node.get("comment_count"),
                "dimensionsHeight": node.get("original_height"),
                "dimensionsWidth": node.get("original_width"),
                "displayUrl": node.get("display_uri"),
                "likesCount": node.get("like_count"),
                "videoViewCount": node.get("view_count"),
                "timestamp": unix_to_iso(node.get("taken_at")),
                "ownerUsername": node.get("user", {}).get("username"),
                "ownerId": node.get("user", {}).get("pk"),
                "productType": node.get("product_type"),
                "isPinned": bool(node.get("timeline_pinned_user_ids")),
                "isCommentsDisabled": node.get("comments_disabled"),
            }

            result["latestPosts"].append(post_obj)

    return result

def JSONCleaner(username):
    # Base path and username
    base_path = "data/raw"

    # Merge paths properly
    user_path = os.path.join(base_path, username)

    # Make sure directory exists
    if not os.path.exists(user_path):
        raise FileNotFoundError(f"Folder does not exist: {user_path}")

    latest_posts = []
    profile = []

    # 1. Remove JSON files smaller than 1000 bytes
    for file in os.listdir(user_path):
        if not file.endswith(".json"):
            continue

        file_path = os.path.join(user_path, file)

        if os.path.getsize(file_path) < 1000:
            print(f"Removing small JSON file: {file_path}")
            os.remove(file_path)
            continue

        else:
          # Try opening JSON file
          try:
              with open(file_path, "r") as f:
                  content = json.load(f)
          except Exception as e:
              print(f"Error reading JSON {file}: {e}")
              continue

          # Ensure top structure exists
          if not isinstance(content, dict) or "data" not in content:
              print(f"Invalid structure, skipping: {file}")
              continue

          data = content["data"]

          # -------------------------
          # Case 1: Latest posts
          # -------------------------
          if "xdt_api__v1__feed__user_timeline_graphql_connection" in data:
              latest_posts.append(content)
              print(f"Added to latest_posts: {file}")

          # -------------------------
          # Case 2: Profile data
          # -------------------------
          elif "user" in data:
              profile.append(content)
              print(f"Added to profile: {file}")

          else:
              print(f"No matching keys, skipping: {file}")

    print("\nSummary:")
    print("Latest posts count:", len(latest_posts))
    print("Profile count:", len(profile))

    final_json = build_final_json(
        profile_json=profile[0],            # normally only one profile JSON
        posts_json_list=latest_posts        # many post JSON files
    )

    output_path = "data/clean"
    os.makedirs(output_path, exist_ok=True)

    output_file = f"{output_path}/{username}_cleaned_instagram_profile.json"

    with open(output_file, "w") as f:
        json.dump(final_json, f, indent=2)

    print(f"Saved cleaned JSON to {output_file}")
