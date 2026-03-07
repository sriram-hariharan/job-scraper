from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, List

@dataclass
class Job:
    company: str
    title: str
    location: Union[str, List[str]]
    url: str
    source: str
    posted_at: Optional[str] = None

    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):

        job = {
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "posted_at": self.posted_at
        }

        job.update(self.meta)

        return job