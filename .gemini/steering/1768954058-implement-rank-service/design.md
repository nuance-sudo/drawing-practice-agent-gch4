# RankService Design

## Architecture
`RankService` will be a standalone service in `packages/agent/src/services/`.
It will be used by `TaskService` or directly called in the background task processing in `reviews.py`.

## Data Models (`packages/agent/src/models/rank.py`)

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class Rank(str, Enum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    DIAMOND = "Diamond"

class RankRange(BaseModel):
    rank: Rank
    min_score: int
    max_score: int

RANK_RANGES = [
    RankRange(rank=Rank.BRONZE, min_score=0, max_score=30),
    RankRange(rank=Rank.SILVER, min_score=31, max_score=50),
    RankRange(rank=Rank.GOLD, min_score=51, max_score=70),
    RankRange(rank=Rank.PLATINUM, min_score=71, max_score=85),
    RankRange(rank=Rank.DIAMOND, min_score=86, max_score=100),
]

class UserRank(BaseModel):
    user_id: str
    current_rank: Rank
    current_score: float
    updated_at: datetime

class RankHistory(BaseModel):
    user_id: str
    old_rank: Rank | None
    new_rank: Rank
    score: float
    changed_at: datetime
    task_id: str # Link to the task that caused the change
```

## Service (`packages/agent/src/services/rank_service.py`)

Methods:
-   `determine_rank(score: float) -> Rank`: Helper to map score to rank.
-   `update_user_rank(user_id: str, score: float, task_id: str) -> UserRank`:
    1.  Get current user rank (from Firestore `users/{user_id}/rank/current` or similar).
    2.  Calculate new rank based on new score.
    3.  If rank changes or it's the first time:
        -   Save new rank to `users/{user_id}` (or `users/{user_id}/rank/current`).
        -   Add entry to `users/{user_id}/rank_history`.
    4.  Return new UserRank.

## Firestore Structure
-   `users/{user_id}`:
    -   `rank`: String (current rank)
    -   `latest_score`: Number
-   `users/{user_id}/rank_history/{history_id}`:
    -   fields from `RankHistory`

## Integration
In `packages/agent/src/api/reviews.py`:
Inside `process_review_task`:
```python
# ... after analysis ...
rank_service = get_rank_service()
rank_service.update_user_rank(user_id, analysis.overall_score, task_id)
# ...
```
