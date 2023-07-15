from story_document_block import StoryBlockGraphicsItem
from json import dump, load
from os.path import join, exists
from os import mkdir
from re import compile
from yattag import Doc


def compile_story_to_html(base_path: str, story_source_path: str):
    loaded_story = load_story(story_source_path)

    LINK_RE = compile(r"\[\[(.*?)\]\]")

    pages_dir = join(base_path, "pages")
    if not exists(pages_dir):
        mkdir(pages_dir)

    for block in loaded_story.get("blocks", []):
        block_page_path = join(pages_dir, f"{block['name']}.html")
        block_page_content = LINK_RE.sub(r'<a href="\1.html">\1</a>', block["body"])
        block_page_content = block_page_content.replace('\n','<br/>')

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


def save_story(base_path: str, start_block_name: str, blocks: list[StoryBlockGraphicsItem]):
    meta_path = join(base_path, "meta")
    content_path = join(base_path, "content")

    if not exists(meta_path):
        mkdir(meta_path)
    if not exists(content_path):
        mkdir(content_path)

    list_of_block_names = []
    for block in blocks:
        content = {
            "x": block.x(),
            "y": block.y(),
        }
        with open(join(meta_path, f"{block.name}.json"), "w") as f:
            dump(content, f, indent=4)

        with open(join(content_path, f"{block.name}.txt"), "w") as f:
            f.write(block.body)

        list_of_block_names.append(block.name)

    with open(join(base_path, f"main.json"), "w") as f:
        dump({"blocks": list_of_block_names, "start": start_block_name}, f, indent=4)


def load_story(base_path: str):
    # Load the list of block names
    metadata: dict
    with open(join(base_path, "main.json")) as f:
        metadata = load(f)

    list_of_block_names: list[str] = metadata.get("blocks", [])

    blocks: list[dict] = []
    for block_name in list_of_block_names:
        # Find this block's metadata file
        block_metadata: dict
        with open(join(base_path, "meta", f"{block_name}.json")) as f:
            block_metadata = load(f)

        block_body: str
        with open(join(base_path, "content", f"{block_name}.txt")) as f:
            block_body = f.read()

        blocks.append(
            {
                "x": block_metadata.get("x", None),
                "y": block_metadata.get("y", None),
                "name": block_name,
                "body": block_body,
            }
        )

    return {"blocks": blocks, "start": metadata.get("start", None)}
