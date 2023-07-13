from story_document_block import StoryDocumentBlock
from json import dump, load
from os.path import join


def save_story(blocks: list[StoryDocumentBlock]):
    list_of_block_names = []
    for block in blocks:
        content = {
            "x": block.x(),
            "y": block.y(),
        }
        with open(join("story", "meta", f"{block.name}.json"), "w") as f:
            dump(content, f, indent=4)

        with open(join("story", "content", f"{block.name}.txt"), "w") as f:
            f.write(block.body)

        list_of_block_names.append(block.name)

    with open(join("story", f"content.json"), "w") as f:
        dump({"blocks": list_of_block_names}, f, indent=4)


def load_story(root: str):
    # Load the list of block names
    metadata: dict
    with open(join(root, "main.json")) as f:
        metadata = load(f)

    list_of_block_names: list[str] = metadata.get("blocks", [])

    blocks: list[dict] = []
    for block_name in list_of_block_names:
        # Find this block's metadata file
        block_metadata: dict
        with open(join(root, "meta", f"{block_name}.json")) as f:
            block_metadata = load(f)

        block_body: str
        with open(join(root, "content", f"{block_name}.txt")) as f:
            block_body = f.read()

        blocks.append(
            {
                "x": block_metadata.get("x", None),
                "y": block_metadata.get("y", None),
                "name": block_name,
                "body": block_body,
            }
        )

    return blocks
