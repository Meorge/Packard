from json import dump, load
from os.path import join, exists
from os import mkdir
from yattag import Doc
from story_link import LINK_RE


def check_story_for_errors(story_data: dict):
    story_errors = {block["id"]: [] for block in story_data["blocks"]}
    unique_blocks: set[dict] = set()
    for block in story_data["blocks"]:
        if block["id"] in unique_blocks:
            story_errors[block["id"]].append(
                {"type": "non_unique_id", "id": block["id"]}
            )
        unique_blocks.add(block["id"])

    for block in story_data["blocks"]:
        for _, target_block_id in LINK_RE.findall(block["body"]):
            if target_block_id not in unique_blocks:
                story_errors[block["id"]].append(
                    {
                        "id": block["id"],
                        "type": "unknown_id_referenced",
                        "referenced_id": target_block_id,
                    }
                )
    return story_errors

def error_to_string(error: dict) -> str:
    t = error.get("type", "")
    if t == "non_unique_id":
        return f"ID is not unique"
    elif t == "unknown_id_referenced":
        return f"Block with ID \"{error['referenced_id']}\" doesn't exist"
    else:
        return f"Unknown error (code \"{t}\")"

def errors_as_list(errors: dict[str, list[dict]]) -> list[dict]:
    errors_out: list[dict] = []
    for id, errors_for_id in errors.items():
        errors_out.extend(errors_for_id.copy())
    return errors_out


def compile_story_to_html(base_path: str, story_source_path: str):
    loaded_story = load_story(story_source_path)

    pages_dir = join(base_path, "pages")
    if not exists(pages_dir):
        mkdir(pages_dir)

    for block in loaded_story.get("blocks", []):
        block_page_path = join(pages_dir, f"{block['id']}.html")
        block_page_content = LINK_RE.sub(r'<a href="\2.html">\1</a>', block["body"])
        block_page_content = block_page_content.replace("\n", "<br/>")

        doc, tag, text = Doc().tagtext()
        doc.asis("<!DOCTYPE html>")
        with tag("html"):
            with tag("body"):
                doc.asis(block_page_content)

        with open(block_page_path, "w") as f:
            f.write(doc.getvalue())

    # Now create index file
    with open(join(base_path, "index.html"), "w") as f:
        doc, tag, text = Doc().tagtext()
        doc.asis("<!DOCTYPE html>")
        with tag("html"):
            with tag("head"):
                doc.stag(
                    "meta",
                    **{
                        "http-equiv": "refresh",
                        "content": f"0; url='pages/{loaded_story['start']}.html'",
                    },
                )

        f.write(doc.getvalue())


def save_story(base_path: str, story_data: dict):
    meta_path = join(base_path, "meta")
    content_path = join(base_path, "content")

    if not exists(meta_path):
        mkdir(meta_path)
    if not exists(content_path):
        mkdir(content_path)

    list_of_block_ids = []
    for block in story_data["blocks"]:
        content = {
            "x": block["x"],
            "y": block["y"],
            "title": block["title"],
        }
        with open(join(meta_path, f"{block['id']}.json"), "w") as f:
            dump(content, f, indent=4)

        with open(join(content_path, f"{block['id']}.txt"), "w") as f:
            f.write(block["body"])

        list_of_block_ids.append(block["id"])

    with open(join(base_path, f"main.json"), "w") as f:
        dump({"blocks": list_of_block_ids, "start": story_data["start"]}, f, indent=4)


def load_story(base_path: str):
    # Load the list of block titles
    metadata: dict
    with open(join(base_path, "main.json")) as f:
        metadata = load(f)

    list_of_block_ids: list[str] = metadata.get("blocks", [])

    blocks: list[dict] = []
    for block_id in list_of_block_ids:
        # Find this block's metadata file
        block_metadata: dict
        with open(join(base_path, "meta", f"{block_id}.json")) as f:
            block_metadata = load(f)

        block_body: str
        with open(join(base_path, "content", f"{block_id}.txt")) as f:
            block_body = f.read()

        blocks.append(
            {
                "x": block_metadata.get("x", None),
                "y": block_metadata.get("y", None),
                "title": block_metadata.get("title", block_id),
                "id": block_id,
                "body": block_body,
            }
        )

    return {"blocks": blocks, "start": metadata.get("start", None)}
