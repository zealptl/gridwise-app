# Dashboard Feature - Testing Guide

## 🧪 Quick Start Testing

### 1. Start the Development Server

```bash
cd /Users/zealpatel/development/gridwise/gridwise-app/app
npm run dev
```

Then open: `http://localhost:5173`

---

## 📋 Manual Testing Checklist

### Visual Testing

#### **Desktop (1440px+)**
- [ ] Open browser at full width
- [ ] Navigate to `/` (Dashboard)
- [ ] Verify 3-column grid layout
- [ ] Check header: "My Teams" + "Create Team" button aligned
- [ ] Verify filters are inline (season + status + count)
- [ ] Hover over a team card - should lift 2px with shadow
- [ ] Hover over buttons - should show visual feedback
- [ ] Check spacing: 24px gaps between cards
- [ ] Check card padding: 16px internal
- [ ] Verify typography hierarchy is clear

#### **Tablet (768px - 1024px)**
- [ ] Resize browser to 768px
- [ ] Verify 2-column grid layout
- [ ] Check filters still inline
- [ ] Verify cards adapt to narrower width
- [ ] Check no horizontal scroll
- [ ] Hover effects still work

#### **Mobile (375px)**
- [ ] Resize browser to 375px
- [ ] Verify single column layout
- [ ] Check filters stack vertically (if needed)
- [ ] Verify "Create Team" button fits
- [ ] Check team count moves to next line
- [ ] Verify touch targets are ≥ 44px
- [ ] No horizontal scroll
- [ ] Text remains readable

---

### Functional Testing

#### **Filter: Season**
- [ ] Click season dropdown
- [ ] Select "2026 Season"
- [ ] Verify results update (teams from 2026 only)
- [ ] Team count updates correctly
- [ ] Select "2025 Season"
- [ ] Verify results update again

#### **Filter: Status**
- [ ] Click status dropdown
- [ ] Select "Valid Only"
- [ ] Verify only valid teams show (green badges)
- [ ] Team count updates
- [ ] Select "Invalid Only"
- [ ] Verify only invalid teams show (red badges)
- [ ] Select "All Teams"
- [ ] Verify all teams show again

#### **Combined Filters**
- [ ] Set season to "2026" and status to "Valid Only"
- [ ] Verify correct filtered results
- [ ] Team count reflects filtered state

#### **Empty State**
- [ ] Apply filters that return no teams
- [ ] Verify empty state appears:
  - Large Layers icon in muted circle
  - "No teams yet" title
  - Helpful description
  - "Create Your First Team" button
- [ ] Click the button
- [ ] Verify navigates to `/teams/create`

#### **Team Cards**
- [ ] Verify each card shows:
  - Team name (large, bold)
  - Status badge (top-right, valid/invalid)
  - Season number
  - Budget used / 100M
  - Budget progress bar
  - Driver count
  - Constructor count
  - View button
  - Edit button
- [ ] Click "View" button
- [ ] Verify navigates to `/teams/{id}`
- [ ] Go back, click "Edit" button
- [ ] Verify navigates to `/teams/{id}/edit`

#### **Loading State**
- [ ] Throttle network to "Slow 3G" in DevTools
- [ ] Refresh page
- [ ] Verify skeleton grid appears:
  - 6 skeleton cards
  - Layout preserved (no layout shift)
  - Subtle pulse animation
- [ ] Wait for data to load
- [ ] Verify smooth transition to actual cards

#### **Error State**
- [ ] Stop backend server (simulate error)
- [ ] Refresh page
- [ ] Verify error display appears:
  - Alert with red styling
  - Error icon
  - Clear error message
  - "Try again" button
- [ ] Start backend server
- [ ] Click "Try again"
- [ ] Verify data loads successfully

---

### Interaction Testing

#### **Hover States**
- [ ] Hover over team card
  - Card lifts -2px
  - Shadow deepens
  - Transition is smooth (200ms)
- [ ] Hover over "Create Team" button
  - Background darkens slightly
  - Cursor becomes pointer
- [ ] Hover over "View" button
  - Border/background changes
  - Smooth transition
- [ ] Hover over "Edit" button
  - Background changes
  - Smooth transition

#### **Focus States** (Keyboard Navigation)
- [ ] Press Tab repeatedly
- [ ] Verify focus order:
  1. Season filter
  2. Status filter
  3. Create Team button
  4. Each team card's View button
  5. Each team card's Edit button
- [ ] Verify focus rings are visible (2px, primary color)
- [ ] Press Enter on focused button
- [ ] Verify action triggers

---

### Accessibility Testing

#### **Keyboard Navigation**
- [ ] Tab through all interactive elements
- [ ] Shift+Tab to navigate backwards
- [ ] Enter/Space to activate buttons
- [ ] Arrow keys in dropdowns
- [ ] Escape to close dropdowns
- [ ] No keyboard traps
- [ ] Logical tab order

#### **Screen Reader** (Using macOS VoiceOver or similar)
- [ ] Enable screen reader
- [ ] Navigate to dashboard
- [ ] Verify announces: "My Teams, heading level 1"
- [ ] Navigate to team card
- [ ] Verify announces team name, status, budget info
- [ ] Navigate to status badge
- [ ] Verify announces "Valid" or "Invalid"
- [ ] Navigate to progress bar
- [ ] Verify announces budget percentage
- [ ] Navigate to buttons
- [ ] Verify announces "View" and "Edit" with context

#### **Color Contrast** (Using browser DevTools)
- [ ] Inspect valid badge
  - Verify contrast ratio ≥ 4.5:1
- [ ] Inspect invalid badge
  - Verify contrast ratio ≥ 4.5:1
- [ ] Inspect body text
  - Verify contrast ratio ≥ 4.5:1
- [ ] Inspect muted text
  - Verify contrast ratio ≥ 4.5:1

#### **Motion Preferences**
- [ ] Enable "Reduce motion" in system preferences
- [ ] Refresh page
- [ ] Verify animations are minimal/instant
- [ ] Hover states should still work but faster

---

### Performance Testing

#### **Loading Performance**
- [ ] Open Chrome DevTools → Performance
- [ ] Record page load
- [ ] Stop recording
- [ ] Verify:
  - No layout shift (CLS = 0)
  - Fast paint times (< 1s)
  - Smooth animations (60fps)

#### **Animation Performance**
- [ ] Open DevTools → Rendering → FPS Meter
- [ ] Hover over multiple cards rapidly
- [ ] Verify FPS stays ~60
- [ ] No janky animations

#### **Memory**
- [ ] Open DevTools → Memory
- [ ] Take heap snapshot
- [ ] Apply various filters (season, status)
- [ ] Take another snapshot
- [ ] Verify no major memory leaks

---

### Responsive Testing (Real Devices)

#### **iPhone (Mobile)**
- [ ] Open on actual iPhone or simulator
- [ ] Verify single column layout
- [ ] Touch interactions work smoothly
- [ ] No pinch-to-zoom required
- [ ] Text is readable
- [ ] Buttons are easy to tap (44px+)

#### **iPad (Tablet)**
- [ ] Open on actual iPad or simulator
- [ ] Verify 2-column layout (portrait)
- [ ] Verify 3-column layout (landscape)
- [ ] Touch interactions work
- [ ] Layout feels balanced

---

## 🎨 Design Quality Checklist

### Visual Hierarchy
- [ ] Eye naturally lands on team name first
- [ ] Status badge is immediately noticeable
- [ ] Actions are clearly separated from data
- [ ] Page title is most prominent on screen

### Spacing & Rhythm
- [ ] All spacing feels consistent
- [ ] No cramped areas
- [ ] No excessive whitespace
- [ ] Cards have breathing room
- [ ] Grid gaps are balanced

### Typography
- [ ] Clear size hierarchy (title > card > body > meta)
- [ ] Line heights are comfortable
- [ ] Font weights establish hierarchy
- [ ] Text never too dense or sparse

### Color & Contrast
- [ ] Valid badge is clearly green (success)
- [ ] Invalid badge is clearly red (error)
- [ ] All text is readable
- [ ] Color has purpose (not decorative)

### Interaction Design
- [ ] Hover states are noticeable but subtle
- [ ] Transitions feel natural (not too fast/slow)
- [ ] Touch targets are appropriately sized
- [ ] Feedback is immediate

---

## 🐛 Known Issues to Test For

### Potential Edge Cases
- [ ] What happens with 0 teams?
  - Should show empty state ✅
- [ ] What happens with 1 team?
  - Should show grid with 1 card ✅
- [ ] What happens with 100+ teams?
  - Should scroll smoothly (pagination TBD)
- [ ] What if team name is very long?
  - Should wrap gracefully
- [ ] What if budget is 0?
  - Progress bar should be empty
- [ ] What if budget is > 100?
  - Progress bar should max at 100%
- [ ] What if network is slow?
  - Skeleton should show, no blank screen

### Browser Compatibility
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Safari iOS (latest)
- [ ] Chrome Android (latest)

---

## 📊 Test Data Scenarios

### Create Test Teams for Thorough Testing

#### **Scenario 1: Valid Team**
```json
{
  "team_name": "Lightning McQueen Racing",
  "season": 2026,
  "budget_used": 85.5,
  "is_valid": true,
  "driver_count": 5,
  "constructor_count": 2
}
```

#### **Scenario 2: Invalid Team**
```json
{
  "team_name": "Over Budget Nightmare",
  "season": 2026,
  "budget_used": 105.0,
  "is_valid": false,
  "driver_count": 3,
  "constructor_count": 1
}
```

#### **Scenario 3: Long Team Name**
```json
{
  "team_name": "This is a Very Long Team Name That Tests Text Wrapping and Truncation",
  "season": 2025,
  "budget_used": 50.0,
  "is_valid": true,
  "driver_count": 5,
  "constructor_count": 2
}
```

#### **Scenario 4: Edge Budget**
```json
{
  "team_name": "Perfect Budget Team",
  "season": 2026,
  "budget_used": 100.0,
  "is_valid": true,
  "driver_count": 5,
  "constructor_count": 2
}
```

---

## ✅ Acceptance Criteria Verification

Go through each criterion and verify:

### 1. Visual Hierarchy is Unmistakable
- [ ] Team name > status > actions hierarchy is clear
- [ ] No confusion about what's most important
- [ ] Eye flows naturally through the card

### 2. All Spacing Uses System Tokens
- [ ] Inspect card padding: should be 24px (p-6)
- [ ] Inspect grid gap: should be 24px (gap-6)
- [ ] No hardcoded pixel values in inline styles
- [ ] All spacing is 8px increments

### 3. Typography Establishes Clear Hierarchy
- [ ] Page title: 30px, bold
- [ ] Card title: 20px, semibold
- [ ] Body text: 16px, normal
- [ ] Metadata: 12-14px, muted

### 4. Colors are Semantic and Pass WCAG AA
- [ ] Green = success/valid (contrast ≥ 4.5:1)
- [ ] Red = error/invalid (contrast ≥ 4.5:1)
- [ ] No decorative color usage

### 5. Hover States Feel Responsive
- [ ] Transitions are 200ms (not too fast/slow)
- [ ] Visual feedback is clear
- [ ] No janky animations

### 6. Responsive Layout Works Fluidly
- [ ] Tested at 375px, 768px, 1024px, 1440px
- [ ] No breaks at any viewport
- [ ] Grid adapts smoothly

### 7. States Feel Designed
- [ ] Loading: skeleton preserves layout
- [ ] Empty: helpful and actionable
- [ ] Error: clear and retry-able

### 8. Accessibility Passes
- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Focus states are visible
- [ ] Color contrast meets standards

### 9. Feels Calm, Confident, Inevitable
- [ ] Design feels intentional, not arbitrary
- [ ] Nothing feels "added because AI suggested it"
- [ ] Every element has a purpose

### 10. Nothing Can Be Removed
- [ ] Every piece of data is necessary
- [ ] Every UI element serves a function
- [ ] No redundant information

---

## 🎯 The Jobs Test

Final validation:

### Question 1: Would a user need to be told how this works?
**Answer should be: NO**
- Dashboard purpose is obvious
- Filters are self-explanatory
- Actions are clearly labeled
- Empty state guides next step

### Question 2: Does this feel inevitable?
**Answer should be: YES**
- Design choices feel necessary, not arbitrary
- Hard to imagine it being designed differently
- Everything is in the "right" place

### Question 3: Is every detail refined?
**Answer should be: YES**
- Hover states are polished
- Empty state is thoughtful
- Loading state preserves layout
- Error state is helpful
- Typography is balanced
- Spacing is consistent

---

## 📸 Visual Regression Testing

### Take Screenshots for Comparison

1. **Desktop - Full Grid**
   - Viewport: 1440px
   - 6+ teams visible
   - All states visible

2. **Desktop - Empty State**
   - Viewport: 1440px
   - No teams
   - Empty state centered

3. **Desktop - Loading State**
   - Viewport: 1440px
   - Skeleton grid

4. **Tablet - 2 Column**
   - Viewport: 768px
   - Grid adapts

5. **Mobile - Single Column**
   - Viewport: 375px
   - Cards stack

6. **Hover State**
   - Desktop
   - Card hovered
   - Shadow visible

---

## 🚀 Ready for Production?

Before deploying, verify all of the above pass. If any fail:

1. Document the issue
2. Determine severity (critical, high, medium, low)
3. Fix critical/high issues before deployment
4. Log medium/low issues for future sprints

---

**Last Updated:** February 15, 2026
**Testing Duration:** ~30-45 minutes for complete checklist
**Tools Needed:** Browser DevTools, Screen Reader, Responsive Design Mode
