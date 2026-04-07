# Design System Strategy: The Focused Canvas

## 1. Overview & Creative North Star
This design system is built upon the Creative North Star of **"The Task Flow."** 

We are moving away from the "grid of boxes" common in productivity tools. Instead, we treat the task management experience as a living, breathing editorial space. This system prioritizes **intentional asymmetry** and **tonal depth** over rigid structural lines. By leveraging the sophistication of Notion’s clarity and Linear’s high-performance utility, we create a UI that feels less like a database and more like a premium workspace. 

The "template" look is avoided through the use of aggressive whitespace and a "layering" philosophy. Rather than using borders to separate ideas, we use the proximity of elements and subtle shifts in surface luminance to guide the eye.

---

## 2. Colors: Tonal Architecture
The palette is built on a foundation of sophisticated slate grays and a high-energy indigo. We do not use color to decorate; we use it to direct intent.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Boundaries must be defined solely through background color shifts. For example, a `surface-container-low` task list sitting on a `surface` background creates a natural, soft-edge separation that feels integrated, not boxed in.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked sheets of fine paper. 
*   **Base:** `surface` (#faf8ff)
*   **Lower Depth:** `surface-container-low` (#f2f3ff) for background groupings.
*   **Higher Depth:** `surface-container-highest` (#dae2fd) for active states or focused sidebars.
*   **The Signature Gradient:** For primary CTAs (like "Add Task"), do not use a flat hex. Use a linear gradient from `primary` (#4648d4) to `primary_container` (#6063ee) at a 135-degree angle to provide a "soul" and tactile quality.

### Glassmorphism
Floating elements (Modals, Hover Menus) should utilize `surface_container_lowest` at 80% opacity with a `20px` backdrop-blur. This allows the user's content to bleed through, maintaining context and "visual air."

---

## 3. Typography: Editorial Authority
We use **Inter** as our typeface, but we treat it with editorial weight.

*   **Display & Headline:** Used sparingly to define "State of Mind." `headline-lg` is your anchor for dashboard views.
*   **Title:** `title-md` and `title-sm` use `Medium (500)` or `Semi-Bold (600)` weight. This creates an authoritative contrast against the `Regular (400)` body text.
*   **The Utility Scale:** `label-md` and `label-sm` are for metadata (dates, tags). Use `on_surface_variant` (#464554) to ensure these don't compete with the task title.

The hierarchy is designed to be "Top-Heavy." Large, bold titles provide the "What," while light, airy body text provides the "Details," creating a rhythm that encourages scanning.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are a fallback, not a primary tool.

*   **The Layering Principle:** Depth is achieved by "stacking." Place a `surface-container-lowest` card on a `surface-container-low` section to create a soft, natural lift.
*   **Ambient Shadows:** When a floating effect is required (e.g., a task detail pop-over), use a shadow with a `24px` blur and `4%` opacity. The shadow color must be tinted with `on_surface` (#131b2e) to mimic natural light.
*   **The Ghost Border:** If accessibility requires a container boundary, use the `outline_variant` (#c7c4d7) at **15% opacity**. A 100% opaque border is considered a design failure in this system.

---

## 5. Components: The Primitive Set

### Buttons
*   **Primary:** Gradient of `primary` to `primary_container`. White text. Border radius: `xl` (0.75rem).
*   **Secondary:** `surface_container_high` background. No border.
*   **Tertiary:** Ghost style. No background until hover. Use `on_surface_variant` for text.

### Input Fields
*   **The Focused Input:** Eschew the 4-sided box. Use a `surface_container_low` background with a `xl` radius. Upon focus, the background transitions to `surface_container_lowest` with a subtle `primary` glow (2px blur).

### Cards & Task Lists
*   **The Divider Ban:** Never use a horizontal line to separate tasks. Use `12px` of vertical white space or a subtle hover state shift to `surface_container_low`. 
*   **Checkboxes:** When checked, the checkbox should transition to `primary` and the task text should move to `on_surface_variant` with a `0.6` opacity.

### Chips (Tags)
*   Low-profile. Use `surface_container_high` with `label-sm` typography. The radius should always be `full` (9999px) to contrast against the `xl` radius of cards.

### Navigation Sidebar
*   Use `surface_dim` (#d2d9f4) to create a clear "anchor" on the left. The active menu item should use `surface_container_lowest` with a `primary` vertical accent bar (4px width) on the far left.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use asymmetrical margins. A wider left margin on task titles creates an "editorial gutter" that feels premium.
*   **Do** use Lucide icons at a `1.25px` or `1.5px` stroke weight. Anything thicker feels "clunky"; anything thinner feels "frail."
*   **Do** leverage `surface_bright` for peak highlights in Dark Mode to maintain readability.

### Don’t
*   **Don’t** use pure black (#000) or pure white (#fff) for backgrounds. Use the tokens `surface` and `on_background` to maintain a soft, "ink on paper" feel.
*   **Don’t** use "Pop-up" animations. Use "Slide and Fade" (200ms, Ease-Out) to mimic the movement of physical layers.
*   **Don’t** use borders on cards. If the card isn't visible against the background, your surface tokens are too close in value—adjust the nesting tier instead.