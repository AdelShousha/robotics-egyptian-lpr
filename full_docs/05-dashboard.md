# Dashboard

## Overview

The monitoring dashboard is a React-based web application that displays real-time license plate detection results. It features a dark cyberpunk-themed design optimized for continuous monitoring scenarios.

![Dashboard Screenshot](./images/dashboard-full-screenshot.png)
*Caption: Full dashboard view showing detection cards and header statistics*

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Build tool and dev server |
| **Tailwind CSS** | Utility-first styling |
| **Radix UI** | Headless component primitives |
| **Lucide React** | Icon library |

---

## Design System

### Color Palette

The dashboard uses a dark theme with cyan accents:

| Variable | Hex Code | Usage |
|----------|----------|-------|
| `--bg-primary` | #121212 | Main background |
| `--bg-secondary` | #1e1e1e | Secondary areas |
| `--bg-card` | #242424 | Card backgrounds |
| `--accent-cyan` | #00FFFF | Primary accent |
| `--accent-green` | #00FF41 | Status indicators |
| `--text-primary` | #e0e0e0 | Main text |
| `--text-secondary` | #a0a0a0 | Secondary text |
| `--border-color` | #333333 | Borders |

![Color Palette](./images/dashboard-color-palette.png)
*Caption: Dashboard color scheme visualization*

### Typography

- **Body Font**: Inter (system fallback)
- **License Plate**: Roboto Mono (monospace for authentic plate rendering)
- **Character Spacing**: 0.1em on plate numbers

---

## Layout Structure

### Header Section

![Dashboard Header](./images/dashboard-header.png)
*Caption: Dashboard header with live status and statistics*

The sticky header contains:

1. **Title**: "Egyptian Plate Recognition"
2. **Live Status Indicator**: Pulsing green dot with "Live Monitor - Active"
3. **Today's Count**: Number of vehicles detected today
4. **Last Detection**: Relative time since last detection (e.g., "5m ago")

### Detection Grid

The main content area displays detection cards in a responsive grid:

| Breakpoint | Columns |
|------------|---------|
| Mobile | 1 column |
| Small (sm) | 2 columns |
| Large (lg) | 3 columns |
| Extra Large (xl) | 4 columns |

---

## Components

### Detection Card

Each detected vehicle is displayed in a card containing:

![Detection Card](./images/detection-card-anatomy.png)
*Caption: Anatomy of a detection card showing all elements*

1. **Vehicle Image**: Full captured image (16:9 aspect ratio)
2. **Plate Thumbnail**: Small cropped plate image
3. **Plate Number**: Arabic text in white box with monospace font
4. **Timestamp**: Detection time (HH:MM:SS format)
5. **Confidence Badge**:
   - Green checkmark + green text if ≥90%
   - Orange text if <90%

### Card Interaction

- **Hover Effect**: Border transitions from #333 to cyan (#00FFFF)
- **Image Fallback**: SVG placeholder if image fails to load

---

## Real-Time Updates

### Auto-Refresh Mechanism

The dashboard automatically fetches new data from the API:

- **Interval**: Every 30 seconds
- **Endpoint**: `GET /api/dashboard`
- **Behavior**: Seamlessly updates without page reload

### Relative Time Display

Timestamps are displayed as human-readable relative times:

| Time Elapsed | Display |
|--------------|---------|
| < 1 minute | "Just now" |
| 1-59 minutes | "Xm ago" |
| 1-23 hours | "Xh ago" |
| 1+ days | "Xd ago" |

---

## Data Flow

```
┌─────────────────────────────┐
│      Dashboard (React)       │
└──────────────┬──────────────┘
               │
               │ GET /api/dashboard
               │ (every 30 seconds)
               ▼
┌─────────────────────────────┐
│      FastAPI Backend         │
└──────────────┬──────────────┘
               │
               │ Query
               ▼
┌─────────────────────────────┐
│    PostgreSQL Database       │
└──────────────┬──────────────┘
               │
               │ Response
               ▼
┌─────────────────────────────┐
│   Dashboard State Update     │
│   - vehicles_today           │
│   - last_detection           │
│   - detections[]             │
└─────────────────────────────┘
```

---

## State Management

### Dashboard Data Interface

```typescript
interface Detection {
  id: number;
  car_image: string;      // Cloudinary URL
  lp_image: string;       // Cloudinary URL
  lp_number: string;      // Arabic plate text
  confidence: number;     // 0-1 decimal
  created_at: string;     // ISO timestamp
}

interface DashboardData {
  vehicles_today: number;
  last_detection: string | null;
  detections: Detection[];
}
```

### Application States

| State | Display |
|-------|---------|
| **Loading** | "Loading detections..." spinner |
| **Empty** | "No detections yet. Waiting for vehicles..." |
| **Error** | Error message with retry button |
| **Active** | Grid of detection cards |

---

## Responsive Design

![Responsive Views](./images/dashboard-responsive.png)
*Caption: Dashboard appearance across different screen sizes*

### Mobile Optimizations

- Single-column card layout
- Reduced padding and margins
- Touch-friendly tap targets
- Optimized image loading

### Desktop Features

- Multi-column grid layout
- Hover interactions
- Maximum container width (1800px)

---

## UI Components Library

The dashboard utilizes shadcn/ui components built on Radix UI:

| Component | Usage |
|-----------|-------|
| Cards | Detection result containers |
| Buttons | Retry action |
| Icons | Checkmark, status indicators |
| Skeleton | Loading placeholders |

---

## Performance Considerations

- **Image Optimization**: Images served via Cloudinary CDN
- **Lazy Loading**: Images load as they enter viewport
- **Error Boundaries**: Graceful fallbacks for failed image loads
- **Efficient Re-renders**: React state updates only changed elements
