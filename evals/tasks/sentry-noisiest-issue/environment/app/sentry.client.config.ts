import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  release: `storefront-web@${process.env.npm_package_version}`,
  tracesSampleRate: 0.1,
});
