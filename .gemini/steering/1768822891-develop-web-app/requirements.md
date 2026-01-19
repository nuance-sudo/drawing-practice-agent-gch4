# Web App Development Requirements

## Overview
Develop the web application for the Drawing Practice Agent. The app will allow users to upload drawing images, view feedback, and manage their tasks.

## User Stories
### US-001: Submit Drawing and Receive Feedback
- [ ] User can upload a drawing image via the web app.
- [ ] Review starts immediately after upload.
- [ ] User can view specific feedback (proportion, shading, line quality).

### US-004: Check Review Status
- [ ] User can check the status of the review in a task list.
- [ ] Status updates via polling.

## Functional Requirements
### FR-001: Web App
- Framework: Next.js 16.x (App Router)
- Language: TypeScript 5.x
- Styling: Tailwind CSS 4.x
- State Management: Zustand 5.x
- Data Fetching: SWR 2.x
- Hosting: Vercel (locally simulate for dev)

## Constraints
- Must use the specified tech stack.
- Follow the directory structure defined in `functional-design.md`.
