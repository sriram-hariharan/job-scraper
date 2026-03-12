from dataclasses import dataclass
from typing import Optional

@dataclass
class Description:
    job_id: str
    html: Optional[str]
    text: Optional[str]