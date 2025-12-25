from datetime import datetime
from typing import Dict

posts_db: Dict[int, "Post"] = {}
next_post_id = 1


class Post:
    def __init__(self, author_id: int, title: str, content: str):
        global next_post_id

        self.id = next_post_id
        self.author_id = author_id
        self.title = title
        self.content = content
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        next_post_id += 1
