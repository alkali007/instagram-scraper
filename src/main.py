import argparse
from .scraper_instagram import InstagramScraper
from .cleaning_json import JSONCleaner

def run(usernames):
    # Normalize: single username → list
    if isinstance(usernames, str):
        usernames = [usernames]

    for username in usernames:
        print(f"\n[INFO] Processing username: {username}")

        # Step 1: Scrape
        InstagramScraper(username)

        # Step 2: Clean
        JSONCleaner(username)

    print("\nAll scraping completed.")

def main():
    parser = argparse.ArgumentParser(
        description="Instagram Profile Scraper & JSON Cleaner"
    )
    
    # Accept 1 or many usernames from CLI
    parser.add_argument(
        "usernames",
        nargs="+",                      # "+" means 1 or more arguments
        help="Instagram username(s) to scrape"
    )

    args = parser.parse_args()

    # Run scraper logic
    run(args.usernames)

if __name__ == "__main__":
    main()
