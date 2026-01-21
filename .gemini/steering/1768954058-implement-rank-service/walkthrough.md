# Walkthrough - RankService Implementation

I have implemented the generic `RankService` to manage user drawing skill ranks.

## Changes

### 1. Model Definition (`packages/agent/src/models/rank.py`)
Defined `Rank` enum, `UserRank`, and `RankHistory` models.
- **Ranks**: Bronze (0-30), Silver (31-50), Gold (51-70), Platinum (71-85), Diamond (86-100)

### 2. Service Implementation (`packages/agent/src/services/rank_service.py`)
Implemented `RankService` with the following features:
- **`determine_rank`**: Maps a score to a `Rank`.
- **`update_user_rank`**: Updates the user's rank in Firestore based on the latest score.
    - Updates `users/{user_id}` with `rank` and `latest_score`.
    - Creates a new document in `users/{user_id}/rank_history` if the rank changes or it's the first update.

### 3. API Integration (`packages/agent/src/api/reviews.py`)
Integrated `RankService` into the `process_review_task` background task.
- After a successful drawing analysis, the user's rank is automatically updated.
- **API Integration**: Refactored `process_review_task` to accept `user_id` directly, improving efficiency by removing redundant database lookups.

## Verification Results

### Automated Tests
Ran unit tests for `RankService` using `pytest`.
All 6 tests passed.

```bash
packages/agent/tests/test_rank_service.py ......                                    [100%]
```

- Verified boundary conditions for score-to-rank mapping.
- Verified rank update logic (promotion, no change).
- Verified history creation logic.
