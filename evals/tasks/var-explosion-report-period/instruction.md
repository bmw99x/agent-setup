# Tidy the sales report before the next feature

Next sprint we're adding a "compare with the previous period" section to the sales report in `/app/reports`, and the code there is already awkward to change. Refactor it first so that feature is easy to build. Don't add the feature itself.

`reports.cli.build_report` is what the finance team's scripts call, so its output for any arguments must stay exactly the same, and `/app/tests` must still pass.
