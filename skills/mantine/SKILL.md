---
name: mantine
description: Use when building UI with Mantine v8. Covers component usage, theming, form handling, and hooks.
version: 1.0.0
author: Bog
license: MIT
metadata:
  hermes:
    tags: [mantine, react, ui, components]
    related_skills: [react, css, typescript]
---

# Mantine v8 Skill

## Package Structure
- Use components from `@mantine/core`, `@mantine/hooks`, `@mantine/form`
- Each package is tree-shakeable; import only what you need

## Theming
- Use Mantine's theme object for colors, spacing, typography
- Never hardcode values; use theme tokens
  ```typescript
  import { useMantineTheme } from '@mantine/core';
  
  const theme = useMantineTheme();
  const primaryColor = theme.colors.blue[5];
  ```

## Components
- Prefer Mantine components over raw HTML elements
- Use Mantine equivalents: `Button`, `TextInput`, `Select`, `Checkbox`, `Textarea`, `Modal`, etc.
  ```typescript
  import { Button, TextInput, Select } from '@mantine/core';
  
  <Button variant="filled" onClick={handleSubmit}>
    Submit
  </Button>
  
  <TextInput
    label="Email"
    placeholder="you@example.com"
    error={errors.email}
  />
  ```

## Forms
- Use `@mantine/form` with `useForm` hook, not controlled inputs directly
  ```typescript
  import { useForm } from '@mantine/form';
  
  const form = useForm({
    initialValues: { email: '', name: '' },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
    },
  });
  
  <TextInput {...form.getInputProps('email')} />
  ```

## Notifications
- Use the `notifications` hook for user feedback
- Never use `alert()` for user-facing messages
  ```typescript
  import { notifications } from '@mantine/notifications';
  
  notifications.show({
    title: 'Success',
    message: 'Your changes have been saved',
    color: 'green',
  });
  ```

## Modals
- Use Mantine's `Modal` component
- Should close on outside click and trap focus
  ```typescript
  import { Modal } from '@mantine/core';
  
  <Modal
    opened={opened}
    onClose={onClose}
    title="Confirm Action"
    centered
  >
    {/* modal content */}
  </Modal>
  ```

## Loading States
- Use `Loader` component or loading overlays
- Never show blank screens during async operations
  ```typescript
  import { LoadingOverlay, Loader } from '@mantine/core';
  
  <Box pos="relative">
    <LoadingOverlay visible={isLoading} />
    {/* content */}
  </Box>
  ```

## Colors
- Use theme colors via `useMantineTheme()` or `getThemeColor()`
  ```typescript
  import { useMantineTheme, getThemeColor } from '@mantine/core';
  
  const theme = useMantineTheme();
  const primary = getThemeColor('blue', theme);
  ```

## Custom Styles
- Use `createStyles` or inline `style` prop for one-off overrides
- Avoid global CSS for component customization
  ```typescript
  import { createStyles } from '@mantine/core';
  
  const useStyles = createStyles((theme) => ({
    customButton: {
      backgroundColor: theme.colors.blue[5],
    },
  }));
  
  // Or inline:
  <Box style={{ backgroundColor: 'blue' }} />
  ```

## Accessibility
- Mantine handles basic a11y, but verify:
  - Keyboard navigation works
  - Focus management is correct
  - ARIA labels on custom components
  - Color contrast meets WCAG standards
