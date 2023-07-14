from story_document_block import StoryDocumentBlock
from json import dump, load
from os.path import join, exists
from os import mkdir


def save_story(base_path: str, start_block_name: str, blocks: list[StoryDocumentBlock]):
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
