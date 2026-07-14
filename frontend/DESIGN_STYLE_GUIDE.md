# ARWA Design Style Guide

## Design Principles

### 1. Premium Wellness Aesthetic
- Clean, spacious layouts that feel calming
- Warm, muted color palette inspired by nature and wellness
- Smooth, purposeful animations that feel premium

### 2. Hierarchy Through Refinement
- Use size, weight, and spacing (not color) for emphasis
- Opacity variations create visual hierarchy
- Whitespace is a design element, not wasted space

### 3. Consistent Micro-Interactions
- Every interactive element provides feedback
- Transitions are smooth (200-300ms) and purposeful
- Hover, active, and focus states are distinct

### 4. Accessibility First
- All interactive elements have clear focus states
- Color is never the only indicator of state
- Motion respects prefers-reduced-motion

---

## Color System

### Primary Colors
```
Primary Orange (Wellness): oklch(0.545 0.175 42)
Used for: CTA buttons, active states, accent elements, brand identity
Hex equivalent: ~#8B5D42 (warm brown)
```

### Neutral Palette
```
Background: oklch(0.96 0.032 85) - light cream
Card: oklch(1 0 0) - pure white
Text/Foreground: oklch(0.195 0.025 20) - dark charcoal
Border: oklch(0.91 0.02 85) - subtle light gray
Muted: oklch(0.94 0.02 85) - soft gray
```

### Dark Mode
```
Background: oklch(0.17 0.02 85) - dark navy
Card: oklch(0.24 0.02 85) - slightly lighter navy
Text: oklch(0.92 0.015 0) - off-white
Primary: oklch(0.585 0.16 42) - lighter orange
```

### Opacity Hierarchy
- **70%** (Primary body text, labels)
- **60%** (Secondary text, descriptions)
- **50%** (Tertiary text, hints)
- **30%** (Borders, very subtle elements)
- **10%** (Icon backgrounds, very light accents)

---

## Typography

### Font Families
- **Headlines**: Default system font (Geist or fallback)
- **Body**: Default system font (Geist or fallback)
- **Mono**: System mono font

### Type Scales
```
Hero Headlines: text-7xl, font-bold, tracking-tight, leading-[1.15]
Section Headers: text-4xl, font-bold, tracking-tight
Card Headers: text-2xl, font-bold, tracking-tight
Labels: text-sm, font-semibold, uppercase, tracking-wide
Body: text-base/lg, font-400-500, leading-relaxed
```

### Line Heights
- Headlines: 1.15 (tight, premium feel)
- Body: 1.5-1.6 (relaxed, readable)
- Labels: 1.2 (compact)

---

## Spacing

### Base Unit: 4px
All spacing uses Tailwind's 4px base (p-1 = 4px, p-2 = 8px, etc.)

### Common Patterns
```
Card Padding: p-8 to p-12
Section Spacing: space-y-10 to space-y-12
Grid Gaps: gap-8 to gap-10
Element Gaps: gap-3 to gap-4
```

### Padding Standards
- **Compact Elements**: p-3 to p-4 (12-16px)
- **Standard Cards**: p-8 to p-10 (32-40px)
- **Hero Sections**: p-10 to p-16 (40-64px)

### Page Margins
```
Mobile: px-6 (24px)
Tablet: px-8 (32px)
Desktop: px-10 lg:px-12 (40-48px)
```

---

## Components

### Buttons
**All buttons are rounded-full (pill-shaped)**

#### Variants
```
Default: bg-primary, text-primary-foreground, shadow-md
Outline: border-border/50, bg-background, hover:bg-muted
Ghost: No background, hover:bg-muted/50
Destructive: bg-destructive/10, text-destructive
Link: text-primary, underline on hover
```

#### Sizes
- **xs**: h-7, px-3, gap-1.5 (for compact UI)
- **sm**: h-8, px-3.5, gap-1.5
- **default**: h-9, px-4, gap-2
- **lg**: h-11, px-6, gap-2 (for primary CTAs)
- **icon**: Circular buttons with appropriate sizing

#### States
```
Hover: Scale up slightly, enhanced shadow
Active: Scale down (active:scale-95), reduced shadow
Focus: Ring with ring-2 and ring-ring/50
Disabled: opacity-50, pointer-events-none
```

### Cards
**Base styling**: `rounded-2xl` with soft shadows

#### Shadow Progression
```
Base: shadow-[0_1px_3px_rgba(0,0,0,0.05)]
Hover: shadow-[0_4px_12px_rgba(0,0,0,0.08)]
Active: shadow-[0_2px_8px_rgba(0,0,0,0.04)]
```

#### Padding Standards
- **Compact**: p-6 (24px)
- **Standard**: p-8 (32px)
- **Generous**: p-10 to p-12 (40-48px)

### Input Fields
```
Base: bg-input, border-border, rounded-lg, px-3 py-2
Focus: border-ring, ring-2 ring-ring/30
Placeholder: text-foreground/50
```

---

## Animations

### Keyframes (Available Globally)
```
fadeIn: 0% opacity: 0 → 100% opacity: 1
slideUp: 0% opacity: 0, translateY(12px) → 100% opacity: 1, translateY(0)
slideDown: 0% opacity: 0, translateY(-8px) → 100% opacity: 1, translateY(0)
scaleIn: 0% opacity: 0, scale(0.95) → 100% opacity: 1, scale(1)
pulse-soft: 0%/100% opacity: 1 → 50% opacity: 0.8
```

### Animation Timings
- **Fast**: 200ms (micro-interactions, hovers)
- **Standard**: 300ms (page transitions, cards)
- **Slow**: 500ms+ (important state changes)

### Easing Functions
- **Default**: cubic-bezier(0.4, 0, 0.2, 1) (ease-in-out)
- **Spring-like**: cubic-bezier(0.34, 1.56, 0.64, 1) for exit animations
- **Linear**: For consistent rotation/progress

### Transition Classes
```
All elements globally: transition-colors duration-200
Interactive elements: transition-all duration-300
Specific elements: transition-[property] duration-[time]
```

---

## Shadows System

### Shadow Progression
```
Subtle: 0_1px_3px_rgba(0,0,0,0.05)
Light: 0_2px_8px_rgba(0,0,0,0.04)
Medium: 0_4px_12px_rgba(0,0,0,0.08)
Strong: 0_6px_24px_rgba(0,0,0,0.12)
Deep: 0_8px_32px_rgba(0,0,0,0.15)
```

### Usage Guidelines
- **Cards**: Medium (0_4px_12px) base, Light (0_2px_8px) on hover
- **Buttons**: Light (0_1px_3px) base, Medium (0_4px_12px) on hover
- **Modals**: Strong (0_6px_24px) for elevation
- **Floating Elements**: Medium to Deep for prominence

---

## Layout Grids

### Responsive Patterns
```
Mobile (default): 1 column, full width
Tablet (md): 2-3 columns with md:grid-cols-2/3
Desktop (lg): 3-4 columns with lg:grid-cols-3/4
```

### Grid Spacing
```
Gap: gap-6 (small spacing), gap-8 (standard), gap-10 (generous)
Responsive: gap-6 md:gap-8 lg:gap-10
```

### Max Content Width
```
Narrow: max-w-2xl (for forms, focused content)
Standard: max-w-4xl (dashboard sections)
Wide: max-w-7xl (full dashboard, main content)
```

---

## Icon Guidelines

### Sizing
```
Inline: size-4 (16px) - within text
UI Buttons: size-5 (20px) - standard interaction
Large Actions: size-6 (24px) - prominent buttons
Hero/Decorative: size-8+ (32px+) - featured elements
```

### Color
```
Default: text-foreground/70
Active/Primary: text-primary
Muted/Disabled: text-foreground/40
```

### Background Containers
```
Default: bg-muted/50, w-12 h-12, rounded-lg
Primary: bg-primary/10, text-primary, w-12 h-12, rounded-lg
Icon-only buttons: No background, just hover effect
```

---

## Interaction Patterns

### Hover States
```
Cards: shadow-[0_4px_12px_rgba(0,0,0,0.08)]
Buttons: shadow increase + color change
Links: underline addition or opacity change
```

### Active States
```
All interactive: active:scale-95 (slight compression)
Buttons: shadow reduction, color deepening
```

### Focus States
```
Buttons/Inputs: focus-visible:ring-2 focus-visible:ring-ring/50
Links: focus-visible:outline-2 outline-offset-2
```

### Disabled States
```
Universal: opacity-50 + pointer-events-none
Inputs: bg-muted, cursor-not-allowed
```

---

## Content Margins

### Page Structure
```
Header: Always fixed with thin border
Sidebar: Fixed on desktop, collapsible on mobile
Main Content: Respects viewport with px-8 sm:px-10 lg:px-12
Footer: If needed, respects page margins
```

### Section Spacing
```
Between major sections: space-y-12
Between subsections: space-y-8
Within section content: space-y-6
```

---

## Accessibility Checklist

- [ ] All buttons have sufficient hit area (min 44x44px)
- [ ] Color contrast ratio ≥ 4.5:1 for text
- [ ] Focus visible states on all interactive elements
- [ ] Alt text on all images
- [ ] Semantic HTML (button, a, form elements)
- [ ] Keyboard navigation supported
- [ ] ARIA labels where appropriate
- [ ] Motion respects prefers-reduced-motion
- [ ] Form fields have associated labels
- [ ] Error messages are clear and actionable

---

## Usage Examples

### Premium Button
```tsx
<Button size="lg" className="rounded-full px-8 gap-2">
  <Plus className="h-5 w-5" />
  Create Item
</Button>
```

### Premium Card
```tsx
<Card className="p-10 md:p-12">
  <h3 className="text-xl font-bold text-foreground mb-6">Title</h3>
  <p className="text-sm text-foreground/70">Content</p>
</Card>
```

### Premium Page Header
```tsx
<div className="space-y-3">
  <h1 className="text-4xl font-bold text-foreground tracking-tight">Title</h1>
  <p className="text-lg text-foreground/70">Subtitle</p>
</div>
```

### Premium Layout
```tsx
<div className="space-y-12">
  <div className="space-y-3">
    <h1>Section</h1>
  </div>
  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
    {/* Cards */}
  </div>
</div>
```

---

## Design Tokens Summary

| Property | Light | Dark |
|----------|-------|------|
| Background | `#F5F1E8` | `#2B2820` |
| Foreground | `#322219` | `#EBEAE8` |
| Card | `#FFFFFF` | `#3D3935` |
| Primary | `#8B5D42` | `#9E7B67` |
| Border | `#E8E3DC` | `#1A1814` |
| Muted | `#EFEBE3` | `#5C5248` |

---

## Future Enhancements
- Animation library integration (Framer Motion)
- Advanced form states and validation styling
- Toast notifications with animations
- Modal/Dialog premium styling
- Data table premium styling
- Chart tooltip styling consistency
