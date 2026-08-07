import json
import os
import sys
import time
import requests

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")

if not BASE_URL:
    print(
        "[!] ERROR: 'BASE_URL' environment variable is not set in GitHub"
        " Secrets!"
    )
    sys.exit(1)

MATCHES_API_TEMPLATE = f"{BASE_URL}/papi/matches/{{category}}"
EXTRACT_API_TEMPLATE = f"{BASE_URL}/papi/extract-url/{{match_id}}"
REFERER_SUFFIX = f"|Referer={BASE_URL}"

CATEGORIES = [
    "football",
    "cricket",
    "basketball",
    "american-football",
    "fight",
    "tennis",
    "baseball",
    "hockey",
    "rugby",
    "motor-sports",
    "golf",
    "darts",
    "cycling",
    "snooker",
    "afl",
    "volleyball",
    "other",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": f"{BASE_URL}/",
}


def process_category(session, category):
    matches_api = MATCHES_API_TEMPLATE.format(category=category)
    print("==================================================")
    print(f"[-] Processing Category: '{category}'")
    print(f"[-] Fetching API: {matches_api}")
    print("==================================================")

    try:
        res = session.get(matches_api, timeout=15)
        if res.status_code != 200:
            print(f"[!] HTTP Error {res.status_code} for category '{category}'")
            return []

        matches = res.json()
        if not isinstance(matches, list):
            print(f"[!] Invalid JSON format for category '{category}'")
            return []

        total_matches = len(matches)
        print(f"[+] Found {total_matches} matches for '{category}'")

        category_results = []

        for idx, match in enumerate(matches, 1):
            match_id = match.get("id")
            title = match.get("title", "Unknown Match")
            league = match.get("league", "Unknown League")

            print(f"  [{idx}/{total_matches}] Match: {title}")
            print(f"        ID   : {match_id}")

            if not match_id:
                print("        [!] Missing match ID, skipping...")
                continue

            extract_url = EXTRACT_API_TEMPLATE.format(match_id=match_id)

            try:
                ext_res = session.get(extract_url, timeout=10)
                if ext_res.status_code == 200:
                    ext_data = ext_res.json()

                    raw_hls = ext_data.get("hlsUrl", "")
                    raw_sd = ext_data.get("sdUrl", "")

                    hls_url = f"{raw_hls}{REFERER_SUFFIX}" if raw_hls else ""
                    sd_url = f"{raw_sd}{REFERER_SUFFIX}" if raw_sd else ""

                    print(f"        [+] HLS: {hls_url if hls_url else 'N/A'}")
                    print(f"        [+] SD : {sd_url if sd_url else 'N/A'}")

                    match_obj = {
                        "matchId": match_id,
                        "title": title,
                        "league": league,
                        "category": match.get("category", category),
                        "date": match.get("date"),
                        "status": match.get("status"),
                        "teams": match.get("teams"),
                        "hlsUrl": hls_url,
                        "sdUrl": sd_url,
                    }
                    category_results.append(match_obj)
                else:
                    print(
                        f"        [!] Extract HTTP Error: {ext_res.status_code}"
                    )

            except Exception as e:
                print(f"        [!] Extraction Exception: {e}")

            time.sleep(0.3)

        return category_results

    except Exception as e:
        print(f"[!] Failed processing category '{category}': {e}")
        return []


def main():
    print("==================================================")
    print("   Automated Multi-Category Stream Extractor      ")
    print("==================================================")

    session = requests.Session()
    session.headers.update(HEADERS)

    for cat in CATEGORIES:
        data = process_category(session, cat)

        file_name = f"{cat}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved {len(data)} matches to '{file_name}'\n")

    print("[SUCCESS] All categories processed and JSON files saved!")


if __name__ == "__main__":
    main()
