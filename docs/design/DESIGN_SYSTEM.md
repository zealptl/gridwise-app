# GridWise Design System

**Version:** 1.0
**Last Updated:** February 2026
**Status:** Active

---

## Philosophy

GridWise is a premium fantasy Formula 1 application. Every detail matters. This design system ensures consistency, clarity, and a calm, confident user experience across all screens.

**Core Principles:**
- **Simplicity is architecture** — Remove until it breaks, then add back the last thing
- **Consistency is non-negotiable** — Same component looks identical everywhere
- **Hierarchy drives everything** — Most important = most prominent
- **Whitespace is a feature** — Breathing room feels premium
- **Responsive is the real design** — Mobile first, desktop enhances

---

## Color Tokens

### Brand Colors
```css
--primary: hsl(221.2, 83.2%, 53.3%)           /* Primary blue */
--primary-foreground: hsl(210, 40%, 98%)      /* Text on primary */

--secondary: hsl(210, 40%, 96.1%)             /* Secondary bg */
--secondary-foreground: hsl(222.2, 47.4%, 11.2%)

--accent: hsl(210, 40%, 96.1%)
--accent-foreground: hsl(222.2, 47.4%, 11.2%)
```

### Semantic Colors

#### Success (Valid Teams, Positive Actions)
```css
--success-bg: hsl(142, 76%, 96%)
--success-border: hsl(142, 76%, 36%)
--success-text: hsl(142, 76%, 26%)

--status-valid-bg: hsl(142, 76%, 96%)
--status-valid-border: hsl(142, 76%, 40%)
```

#### Error (Invalid Teams, Destructive Actions)
```css
--error-bg: hsl(0, 84%, 96%)
--error-border: hsl(0, 84%, 60%)
--error-text: hsl(0, 84%, 40%)

--destructive: hsl(0, 84%, 60.2%)
--destructive-foreground: hsl(210, 40%, 98%)

--status-invalid-bg: hsl(0, 84%, 96%)
--status-invalid-border: hsl(0, 84%, 60%)
```

#### Warning (Approaching Limits, Caution)
```css
--warning-info: hsl(199, 89%, 48%)            /* Blue - informational */
--warning-caution: hsl(38, 92%, 50%)          /* Amber - warning */
--warning-danger: hsl(0, 84%, 60%)            /* Red - critical */
```

### Budget Visualization
```css
--budget-safe: hsl(142, 76%, 36%)             /* Under budget (green) */
--budget-warning: hsl(38, 92%, 50%)           /* Near budget (amber) */
--budget-danger: hsl(0, 84%, 60%)             /* Over budget (red) */
```

### Transfer States
```css
--transfer-added: hsl(142, 76%, 40%)          /* Green - new selection */
--transfer-removed: hsl(0, 84%, 60%)          /* Red - removed selection */
--transfer-neutral: hsl(var(--muted))         /* Gray - unchanged */
```

### Rule Severity
```css
--severity-error-bg: hsl(0, 84%, 96%)
--severity-error-text: hsl(0, 84%, 40%)
--severity-error-border: hsl(0, 84%, 60%)

--severity-warning-bg: hsl(38, 92%, 96%)
--severity-warning-text: hsl(38, 92%, 40%)
--severity-warning-border: hsl(38, 92%, 60%)

--severity-info-bg: hsl(199, 89%, 96%)
--severity-info-text: hsl(199, 89%, 40%)
--severity-info-border: hsl(199, 89%, 60%)
```

### Neutral Colors
```css
--background: hsl(0, 0%, 100%)                /* Page background */
--foreground: hsl(222.2, 84%, 4.9%)           /* Primary text */

--card: hsl(0, 0%, 100%)                      /* Card background */
--card-foreground: hsl(222.2, 84%, 4.9%)

--muted: hsl(210, 40%, 96.1%)                 /* Subtle backgrounds */
--muted-foreground: hsl(215.4, 16.3%, 46.9%)  /* Secondary text */

--border: hsl(214.3, 31.8%, 91.4%)            /* Default borders */
--input: hsl(214.3, 31.8%, 91.4%)             /* Input borders */
--ring: hsl(221.2, 83.2%, 53.3%)              /* Focus rings */
```

### Admin-Specific
```css
--admin-header-bg: hsl(220, 14%, 96%)
--admin-border: hsl(220, 13%, 91%)
```

### State Colors
```css
--selected-bg: hsl(var(--primary) / 0.1)
--selected-border: hsl(var(--primary))
--disabled-opacity: 0.5
```

---

## Typography

### Font Family
```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

### Font Sizes & Line Heights

```css
/* Mobile-first sizing */
--text-xs: 12px / 16px                        /* Labels, metadata */
--text-sm: 14px / 20px                        /* Body, secondary info */
--text-base: 16px / 24px                      /* Base body text */
--text-lg: 18px / 28px                        /* Subheadings */
--text-xl: 20px / 28px                        /* Card titles */
--text-2xl: 24px / 32px                       /* Section headings */
--text-3xl: 30px / 36px                       /* Page headings */

/* Desktop enhancements (optional scale-up) */
@media (min-width: 1024px) {
  --text-3xl: 32px / 40px
}
```

### Font Weights
```css
--font-normal: 400                            /* Body text */
--font-medium: 500                            /* Emphasis, labels */
--font-semibold: 600                          /* Subheadings */
--font-bold: 700                              /* Headings, primary emphasis */
```

### Usage Guidelines
- **Page Titles:** text-3xl, font-bold, tracking-tight
- **Section Headings:** text-2xl, font-bold
- **Card Titles:** text-xl, font-semibold
- **Body Text:** text-base, font-normal
- **Secondary Info:** text-sm, text-muted-foreground
- **Metadata/Labels:** text-xs, text-muted-foreground, font-medium

---

## Spacing

### Scale (8px base)
```css
--spacing-xs: 8px                             /* Icon gaps, small internal spacing */
--spacing-sm: 12px                            /* Compact spacing */
--spacing-md: 16px                            /* Card padding, standard spacing */
--spacing-lg: 24px                            /* Card gaps, section spacing */
--spacing-xl: 32px                            /* Page margins, major sections */
--spacing-2xl: 48px                           /* Large section breaks */
```

### Form-Specific
```css
--form-section-gap: 32px                      /* Gap between major form sections */
--form-input-gap: 12px                        /* Gap between label and input */
--form-field-gap: 20px                        /* Gap between form fields */
```

### Timeline
```css
--timeline-dot-size: 12px
--timeline-line-width: 2px
--timeline-spacing: 24px
```

### Usage Guidelines
- **Card Internal Padding:** spacing-md (16px)
- **Grid Gaps:** spacing-lg (24px)
- **Page Margins:** spacing-xl (32px)
- **Section Breaks:** spacing-2xl (48px)
- **Icon-Text Gap:** spacing-xs (8px)
- **Button Internal Padding:** spacing-sm (12px) vertical, spacing-md (16px) horizontal

---

## Border Radius

```css
--radius: 0.5rem                              /* 8px - default */
--radius-sm: calc(var(--radius) - 4px)        /* 4px - small elements */
--radius-md: calc(var(--radius) - 2px)        /* 6px - medium elements */
--radius-lg: var(--radius)                    /* 8px - cards, buttons */
--radius-xl: 12px                             /* Large cards */
--radius-full: 9999px                         /* Circles, pills */
```

### Usage Guidelines
- **Cards:** radius-lg (8px)
- **Buttons:** radius-md (6px)
- **Inputs:** radius-md (6px)
- **Badges/Pills:** radius-full
- **Icons/Avatars:** radius-full
- **Small UI Elements:** radius-sm (4px)

---

## Shadows

```css
--shadow-card: 0 1px 3px rgba(0, 0, 0, 0.12)
--shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.15)
--shadow-dialog: 0 10px 40px rgba(0, 0, 0, 0.2)
```

### Usage Guidelines
- **Default Cards:** shadow-card
- **Hover State:** shadow-card-hover
- **Dialogs/Modals:** shadow-dialog
- **Sticky Elements:** shadow-card

---

## Transitions & Animations

### Durations
```css
--transition-fast: 150ms                      /* Micro-interactions */
--transition-base: 200ms                      /* Default transitions */
--transition-slow: 300ms                      /* Large movements */
```

### Easing
```css
--ease-out: cubic-bezier(0, 0, 0.2, 1)
--ease-in: cubic-bezier(0.4, 0, 1, 1)
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1)
--ease-bounce: cubic-bezier(0.16, 1, 0.3, 1)
```

### Specific Animations
```css
--slide-in: 300ms cubic-bezier(0.16, 1, 0.3, 1)
--fade-in: 200ms ease-out
--scale-in: 150ms cubic-bezier(0.16, 1, 0.3, 1)
```

### Usage Guidelines
- **Hover States:** transition-base (200ms), ease-out
- **Focus States:** transition-fast (150ms), ease-out
- **Modal Entry:** slide-in (300ms), ease-bounce
- **Toast/Alert Entry:** fade-in (200ms), ease-out
- **Budget Bar Fill:** transition-slow (300ms), ease-out

---

## Component Patterns

### Card
```css
border: 1px solid var(--border)
border-radius: var(--radius-lg)
padding: var(--spacing-md)
background: var(--card)
box-shadow: var(--shadow-card)
transition: box-shadow var(--transition-base)

/* Hover */
&:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}
```

### Button (Primary)
```css
background: var(--primary)
color: var(--primary-foreground)
padding: var(--spacing-sm) var(--spacing-md)
border-radius: var(--radius-md)
font-weight: var(--font-medium)
transition: all var(--transition-base)

/* Hover */
&:hover {
  opacity: 0.9;
}

/* Disabled */
&:disabled {
  opacity: var(--disabled-opacity);
  cursor: not-allowed;
}
```

### Badge (Status)
```css
padding: 4px 12px
border-radius: var(--radius-full)
font-size: var(--text-xs)
font-weight: var(--font-medium)

/* Valid */
&.valid {
  background: var(--success-bg);
  color: var(--success-text);
  border: 1px solid var(--success-border);
}

/* Invalid */
&.invalid {
  background: var(--error-bg);
  color: var(--error-text);
  border: 1px solid var(--error-border);
}
```

### Selection Item (Driver/Constructor)
```css
border: 2px solid var(--border)
border-radius: var(--radius-lg)
padding: var(--spacing-sm)
transition: all var(--transition-base)

/* Hover */
&:hover {
  background: var(--muted);
  border-color: var(--muted-foreground);
}

/* Selected */
&.selected {
  background: var(--selected-bg);
  border-color: var(--selected-border);
  box-shadow: 0 0 0 2px var(--selected-bg);
}

/* Disabled */
&:disabled {
  opacity: var(--disabled-opacity);
  cursor: not-allowed;
}
```

---

## Responsive Breakpoints

```css
/* Mobile First - Base styles are mobile */
--breakpoint-sm: 640px                        /* Tablet */
--breakpoint-md: 768px                        /* Small desktop */
--breakpoint-lg: 1024px                       /* Desktop */
--breakpoint-xl: 1280px                       /* Large desktop */
--breakpoint-2xl: 1536px                      /* Extra large */
```

### Grid Patterns

**Dashboard Grid:**
```css
/* Mobile: 1 column */
grid-template-columns: 1fr;

/* Tablet: 2 columns */
@media (min-width: 768px) {
  grid-template-columns: repeat(2, 1fr);
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
  grid-template-columns: repeat(3, 1fr);
}
```

**Form Layout (Team Creation/Edit):**
```css
/* Mobile: Stacked */
grid-template-columns: 1fr;

/* Desktop: Sidebar + Main */
@media (min-width: 1024px) {
  grid-template-columns: 1fr 3fr;
}
```

**Detail Page:**
```css
/* Mobile: Stacked */
grid-template-columns: 1fr;

/* Desktop: Main + Sidebar */
@media (min-width: 1024px) {
  grid-template-columns: 2fr 1fr;
}
```

---

## Sticky Positioning

```css
--sticky-top-mobile: 72px                     /* Below mobile header */
--sticky-top-desktop: 24px                    /* Desktop sticky offset */
```

### Usage
- **Budget Display (Desktop):** `position: sticky; top: var(--sticky-top-desktop);`
- **Transfer Counter (Desktop):** `position: sticky; top: var(--sticky-top-desktop);`
- **Mobile headers:** Adjust for fixed navigation

---

## Accessibility Standards

### Contrast Ratios (WCAG AA)
- **Normal Text:** 4.5:1 minimum
- **Large Text (18px+):** 3:1 minimum
- **UI Components:** 3:1 minimum

### Focus States
```css
/* Visible focus indicator */
outline: 2px solid var(--ring);
outline-offset: 2px;
border-radius: var(--radius-sm);
```

### Touch Targets
- **Minimum Size:** 44px × 44px (mobile)
- **Desktop:** 36px × 36px acceptable
- **Padding around small icons to meet target size**

### Screen Readers
- **Icons:** Use `aria-hidden="true"` for decorative icons
- **Actions:** Provide `aria-label` for icon-only buttons
- **Status:** Use `role="status"` for dynamic updates
- **Live regions:** Use `aria-live="polite"` for toasts/alerts

---

## Motion & Animation Guidelines

### When to Animate
✅ **Good uses:**
- Hover states (buttons, cards)
- Focus states (inputs, buttons)
- Modal entry/exit
- Toast notifications
- Loading states (skeleton, spinner)
- Budget bar filling
- Validation errors appearing

❌ **Avoid:**
- Gratuitous animations
- Auto-playing carousels
- Animations longer than 500ms
- Distracting motion in periphery

### Accessibility
- **Respect `prefers-reduced-motion`:**
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Icon System

### Library
**Lucide React** — Consistent, modern, open-source

### Standard Sizes
```css
--icon-xs: 12px                               /* Inline with small text */
--icon-sm: 16px                               /* Default, inline with text */
--icon-md: 20px                               /* Headings, emphasis */
--icon-lg: 24px                               /* Large actions */
--icon-xl: 48px                               /* Empty states, hero */
```

### Common Icons
- **CheckCircle:** Valid status, success
- **XCircle:** Invalid status, error
- **AlertCircle:** Warning, attention needed
- **Zap:** DRS Boost
- **Users:** Drivers
- **Building2:** Constructors
- **Wallet:** Budget
- **Calendar:** Transfer history, dates
- **TrendingDown:** Transfers
- **Shield:** Rules
- **PlusCircle:** Create action
- **Pencil:** Edit action
- **Trash2:** Delete action
- **Eye:** View action
- **ArrowLeft:** Back navigation
- **Save:** Save changes

---

## Loading States

### Skeleton Screens
- Preserve layout structure
- Use `bg-muted` for skeleton blocks
- Animate with `animate-pulse`
- Match actual content sizing

### Spinners
- Use for async operations
- Sizes: sm (16px), md (32px), lg (48px)
- Centered with message below (e.g., "Loading team...")

### Progress Bars
- For determinate progress (budget usage)
- Height: 8-12px
- Smooth transitions (300ms)
- Color changes based on state

---

## Empty States

### Structure
```typescript
<EmptyState
  icon={IconComponent}          // 48px icon
  title="Short title"           // text-xl, font-semibold
  description="Helpful text"    // text-base, text-muted-foreground
  action={<Button />}           // Primary action
/>
```

### Guidelines
- Icon in muted background circle
- Title is concise (3-6 words)
- Description explains why empty and what to do
- Action button guides next step
- Centered, generous padding (py-16)

---

## Error States

### Inline Errors (Form Validation)
- Red text, text-sm
- Icon (AlertCircle) at 16px
- Fade in (200ms)
- Positioned below field

### Alert Banners
- Destructive variant (red background, red border)
- AlertCircle icon
- Title + description
- Optional action (retry, dismiss)

### Full-Page Errors
- Centered layout
- Large icon (48px)
- Clear error message
- Retry button
- Back/home link

---

## Form Patterns

### Input States
```css
/* Default */
border: 1px solid var(--input);
background: var(--background);

/* Focus */
border-color: var(--ring);
outline: 2px solid var(--ring);
outline-offset: 2px;

/* Error */
border-color: var(--destructive);

/* Disabled */
opacity: 0.5;
cursor: not-allowed;
background: var(--muted);
```

### Label Pattern
```html
<Label>Field Name</Label>
<Input />
<p class="text-sm text-muted-foreground">Helper text</p>
<p class="text-sm text-destructive">Error message</p>
```

---

## Testing Checklist

Before shipping any component:

### Visual
- [ ] Spacing uses design tokens (no hardcoded values)
- [ ] Colors use CSS variables (no hardcoded hex)
- [ ] Typography follows hierarchy
- [ ] Hover states are visible
- [ ] Focus states meet accessibility standards
- [ ] Disabled states are obvious

### Responsive
- [ ] Works on mobile (375px)
- [ ] Works on tablet (768px)
- [ ] Works on desktop (1024px+)
- [ ] No horizontal scroll at any size
- [ ] Touch targets meet 44px minimum on mobile

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes
- [ ] Color contrast meets WCAG AA
- [ ] Focus indicators are visible
- [ ] ARIA labels on icon-only buttons

### Performance
- [ ] Transitions feel smooth (60fps)
- [ ] No layout shift on load
- [ ] Loading states preserve layout
- [ ] Animations respect prefers-reduced-motion

---

## Maintenance

This design system is a living document. Update it when:
- New patterns emerge across multiple features
- Inconsistencies are discovered
- New components are standardized
- User feedback reveals UX issues

**Always update DESIGN_SYSTEM.md before implementing a new pattern.** This ensures consistency and prevents design debt.

---

**Last updated:** February 14, 2026
**Next review:** March 2026
