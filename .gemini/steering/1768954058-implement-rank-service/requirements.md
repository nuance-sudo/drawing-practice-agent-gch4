# RankService Implementation Requirements

## Overview
Implement a service to manage user drawing skill ranks based on drawing scores.

## Functional Requirements
1.  **Rank Definition**:
    -   Store rank definitions (Bronze, Silver, Gold, Platinum, Diamond) and their score ranges.
2.  **Rank Calculation**:
    -   Calculate rank based on the latest drawing score (or an average/weighted average if deemed appropriate, but simplest first: latest score).
    -   Issue description says "based on drawing score".
3.  **Rank Update**:
    -   Update user's rank when a new drawing analysis is completed.
    -   Support promotion and demotion.
4.  **History Tracking**:
    -   Save rank history to Firestore.

## Data Models
-   `Rank`: Enum or specific class for rank levels.
-   `UserRank`: Current rank of a user.
-   `RankHistory`: History of rank changes.

## Constraints
-   Must integrate with Firestore.
-   Must be called from `process_review_task`.
