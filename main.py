import os
import requests
import frontmatter
from slugify import slugify
from pprint import pprint
from dotenv import load_dotenv
from notion_client import Client
from steam_web_api import Steam


load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])
steam = Steam(os.environ["STEAM_TOKEN"])


def translate_recommended(emoji):
    match emoji:
        case "👍":
            return "yes"
        case "👎":
            return "no"
        case "🤔":
            return "interested"
        case "😐":
            return "meh"
        case _:
            return ""


def get_cover_url(attrs):
    plats = attrs.get("platform").split(",")
    if "PC" in plats or "PCVR" in plats:
        games = steam.apps.search_games(attrs.get("name"))
        if games["apps"]:
            try:
                game_id = games["apps"][0]["id"]
                if isinstance(game_id, list):
                    game_id = game_id[0]
                return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game_id}/library_600x900_2x.jpg"
            except IndexError as e:
                print("Steam call returned value but index failed")
                print(e)
    if attrs.get("type") == "Movie" or attrs.get("type") == "TV":
        url = f"https://api.themoviedb.org/3/search/{attrs.get('type').lower()}"  # ?query=Mickey%2017&include_adult=false&language=en-US&page=1"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv('TMDB_API_KEY')}",
        }
        response = requests.get(
            url,
            headers=headers,
            params={
                "query": attrs.get("name")
                if attrs.get("type") == "Movie"
                else attrs.get("name").split(" Season ")[0],
                "include_adult": False,
                "language": "en-US",
                "page": 1,
            },
        )
        if response.status_code == 200:
            return f"https://image.tmdb.org/t/p/w1280{response.json()['results'][0]['poster_path']}"
        else:
            print("Movie lookup failed")
    return ""


def export_take(data):
    name = data["properties"]["Name"]["title"][0]["plain_text"]
    attrs = {
        "name": name,
        "slug": slugify(name),
        "type": data["properties"]["Type"]["select"]["name"],
        "platform": ",".join(
            map(lambda x: x["name"], data["properties"]["Platform"]["multi_select"])
        ),
        "date": data["properties"]["Date"]["date"]["start"],
        "score": data["properties"]["Score"]["number"],
        "recommended": translate_recommended(
            data["properties"]["Recommend"]["select"]["name"]
        ),
        "status": data["properties"]["Status"]["status"]["name"],
        "notion_id": data["id"],
    }
    attrs["cover"] = get_cover_url(attrs)
    take = frontmatter.Post(
        content="",
        **attrs,
    )
    with open(f"export/{slugify(name)}.md", "w") as f:
        export = frontmatter.dumps(take)
        f.write(export)
    print(f"Exported take: {name} > {slugify(name)}.md")


if __name__ == "__main__":
    takes = notion.databases.query(
        **{
            "database_id": os.environ["NOTION_DATABASE"],
            "filter": {"property": "Publish", "checkbox": {"equals": True}},
        }
    )

    os.makedirs("export", exist_ok=True)

    for take in takes["results"]:
        export_take(take)
