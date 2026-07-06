# SentinelArena — Accessibility Statement

> **Standard:** WCAG 2.2 Level AA | **Last Audited:** 2026-07-06

## Commitment

SentinelArena is committed to ensuring digital accessibility for all users, including fans, volunteers, and organizers with disabilities. We aim to conform to WCAG 2.2 Level AA across all three frontend applications.

## Testing Methodology

### Automated Testing
- **axe-core** integrated into Playwright E2E tests (`@axe-core/playwright`)
- Runs on every CI build; critical violations fail the pipeline
- Covers: color contrast, ARIA attributes, heading hierarchy, form labels, keyboard traps

### Manual Testing
- Keyboard-only navigation testing on all critical user flows
- Screen reader testing with NVDA (Windows) and VoiceOver (macOS)
- Voice input/output flow testing in Chrome
- Text zoom to 200% functionality verification
- Reduced motion preference testing

## Accessibility Features

### All Applications
- Semantic HTML5 elements (`<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`)
- Proper heading hierarchy (single `<h1>` per page)
- All interactive elements are keyboard-navigable with visible focus indicators
- Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- `prefers-reduced-motion` media query respected for all animations
- Language attribute set on `<html>` element per current locale (WCAG SC 3.1.1)
- Error messages associated with form controls via `aria-describedby`

### Fan PWA (Additional)
- **ARIA live regions** (`aria-live="polite"`) for chat responses and crowd advisories
- **Voice input** via Web Speech API as alternative to typing (progressive enhancement)
- **Voice output** (TTS) for navigation instructions
- Indoor map includes text alternatives for all visual route information
- Touch targets ≥ 44x44px for mobile accessibility

### Web Dashboard (Additional)
- **ARIA live regions** for real-time crowd density updates
- Data tables include proper `<th>` scope attributes
- Heatmap includes text alternative density readings
- Decision actions have clear confirmation dialogs with focus management

### Volunteer App (Additional)
- Simplified interface optimized for quick task completion
- High-contrast mode support
- Large touch targets for field use

## Multi-Language as Accessibility

Supporting 5 languages (English, Hindi, Tamil, Telugu, Spanish) is itself an accessibility feature:
- **WCAG SC 3.1.1** (Language of Page): `lang` attribute dynamically set based on user locale
- **WCAG SC 3.1.2** (Language of Parts): Mixed-language content marked with appropriate `lang` attributes
- Enables participation by non-English-speaking fans and volunteers, which is a genuine inclusion requirement for international tournament venues

## Known Gaps

| Gap | Severity | Mitigation | Status |
|-----|----------|------------|--------|
| SVG indoor map may not be fully accessible to screen readers | Medium | Text-based route description provided alongside visual map | In progress |
| Web Speech API limited to Chrome/Edge | Low | Text input always available as fallback; documented as progressive enhancement | Accepted |
| Complex data visualizations (heatmap) may lack detailed descriptions | Medium | Tabular data alternative provided for all charts | In progress |

## Tools Used

- `@axe-core/playwright` — automated accessibility scanning in CI
- axe DevTools browser extension — manual audit
- WAVE Web Accessibility Evaluator — supplementary scanning
- Chrome DevTools accessibility inspector
- NVDA screen reader (Windows)
- Chrome Lighthouse accessibility audit

## Contact

For accessibility feedback or to report barriers, contact the SentinelArena team.
