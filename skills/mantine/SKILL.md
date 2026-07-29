---
name: mantine
description: Use when building or reviewing UI with Mantine v8 — styling, components, forms, hooks. Enforces the styling precedence law (props before classNames before CSS modules).
version: 2.0.0
author: Bog
license: MIT
metadata:
  hermes:
    tags: [mantine, react, ui, components, styling]
    related_skills: [react, css, typescript]
---

# Mantine v8 Skill

Source of truth for styling: https://mantine.dev/styles/style-props/

## ⚠️ VERY IMPORTANT — Styling Precedence Law

Before writing ANY CSS, walk this ladder top-down. Stop at the first rung that works.

1. **Right component** — does Mantine already model this? A bordered, padded, rounded box IS `<Card>`/`<Paper>`. A vertical tab list IS `<Tabs orientation="vertical">`. A column of spaced children IS `<Stack>`; a row IS `<Group>`. Reach for the component before styling a `<Box>`/`<div>`.
2. **Style props** — `w`, `h`, `mih`, `maw`, `bg`, `bdrs`, `m`/`mt`/`p`/`px`, `c`, `ta`, `pos`, … Map CSS to props via [style-props.md](style-props.md). This handles the vast majority of one-off layout/spacing.
3. **`classNames` (Styles API)** — only when targeting a component's inner elements that props can't reach.
4. **CSS module `className`** — last resort. Only for things props/Styles API genuinely cannot express (pseudo-selectors, keyframes, `overflow`, `white-space`, complex `:has()`, container queries).

A CSS class that only sets things props can express (width, height, background, border-radius, margin, padding, flex-direction) is a defect. Delete it; use props.

**`style={{ ... }}` is NOT on this ladder.** It is never the answer. Even when no Mantine prop exists for a CSS property (e.g. `overflow`, `white-space`), the correct fallback is a CSS module class — not an inline style object. Inline style bypasses the cascade, breaks dark-mode overrides, and is flagged in every review.

### Hard rules (these are what reviewers flag)

- **Never `style={{ ... }}`** — not even for "no prop exists". Use a CSS module class instead. `style={{ overflow: "hidden" }}` → `.wrap { overflow: hidden }` + `className={classes.wrap}`.
- **No curly braces around string-literal props.** `w="100%"` not `w={"100%"}`. `h="100%"` not `h={"100%"}`.
- **No `createStyles`.** It was removed in v8 — use props → `classNames` → CSS modules.
- **Don't hand-roll layout** (`display:flex; flex-direction:column`) when `<Stack>`/`<Group>`/`orientation` props exist.
- **`gap`/`spacing` use theme tokens** (`gap="xs"`), not raw rem, unless a specific value is required.

When unsure which prop maps to a CSS property, consult [style-props.md](style-props.md) — do not guess or fall back to CSS.

## Theming
- Use theme tokens for color/spacing/typography — never hardcode.
  ```tsx
  const theme = useMantineTheme();
  const primary = theme.colors.blue[5];
  ```

## Components
- Prefer Mantine components over raw HTML: `Button`, `TextInput`, `Select`, `Checkbox`, `Textarea`, `Modal`, `Card`, `Paper`, `Stack`, `Group`, `Tabs`.

## Forms
- Use `@mantine/form`'s `useForm`, not raw controlled inputs.
  ```tsx
  const form = useForm({ initialValues: { email: "" }, validate: { email: (v) => (/^\S+@\S+$/.test(v) ? null : "Invalid") } });
  <TextInput {...form.getInputProps("email")} />
  ```

## Notifications
- `notifications.show({ title, message, color })` — never `alert()`.

## Modals
- `<Modal opened onClose title centered>` — closes on outside click, traps focus.

## Loading
- `<LoadingOverlay visible={isLoading} />` inside a `pos="relative"` parent — never blank screens.

## Accessibility
- Mantine covers basics; still verify keyboard nav, focus management, ARIA on custom components, contrast.
