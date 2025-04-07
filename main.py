import os
import frontmatter
from slugify import slugify
from pprint import pprint
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


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


def export_take(data):
    name = data["properties"]["Name"]["title"][0]["plain_text"]
    take = frontmatter.Post(
        content="",
        **{
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
        },
    )
    with open(f"export/{slugify(name)}.md", "w") as f:
        export = frontmatter.dumps(take)
        f.write(export)
    print(f"Exported take: {name} > {slugify(name)}.md")


if __name__ == "__main__":
    notion = Client(auth=os.environ["NOTION_TOKEN"])

    takes = notion.databases.query(
        **{
            "database_id": os.environ["NOTION_DATABASE"],
            "filter": {"property": "Publish", "checkbox": {"equals": True}},
        }
    )

    os.makedirs("export", exist_ok=True)

    for take in takes["results"]:
        export_take(take)
