import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { render as rtlRender } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import { theme } from "./theme";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <MantineProvider theme={theme} env="test">
      <Notifications />
      {children}
    </MantineProvider>
  );
}

export function render(ui: ReactElement) {
  return rtlRender(ui, { wrapper: Providers });
}
