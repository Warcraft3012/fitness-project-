import datetime

class User:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.completed_challenges = set()
        self.viewed_calendar = set()
        self.earned_badges = set()
        self.messages = []

class Message:
    def __init__(self, content, author_id, categories, timestamp=None, replies=None):
        self.content = content
        self.timestamp = timestamp if timestamp else datetime.datetime.now().isoformat(timespec="seconds")
        self.author_id = author_id
        self.categories = set(categories)
        # replies is a list of dicts: [{"content": ..., "author_id": ..., "timestamp": ...}, ...]
        self.replies = replies if replies is not None else []

    def to_dict(self):
        # For JSON serialization
        return {
            "content": self.content,
            "timestamp": self.timestamp,
            "author_id": self.author_id,
            "categories": list(self.categories),
            "replies": self.replies
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            content=data.get("content", ""),
            author_id=data.get("author_id", ""),
            categories=data.get("categories", []),
            timestamp=data.get("timestamp"),
            replies=data.get("replies", [])
        )

class Challenge:
    def __init__(self, title, description, difficulty, equipment_tags):
        self.title = title
        self.description = description
        self.difficulty = difficulty
        self.equipment_tags = set(equipment_tags.split(";")) if equipment_tags else set()

class Badge:
    def __init__(self, name, description, requirements, category):
        self.name = name
        self.description = description
        self.requirements = set(requirements)
        self.category = category


