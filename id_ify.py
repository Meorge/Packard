def id_ify(title: str) -> str:
    """
    Takes a title and makes it all lowercase, then replaces spaces with
    hyphens to make it more URL-friendly.
    """
    return '-'.join([t.lower() for t in title.split()])