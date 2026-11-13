import { Button, MantineProvider } from "@mantine/core";
import { render, screen } from "@testing-library/react";
import { test } from "vitest";

// No stubs of its own: passes only when the suite's setup file provides what Mantine needs from the browser.
test("a Mantine component renders in any test file", () => {
  render(
    <MantineProvider>
      <Button>Save</Button>
    </MantineProvider>,
  );
  screen.getByRole("button", { name: "Save" });
});
