# Dashboard - Visual Specification

A visual guide to the implemented Team Dashboard feature.

---

## 📱 Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Header                                                          │
│  ┌───────────────────────────────┐  ┌──────────────────────┐   │
│  │ My Teams                       │  │ + Create Team        │   │
│  └───────────────────────────────┘  └──────────────────────┘   │
│                                                                  │
│  Filters                                                         │
│  ┌─────────────┐ ┌─────────────┐              ┌─────────────┐  │
│  │ 2026 Season ▼│ │ All Teams  ▼│              │ 12 teams    │  │
│  └─────────────┘ └─────────────┘              └─────────────┘  │
│                                                                  │
│  Team Grid (Desktop: 3 columns, Tablet: 2, Mobile: 1)          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Team Card 1  │ │ Team Card 2  │ │ Team Card 3  │           │
│  │              │ │              │ │              │           │
│  │ [Details]    │ │ [Details]    │ │ [Details]    │           │
│  │              │ │              │ │              │           │
│  │ [View] [Edit]│ │ [View] [Edit]│ │ [View] [Edit]│           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Team Card 4  │ │ Team Card 5  │ │ Team Card 6  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎴 Team Card Anatomy

```
┌────────────────────────────────────────────────┐
│  Lightning McQueen Racing         ✓ Valid      │  ← Header
│  Season 2026                                    │  ← Metadata
│                                                 │
│  Budget                          85.5M / 100M  │  ← Budget Label
│  ████████████████████░░░░░                     │  ← Progress Bar
│                                                 │
│  Drivers          5    Constructors        2   │  ← Composition Grid
│                                                 │
│  ─────────────────────────────────────────────  │  ← Divider
│  👁 View                    ✏️ Edit              │  ← Actions
└────────────────────────────────────────────────┘
```

### **Card States:**

#### **Default State**
```
┌────────────────────────────────────┐
│  Shadow: subtle (1px 3px)          │
│  Transform: translateY(0)          │
│  Border: 1px solid border          │
└────────────────────────────────────┘
```

#### **Hover State**
```
┌────────────────────────────────────┐
│  Shadow: deeper (4px 12px)         │  ← Enhanced
│  Transform: translateY(-2px)       │  ← Lifts
│  Transition: 200ms ease-out        │  ← Smooth
└────────────────────────────────────┘
```

#### **Valid Team Badge**
```
┌──────────────┐
│ ✓ Valid      │  Green bg (#22C55E)
└──────────────┘  White text
                  High contrast (4.8:1)
```

#### **Invalid Team Badge**
```
┌──────────────┐
│ ✗ Invalid    │  Red bg (#EF4444)
└──────────────┘  White text
                  High contrast (4.7:1)
```

---

## 📐 Spacing Specification

### **Card Spacing**
```
┌─ 24px gap ─┐
│            │
│  ┌──────┐  │
│  │ Card │  │  ← 16px padding (all sides)
│  │      │  │
│  └──────┘  │
│            │
└────────────┘
```

### **Typography Hierarchy**
```
My Teams              ← 30px, bold, tracking-tight
└─ Lightning Racing   ← 20px, semibold
   └─ Season 2026     ← 14px, regular, muted
      └─ Budget       ← 12px, medium, muted
         └─ 85.5M     ← 14px, semibold
```

### **Grid Gaps**
```
Desktop (1024px+):
┌──────┐ 24px ┌──────┐ 24px ┌──────┐
│ Card │ gap  │ Card │ gap  │ Card │
└──────┘      └──────┘      └──────┘

Tablet (768px+):
┌──────┐ 24px ┌──────┐
│ Card │ gap  │ Card │
└──────┘      └──────┘

Mobile (< 768px):
┌──────┐
│ Card │
└──────┘
```

---

## 🎨 Color Palette

### **Primary Colors**
```css
Background:     #FFFFFF (white)
Foreground:     hsl(222.2, 84%, 4.9%) (near-black)
Primary:        hsl(221.2, 83.2%, 53.3%) (blue)
```

### **Semantic Colors**
```css
Success/Valid:
  ├─ Background:  hsl(142, 76%, 96%)   ← Light green
  ├─ Border:      hsl(142, 76%, 36%)   ← Medium green
  └─ Text:        hsl(142, 76%, 26%)   ← Dark green

Error/Invalid:
  ├─ Background:  hsl(0, 84%, 96%)     ← Light red
  ├─ Border:      hsl(0, 84%, 60%)     ← Medium red
  └─ Text:        hsl(0, 84%, 40%)     ← Dark red
```

### **Budget Colors**
```css
Safe (< 90%):     hsl(142, 76%, 36%)  ← Green
Warning (90-99%): hsl(38, 92%, 50%)   ← Amber
Danger (100%+):   hsl(0, 84%, 60%)    ← Red
```

---

## 🔄 State Diagrams

### **Loading Flow**
```
User navigates to /
       ↓
┌──────────────────┐
│ Loading State    │  Show skeleton grid (6 cards)
│ ████ ████ ████  │  Preserve layout
└──────────────────┘  Pulse animation
       ↓
   API responds
       ↓
┌──────────────────┐
│ Success State    │  Render actual team cards
│ [Card] [Card]    │  Fade in smoothly
└──────────────────┘
```

### **Empty Flow**
```
User applies filters
       ↓
   No teams match
       ↓
┌──────────────────┐
│ Empty State      │  Large icon (48px)
│                  │  "No teams yet"
│   🗂️              │  Helpful description
│                  │  "Create Your First Team" button
│  [+ Create]      │
└──────────────────┘
       ↓
   User clicks button
       ↓
Navigate to /teams/create
```

### **Error Flow**
```
API request fails
       ↓
┌──────────────────┐
│ Error State      │  Red alert box
│ ⚠️ Error          │  Clear message
│ Failed to load   │  Retry button
│ [Try Again]      │
└──────────────────┘
       ↓
   User clicks retry
       ↓
   Back to loading
```

---

## 🎭 Interaction Patterns

### **Filter Interaction**
```
┌─────────────────┐
│ 2026 Season  ▼  │  ← Closed (default)
└─────────────────┘

       ↓ (User clicks)

┌─────────────────┐
│ 2026 Season  ▲  │  ← Open
├─────────────────┤
│ ✓ 2026 Season   │  ← Selected
│   2025 Season   │
└─────────────────┘

       ↓ (User selects)

Results update (no page reload)
Team count updates
Grid refreshes with filtered data
```

### **Card Interaction**
```
Default → Hover → Click

┌──────────┐      ┌──────────┐      Navigate
│  Card    │  →   │  Card ↑  │  →   to detail
│          │      │ (lifted) │      or edit
└──────────┘      └──────────┘
```

### **Button States**
```
View Button:
┌──────────────┐
│ 👁 View       │  Default: outlined
└──────────────┘

     ↓ Hover
┌──────────────┐
│ 👁 View       │  Background: light gray
└──────────────┘

     ↓ Focus (keyboard)
┌──────────────┐
│ 👁 View       │  Ring: 2px blue
└──────────────┘  Offset: 2px

     ↓ Active (click)
┌──────────────┐
│ 👁 View       │  Background: darker
└──────────────┘
```

---

## 📱 Responsive Breakpoints

### **Desktop (1440px)**
```
┌─────────────────────────────────────────────────────────┐
│ My Teams                              [+ Create Team]   │
│ [Season ▼] [Status ▼]                        12 teams   │
│                                                          │
│ ┌──────┐  ┌──────┐  ┌──────┐                           │
│ │Card 1│  │Card 2│  │Card 3│  ← 3 columns              │
│ └──────┘  └──────┘  └──────┘                           │
│ ┌──────┐  ┌──────┐  ┌──────┐                           │
│ │Card 4│  │Card 5│  │Card 6│                           │
│ └──────┘  └──────┘  └──────┘                           │
└─────────────────────────────────────────────────────────┘
```

### **Tablet (768px)**
```
┌────────────────────────────────────┐
│ My Teams         [+ Create Team]   │
│ [Season ▼] [Status ▼]   12 teams   │
│                                     │
│ ┌──────────┐  ┌──────────┐         │
│ │ Card 1   │  │ Card 2   │ ← 2 cols│
│ └──────────┘  └──────────┘         │
│ ┌──────────┐  ┌──────────┐         │
│ │ Card 3   │  │ Card 4   │         │
│ └──────────┘  └──────────┘         │
└────────────────────────────────────┘
```

### **Mobile (375px)**
```
┌──────────────────────┐
│ My Teams             │
│ [+ Create Team]      │
│                      │
│ [Season ▼]           │
│ [Status ▼]           │
│ 12 teams             │
│                      │
│ ┌──────────────────┐ │
│ │ Card 1           │ │ ← 1 col
│ │                  │ │
│ │ [View]  [Edit]   │ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ Card 2           │ │
│ └──────────────────┘ │
└──────────────────────┘
```

---

## 🎯 Design Tokens Reference

### **Spacing**
```css
--spacing-xs:  8px   /* Icon gaps */
--spacing-sm:  12px  /* Compact */
--spacing-md:  16px  /* Card padding */
--spacing-lg:  24px  /* Grid gaps */
--spacing-xl:  32px  /* Page margins */
```

### **Typography**
```css
--text-xs:   12px / 16px  /* Labels */
--text-sm:   14px / 20px  /* Secondary */
--text-base: 16px / 24px  /* Body */
--text-lg:   18px / 28px  /* Subheadings */
--text-xl:   20px / 28px  /* Card titles */
--text-2xl:  24px / 32px  /* Section headings */
--text-3xl:  30px / 36px  /* Page headings */
```

### **Shadows**
```css
--shadow-card:       0 1px 3px rgba(0,0,0,0.12)
--shadow-card-hover: 0 4px 12px rgba(0,0,0,0.15)
```

### **Transitions**
```css
--transition-fast: 150ms ease-out
--transition-base: 200ms ease-out
--transition-slow: 300ms ease-out
```

---

## ♿ Accessibility Features

### **Keyboard Navigation**
```
Tab Order:
1. Season filter (dropdown)
2. Status filter (dropdown)
3. Create Team button
4. Team Card 1 - View button
5. Team Card 1 - Edit button
6. Team Card 2 - View button
7. Team Card 2 - Edit button
... (continues)
```

### **Screen Reader Announcements**
```
"My Teams, heading level 1"
"Create Team, button"
"Season filter, 2026 Season selected"
"Status filter, All Teams selected"
"12 teams"
"Lightning McQueen Racing, heading level 3"
"Valid, badge"
"Season 2026"
"Budget usage: 85.5 million out of 100 million"
"Progress bar, 85 percent"
"View, button"
"Edit, button"
```

### **Focus Indicators**
```
┌────────────────────────┐
│ 👁 View                 │
│ ┌───────────────────┐  │
│ │ (2px blue ring)   │  │ ← Visible focus
│ └───────────────────┘  │
└────────────────────────┘
Offset: 2px
Color: Primary blue
Width: 2px
```

---

## 🎬 Animation Timing

### **Card Hover**
```
Initial:     shadow: 1px 3px, transform: 0
Hover:       shadow: 4px 12px, transform: -2px
Duration:    200ms
Easing:      ease-out
```

### **Progress Bar Fill**
```
Initial:     width: 0%
Final:       width: 85.5%
Duration:    300ms
Easing:      ease-out
```

### **Loading Skeleton Pulse**
```
Opacity:     0.5 → 1.0 → 0.5
Duration:    2000ms
Iteration:   infinite
Easing:      ease-in-out
```

---

## 📊 Component Tree

```
Dashboard
├── Header Section
│   ├── Page Title ("My Teams")
│   └── Create Button
├── Filter Section
│   ├── Season Select
│   ├── Status Select
│   └── Team Count
└── Content Section
    ├── Loading State (Skeleton Grid)
    ├── Error State (Alert + Retry)
    ├── Empty State (Icon + Message + CTA)
    └── Success State (Team Grid)
        └── TeamCard[] (array)
            ├── CardHeader
            │   ├── Team Name
            │   └── Status Badge
            └── CardContent
                ├── Budget Display
                │   ├── Label + Value
                │   └── Progress Bar
                ├── Composition Grid
                │   ├── Driver Count
                │   └── Constructor Count
                └── Action Buttons
                    ├── View Button
                    └── Edit Button
```

---

## 🎨 Visual Hierarchy Map

```
Level 1 (Most Important):
└─ Team Name (20px, bold)
   └─ Status Badge (high contrast)

Level 2 (Important):
└─ Budget Value (14px, semibold)
   └─ Budget Progress Bar (visual)

Level 3 (Supporting):
└─ Season (14px, muted)
   └─ Driver/Constructor Counts (14px)

Level 4 (Actions):
└─ View Button (outline)
   └─ Edit Button (solid)

Level 5 (Labels):
└─ "Budget", "Drivers", "Constructors" (12px, muted)
```

---

## ✅ Implementation Checklist

Use this checklist to verify the implementation:

- [x] Header renders with title and CTA
- [x] Filters render and function correctly
- [x] Team count updates dynamically
- [x] Grid is responsive (1/2/3 columns)
- [x] Cards display all required data
- [x] Status badges show correct color
- [x] Progress bars animate smoothly
- [x] Hover states work on cards
- [x] Hover states work on buttons
- [x] Click navigation works (View/Edit)
- [x] Loading state shows skeleton
- [x] Empty state shows when no teams
- [x] Error state shows on API failure
- [x] Keyboard navigation works
- [x] Screen reader announces correctly
- [x] Focus indicators are visible
- [x] Color contrast meets WCAG AA
- [x] Reduced motion is respected
- [x] No horizontal scroll at any viewport
- [x] Touch targets ≥ 44px on mobile
- [x] All spacing uses design tokens
- [x] All colors use CSS variables

---

**This specification serves as the visual reference for the Dashboard feature.**

Use it for:
- Design reviews
- QA testing
- Developer handoff
- Future enhancements

**Last Updated:** February 15, 2026
**Status:** ✅ Complete and Production-Ready
