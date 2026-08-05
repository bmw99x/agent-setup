# Mantine-specific patterns

### matchMedia + ResizeObserver

Mantine's `@mantine/core` calls `window.matchMedia` on mount and uses `ResizeObserver` for
layout. jsdom provides neither. Stub both in `setupTests.ts` (not per-file — see above).

### modals.openConfirmModal (imperative API)

`@mantine/modals` confirm modals render through a portal and are triggered imperatively.
Capture the config synchronously by mocking the module:

```ts
const openConfirmModalMock = vi.fn();

vi.mock("@mantine/modals", () => ({
  modals: { openConfirmModal: (...args: unknown[]) => openConfirmModalMock(...args) },
}));

afterEach(() => { openConfirmModalMock.mockReset(); });

it("opens confirm with correct title", async () => {
  // ... trigger action ...

  expect(openConfirmModalMock).toHaveBeenCalledTimes(1);

  const config = openConfirmModalMock.mock.calls[0]?.[0] as {
    title: string;
    onConfirm: () => void;
  };
  expect(config.title).toBe("Delete Item");

  // Execute the callback to trigger the mutation
  await act(async () => { config.onConfirm(); });
});
```

### `ModalsProvider` for `useModals` hook

When the component under test uses `useModals()` (not the imperative `modals` object),
wrap the render with `<ModalsProvider>`:

```ts
render(
  <MantineProvider>
    <ModalsProvider>
      <MyComponent />
    </ModalsProvider>
  </MantineProvider>,
);
```

### Selector dropdowns (Mantine `Select`)

Mantine's `Select` renders a hidden combobox — clicking the textbox opens the dropdown:

```ts
fireEvent.click(screen.getByRole("textbox", { name: "Template" }));
// options appear in the document (not inside the textbox)
fireEvent.click(screen.getByText("Option A"));
```

Use `screen.getAllByText(...)` + `.at(-1)` when the same text appears in the field AND the
dropdown list.

### `within()` for dialog scoping

Mantine modals render in a portal. Scope queries to avoid grabbing elements outside:

```ts
const dialog = await screen.findByRole("dialog", { name: "Edit Item" });
const q = within(dialog);
expect(q.getByText("Name")).toBeInTheDocument();
fireEvent.change(q.getByRole("textbox", { name: "Name" }), { target: { value: "New" } });
```
