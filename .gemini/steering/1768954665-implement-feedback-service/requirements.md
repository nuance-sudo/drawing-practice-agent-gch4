# FeedbackService Implementation Requirements

## Overview
Implement a service to generate structured feedback for users based on drawing analysis and their skill rank.

## Functional Requirements
1.  **Structured Feedback Generation**:
    -   Generate detailed feedback from `DessinAnalysis` results.
    -   Include specific advice based on the 4 evaluation criteria (Proportion, Tone, Texture, Line Quality).
2.  **Rank-Adaptive Feedback**:
    -   Adjust feedback tone and content complexity based on User Rank.
    -   **Bronze/Silver**: Focus on basics, encouraging tone, simple terms.
    -   **Gold**: More technical, focus on observation and structure.
    -   **Platinum/Diamond**: High-level advice, strict evaluation, professional nuances.
3.  **Markdown Generation**:
    -   Format the detailed feedback as Markdown.
4.  **Integration**:
    -   Called after analysis and rank update in `process_review_task`.
    -   Store the generated feedback structure (summary + detailed markdown) in Firestore.

## Data Models
-   `FeedbackResponse`: Already defined in `src/models/feedback.py`.
    -   `analysis`: `DessinAnalysis`
    -   `summary`: `str`
    -   `detailed_feedback`: `str` (Markdown)

## Constraints
-   Use `DessinAnalysis` results from `analysis.py`.
-   Use `UserRank` from `RankService`.
-   Must not re-call Gemini API for text generation if possible (to save tokens/latency), OR use a lightweight call if needed for Markdown generation.
    -   *Decision*: `analysis.py` already gets structured data. Generating Markdown from that structured data using templates or simple logic is faster and cheaper than another LLM call. However, "Rank-Adaptive" implies nuance.
    -   *Approach*: Use the LLM (Gemini) to generate the *text* of the feedback during the analysis phase or a separate phase?
    -   Current `analysis.py` prompt (`DESSIN_ANALYSIS_SYSTEM_PROMPT`) likely returns JSON.
    -   To get "Detailed Markdown Feedback" adapted to rank, we have two options:
        1.  Client-side generation (Python): Use templates based on the scores/strings in `DessinAnalysis`.
        2.  Server-side generation (LLM): Ask Gemini to generate the markdown feedback *considering the user's rank*.
    -   Option 2 is more "Agentic" and flexible.
    -   *Refinement*: We should probably update `analyze_dessin_image` to accept `user_rank` context, OR create `FeedbackService` that might call LLM again (or be part of the initial call).
    -   *Simplest Path*: The `DessinAnalysis` object has `strengths` and `improvements`. `FeedbackService` can generate the Markdown string by combining these with rank-specific templates or headers.
    -   *Better Path*: Passes `rank` to `analyze_dessin_image` and have the prompt handle it? -> `analyze_dessin_image` is in `tools/analysis.py`.
    -   Let's decouple. `FeedbackService.generate_feedback(analysis: DessinAnalysis, rank: Rank) -> FeedbackResponse`.
    -   For V1, we can implement rule-based Markdown generation to avoid double billing/latency. We can iterate to LLM-based later if needed.

## Dependencies
-   `RankService`
