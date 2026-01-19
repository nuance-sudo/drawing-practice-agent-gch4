# Web App Implementation Design

## Tech Stack
- **Framework**: Next.js 16.x (App Router)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **State Management**: Zustand 5.x
- **Data Fetching**: SWR 2.x
- **Auth**: Auth.js 5.x (GitHub OAuth) - *Will implement basic structure first*

## Directory Structure
```
packages/web/
├── app/
│   ├── page.tsx                # Home (Login/Landing)
│   ├── layout.tsx              # Root Layout
│   ├── (authenticated)/        # Authenticated routes
│   │   ├── dashboard/          # Main dashboard
│   │   │   └── page.tsx
│   │   └── layout.tsx
├── components/
│   ├── ui/                     # Basic UI components (Button, Card, etc.)
│   ├── features/               # Feature-specific components
│       ├── ImageUpload.tsx
│       └── TaskList.tsx
├── stores/
│   └── taskStore.ts
├── lib/
│   └── api.ts
├── package.json
├── next.config.ts
└── tailwind.config.ts
```

## Implementation Steps
1. Initialize Next.js project in `packages/web`.
2. Configure Tailwind CSS.
3. specific directories (`components`, `stores`, `lib`).
4. Implement basic UI shell.
