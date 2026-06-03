# Team Creation Feature - Design Showcase

## 🎨 Visual Design Language

### Premium F1 Racing Aesthetic
The team creation interface embodies the precision and speed of Formula 1:

**Color Palette:**
- **Primary Blue** (`hsl(221.2, 83.2%, 53.3%)`) - Selection states, focus rings, icons
- **Racing Green** (`hsl(142, 76%, 36%)`) - Success, under budget, completion
- **Boost Yellow** (`hsl(38, 92%, 50%)`) - DRS Boost power-up, warnings
- **Alert Red** (`hsl(0, 84%, 60%)`) - Over budget, errors, danger states
- **Neutral Grays** - Muted backgrounds, secondary text, borders

### Typography Hierarchy

```
Page Title (Create New Team)
  ↓ text-3xl font-bold tracking-tight
Section Headings (Select Drivers, Budget)
  ↓ text-lg font-semibold with icons
Budget Numbers (Large, prominent)
  ↓ text-2xl font-bold tabular-nums
Selection Count Badges
  ↓ text-base px-3 py-1
Body Text
  ↓ text-base font-normal
Helper Text / Metadata
  ↓ text-sm text-muted-foreground
```

## 🎬 Animation Choreography

### Entry Animations (Page Load)
```
Page fade-in → 500ms
  ↓
Team name card appears
  ↓
Budget sidebar slides in (sticky position)
  ↓
Driver selector fades in
  ↓
Constructor selector fades in
```

### Interaction Animations

**1. Selection Micro-interactions**
- Hover: `scale(1.01)` + border color change (200ms)
- Click: Instant selection with scale to `1.02`
- Checkbox: Checkmark appears with 150ms transition
- Background tint: Primary color at 5% opacity

**2. Budget Bar Animation**
- Width transition: 300ms ease-out
- Color transition: 300ms (green → amber → red)
- Number counting: Instant (no animation on digits)

**3. Completion States**
- Green ring appears on cards: 300ms fade-in
- Checkmark icon: Instant appearance
- Success message: Fade-in from top (200ms)

**4. DRS Boost Selection**
- Selected item: Yellow background + pulse animation
- Yellow lightning bolt: Fill animation + continuous pulse

## 📐 Layout Architecture

### Desktop Layout (≥1024px)

```
┌─────────────────────────────────────────────────────┐
│  ← Back    Create New Team                          │
│            Select drivers and constructors...       │
├─────────────┬───────────────────────────────────────┤
│  Sidebar   │         Main Selection Area           │
│  (sticky)  │                                        │
│            │  ┌──────────────────────────────────┐ │
│  ┌──────┐  │  │  Select Drivers          3 / 5  │ │
│  │Budget│  │  │  ─────────────────────────────  │ │
│  │ 72.3M│  │  │  Search...  [Teams filter]      │ │
│  │──────│  │  │  ☐ Driver 1    12.5M           │ │
│  │ ████ │  │  │  ☑ Driver 2    15.0M ←Selected │ │
│  └──────┘  │  │  ...                            │ │
│            │  └──────────────────────────────────┘ │
│  ┌──────┐  │                                        │
│  │ DRS  │  │  ┌──────────────────────────────────┐ │
│  │Boost │  │  │  Select Constructors     2 / 2  │ │
│  │ ⚡   │  │  │  ─────────────────────────────  │ │
│  └──────┘  │  │  ☑ Constructor 1    18.0M      │ │
│            │  │  ☑ Constructor 2    14.3M      │ │
│            │  └──────────────────────────────────┘ │
└─────────────┴───────────────────────────────────────┘
│  [Cancel]  [Create Team ✓]    ✓ Ready to create   │
└─────────────────────────────────────────────────────┘
```

### Mobile Layout (<1024px)

```
┌──────────────────────┐
│ ← Back   Create Team │
├──────────────────────┤
│  Team Name Input     │
│  ─────────────────── │
├──────────────────────┤
│  ┌────────────────┐  │
│  │ Budget: 72.3M  │  │
│  │ ──────████──── │  │
│  └────────────────┘  │
├──────────────────────┤
│  ┌────────────────┐  │
│  │ Select Drivers │  │
│  │ 3 / 5 selected │  │
│  │ Search...      │  │
│  │ [Team filters] │  │
│  │ ☐ Driver 1     │  │
│  │ ☑ Driver 2     │  │
│  └────────────────┘  │
├──────────────────────┤
│  ┌────────────────┐  │
│  │ Constructors   │  │
│  │ 2 / 2 selected │  │
│  └────────────────┘  │
├──────────────────────┤
│  ┌────────────────┐  │
│  │ DRS Boost ⚡   │  │
│  │ ○ Driver 2     │  │
│  │ ○ Driver 3     │  │
│  └────────────────┘  │
├──────────────────────┤
│ [Cancel] [Create ✓] │
└──────────────────────┘
```

## 🎯 Visual States

### 1. Budget Display States

**Under Budget (< 90%)**
- Text: Green (`text-green-600`)
- Bar: Green fill
- Message: None or "Budget optimized"

**Near Budget (90-100%)**
- Text: Amber (`text-amber-600`)
- Bar: Amber fill
- Message: "Almost at budget cap"

**Over Budget (> 100%)**
- Text: Red (`text-red-600`)
- Bar: Red fill (capped at 100% width)
- Message: "Over budget by X.XM"
- Icon: Animated pulse alert circle

### 2. Selection States

**Unselected**
```css
border: 2px solid var(--border)
background: transparent
hover: bg-muted + scale(1.01)
```

**Selected**
```css
border: 2px solid var(--primary)
background: primary/5
shadow: subtle
scale: 1.02
✓ Checkbox checked
```

**Disabled (Max reached)**
```css
opacity: 0.5
cursor: not-allowed
no hover effects
```

### 3. Completion Indicators

**Incomplete Section**
- Badge: Secondary variant
- Card: Normal border
- Helper text: "Select X more..."

**Complete Section**
- Badge: Primary variant
- Card: Green ring (2px)
- Helper text: Green background "✓ Complete"

## 🔍 Attention to Detail

### Micro-interactions

1. **Search Input**
   - Focus ring: 2px primary blue
   - Clear button: Appears on input
   - Icon: Subtle gray, positioned left

2. **Team Filter Pills**
   - Active: Primary background
   - Inactive: Outline style
   - Hover: Slight scale up (1.05)
   - Click: Instant state change

3. **Selection Buttons**
   - Press: Minimal scale down (0.98)
   - Release: Spring to selected state
   - Focus: Prominent ring
   - Disabled: Faded with tooltip hint

4. **DRS Boost Radio**
   - Selected: Yellow background
   - Icon: Pulsing lightning bolt
   - Border: Yellow accent
   - Scale: 1.02 on selection

### Typography Details

- **Tabular nums** on all price displays
- **Font weights**: Normal (400), Medium (500), Semibold (600), Bold (700)
- **Line heights**: Tight on headings, comfortable on body text
- **Letter spacing**: Tight tracking on headings (`tracking-tight`)

### Spacing Rhythm

Using 8px base scale:
- xs: 8px (icon gaps)
- sm: 12px (compact spacing)
- md: 16px (card padding)
- lg: 24px (section gaps)
- xl: 32px (major sections)

### Color Usage Philosophy

**Primary Blue**: Trust, action, selection
**Green**: Success, validation, safe state
**Yellow**: Power, boost, special action
**Red**: Alert, danger, over limit
**Gray**: Neutral, secondary, disabled

## 🏁 User Journey Flow

### Step-by-Step Experience

**1. Land on Page**
- Fade-in animation (500ms)
- Team name input auto-focused
- Clear heading and description

**2. Enter Team Name**
- Input expands slightly on focus
- Helper text guides user
- Validation: Max 50 characters

**3. See Budget**
- Sidebar appears (desktop)
- Empty state: "Select players to see budget"
- Real-time updates as selections made

**4. Select Drivers**
- Search immediately available
- Team filters for quick navigation
- Visual feedback on each selection
- Counter updates: "3 / 5"
- Disabled state when 5 selected

**5. Select Constructors**
- Similar UI to drivers (consistency)
- Simpler (no search needed)
- Quick selection of 2 teams

**6. Assign DRS Boost**
- Progressive disclosure: appears after drivers
- Radio selection from 5 drivers
- Yellow accent makes it feel special
- Pulsing animation on selection

**7. Review & Submit**
- Validation summary at top
- Submit button state indicates readiness
- Progress indicator: "✓ Ready to create"
- Click → Loading spinner → Toast → Redirect

## 🎪 Special Effects

### Hover States
- Cards: Subtle lift (-2px) + shadow
- Buttons: Scale (1.05) + brightness
- Pills: Scale (1.05) + shadow

### Focus States
- 2px ring with offset
- Primary blue color
- Matches brand identity

### Loading States
- Spinner with message
- Button disabled with opacity
- Contextual loading text

### Success States
- Toast notification slides in
- Green checkmark icon
- Smooth redirect after 1s delay

## 🚀 Performance Considerations

- **CSS Transitions** over JavaScript animations
- **Will-change** property avoided (let browser optimize)
- **Transform** and **opacity** for animations (GPU-accelerated)
- **Debounced search** (not implemented, but recommended)
- **Lazy loading** for large driver lists (future enhancement)

---

## 🎨 Design Principles Applied

1. **Simplicity Through Hierarchy** - Most important elements are largest/boldest
2. **Progressive Disclosure** - Show what's needed when it's needed
3. **Real-time Feedback** - Every action has immediate visual response
4. **Error Prevention** - Disable invalid options before user clicks
5. **Consistency** - Same patterns repeated across components
6. **Purposeful Motion** - Every animation serves a function
7. **Premium Feel** - Attention to spacing, typography, and polish

---

**Result**: A form that feels inevitable, not overwhelming. Fast, precise, and race-ready. 🏎️
