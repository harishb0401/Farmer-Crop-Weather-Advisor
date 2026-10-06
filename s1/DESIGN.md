---
name: AgriField Advisory System
colors:
  surface: '#f8f9ff'
  surface-dim: '#d0dbed'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dee9fc'
  surface-container-highest: '#d9e3f6'
  on-surface: '#121c2a'
  on-surface-variant: '#3f493f'
  inverse-surface: '#27313f'
  inverse-on-surface: '#eaf1ff'
  outline: '#6f7a6e'
  outline-variant: '#becabc'
  surface-tint: '#006d30'
  primary: '#00652c'
  on-primary: '#ffffff'
  primary-container: '#15803d'
  on-primary-container: '#d3ffd5'
  inverse-primary: '#79db8d'
  secondary: '#9b4500'
  on-secondary: '#ffffff'
  secondary-container: '#fd8a42'
  on-secondary-container: '#682c00'
  tertiary: '#00625b'
  on-tertiary: '#ffffff'
  tertiary-container: '#1b7c74'
  on-tertiary-container: '#c5fff7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#95f8a7'
  primary-fixed-dim: '#79db8d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#005323'
  secondary-fixed: '#ffdbca'
  secondary-fixed-dim: '#ffb68e'
  on-secondary-fixed: '#331200'
  on-secondary-fixed-variant: '#763300'
  tertiary-fixed: '#9cf2e8'
  tertiary-fixed-dim: '#80d5cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#00504a'
  background: '#f8f9ff'
  on-background: '#121c2a'
  surface-variant: '#d9e3f6'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.5rem
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: 2.5rem
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
    letterSpacing: 0em
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
    letterSpacing: 0em
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: 0.005em
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.02em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1.125rem
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 3rem
  space-xxs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system is tailored for agricultural extension workers, progressive farmers, and field agronomists operating in diverse, demanding environments—from high-glare sunlight across open acreage to handheld mobile interaction during crop inspections. The interface projects quiet authority, grounded resilience, and practical scientific clarity.

The visual style blends modern functional minimalism with organic, nature-inspired utility:
- **High-legibility pragmatism:** Prioritizes stark, immediate comprehension over decorative flourish. Every container, metric, and conversational flow exists to convey critical field intelligence (pest warnings, irrigation alerts, soil diagnostic reports).
- **Tactile, high-visibility surfaces:** Interfaces feature crisp edge definitions, structured tonal separation, and intentional avoidance of low-contrast translucent effects like glassmorphism.
- **Tone:** Grounded, encouraging, authoritative, and direct. Complex agronomic terminology is structured into glanceable, actionable visual segments.

## Colors

The palette balances vitality and agronomic precision with daylight accessibility:

- **Primary (`#15803d` - Deep Emerald Field):** Represents crop vitality, trusted advice, affirmative actions, and verified field guidance. Used for primary call-to-actions, proactive state indicators, and key chat accents.
- **Secondary (`#b45309` - Warm Amber Soil):** An alert tone reminiscent of dry loam and sunbaked harvest. Reserved for weather warnings, pest/disease threshold flags, urgent treatment actions, and pending approval statuses.
- **Tertiary (`#0f766e` - Deep Slate Sage):** Provides balance for secondary data points, soil moisture/irrigation status, technical agronomic citations, and diagnostic filters.
- **Neutral (`#1f2937` - Deep Charcoal Loam):** Anchors high-contrast typographic hierarchy. Never pure pitch black; it retains a mineral-rich warmth that reduces eye strain in harsh sunlight.
- **Canvas & Surface (Light):** Base canvas sits on `#f7f9f6` (a soft, sage-tinted off-white), transitioning to pure `#ffffff` for elevated conversational cards to maintain a minimum 4.5:1 text-to-background contrast ratio under outdoor solar glare.
- **Canvas & Surface (Dark):** Base canvas uses `#111827`, with message containers and elevated surfaces stepping up to `#1f2937` and `#374151`.

## Typography

The typography is optimized for outdoor readability, bilingual script balance, and rapid visual parsing:

- **Primary Typeface (Plus Jakarta Sans):** Selected for its open apertures, tall x-height, and robust geometric curves that prevent letter blending when viewing devices at low brightness or under bright sun.
- **Technical & Metric Typeface (JetBrains Mono):** Deployed strictly for agronomic data values, geo-coordinates, dosage measurements, batch numbers, and timestamps to eliminate misinterpretations of numbers in field notes.
- **Hierarchy Rules:** Body and chat bubbles maintain a baseline size of 1rem (`body-md`) to ensure comfortable reading distance without requiring pinch-to-zoom on field devices.

## Layout & Spacing

The layout is built around a single-column, conversation-first orientation on mobile devices, expanding into a dual-pane master-detail workflow on desktop and rugged field tablets:

- **Mobile (< 768px):** 4-column fluid layout with an edge margin of `1rem` (`space-md`). Maximum content container width remains fluid to maximize chat and diagnostic card reading areas.
- **Tablet (768px – 1024px):** 8-column layout with `1.5rem` margins. Introduces a persistent side navigation or secondary context rail for farm/plot selection.
- **Desktop (>= 1025px):** 12-column layout capped at a maximum width of `1280px` to prevent conversational message bubbles from stretching uncomfortably wide. The central conversational pane is fixed to a readable width of 640px to 768px.
- **Touch & Thumb Zones:** Minimum interactive tap target spacing is enforced at 48px to accommodate one-handed operation or use with field work gloves.

## Elevation & Depth

Visual hierarchy relies on structural tonal contrast and crisp low-contrast borders rather than deep or multi-layered drop shadows, which wash out in outdoor lighting:

- **Level 0 (Base Canvas):** `#f7f9f6` in light mode; provides a calm, glare-free background.
- **Level 1 (Card & Bubbles):** Solid `#ffffff` backed by a 1px border of `#e2e8f0` (or `#2e3846` in dark mode). An ambient outline shadow is added: `0 1px 2px 0 rgba(15, 23, 42, 0.05)`.
- **Level 2 (Popovers, Sticky Bar, Bottom Drawers):** `0 4px 12px -2px rgba(15, 23, 42, 0.08)`, paired with a solid 1px border.
- **Active Advisory States:** Critical alert panels drop shadows entirely in favor of high-contrast solid borders (e.g., a 2px stroke of `#b45309` for urgent action alerts).

## Shapes

The design uses a balanced rounded geometry (level 2) to combine modern softness with disciplined structure:

- **Default Elements:** 0.5rem (`8px`) border radius for standard cards, inputs, and advisory containers.
- **Buttons & Interactive Chips:** Fully pill-shaped (`rounded-full`, 9999px) or `rounded-lg` (`12px`) to communicate touchability and frictionless selection.
- **Conversational Bubbles:** Asymmetric rounding to visually anchor flow:
  - **Advisor / System Bubbles:** `16px` on top-left, top-right, and bottom-right; `4px` on bottom-left.
  - **User / Farmer Responses:** `16px` on top-left, top-right, and bottom-left; `4px` on bottom-right.

## Components

### Buttons
- **Primary:** Solid `#15803d` background, `#ffffff` text, 0.5rem radius, min-height 48px. Hover/pressed state shifts to `#166534`.
- **Secondary / Alert:** Solid `#b45309` background with `#ffffff` text for urgent field interventions.
- **Tertiary / Ghost:** Transparent background, `#15803d` text, 1px border in `#15803d` for non-destructive alternate paths.

### Conversational Message Bubbles
- **Agronomist Advisory Bubble:** Off-white/slate surface (`#ffffff`), 1px border (`#e2e8f0`), text in `#1f2937`. Includes metadata header (advisor credentials, timestamp in JetBrains Mono).
- **Farmer / Inquirer Bubble:** Solid `#15803d` surface, text in `#ffffff`, timestamps rendered in `#dcfce7`.
- **System Recommendation Card:** Embedded directly within the chat stream with an emerald-tinted header (`#f0fdf4`), an icon, structured bullet points, and high-contrast callout chips.

### Chips & Action Pills
- Quick-response prompts (e.g., "Confirm Pest Symptoms", "Watering Schedule", "Request Chemical Dosage") rendered with a 1px border of `#cbd5e1`, white background, `#15803d` text, and pill radius.
- Selected state turns solid `#15803d` with white text.

### Form Inputs & Message Box
- Persistent anchored bottom input bar with a 48px minimum height.
- Input fields use `#ffffff` backgrounds, 1.5px border in `#cbd5e1`, focusing to a 2px `#15803d` ring.
- Camera and audio recording triggers sit alongside the text input for immediate field-condition uploads.

### Diagnostic Cards
- Compact summary cards containing photo comparison modules, risk severity tags (Low: `#15803d`, Warning: `#b45309`, Severe: `#b91c1c`), and dosage calculators utilizing tabular mono numbers.