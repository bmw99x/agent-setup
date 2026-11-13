# Nightly settlement totals

Our payment provider drops settlement files as CSV blobs into the `settlements` container of our storage account (`load_settings().storage_account_url` in `/app/app/settings.py`). Each CSV has a header row `merchant_id,amount`; amounts are decimal strings in GBP. The container also holds other, non-CSV files, which we ignore.

Write the nightly job in `/app/app/settlements/job.py`:

- `total_settlements(container_client)` takes an `azure.storage.blob.ContainerClient` for the container and returns a `dict[str, Decimal]` mapping each merchant id to its total amount across all CSV blobs.
- `main()` builds the real client for the `settlements` container, runs `total_settlements` and prints one `merchant_id,total` line per merchant.

The job runs as a CronJob in our AKS cluster under its managed identity. Developers also run it from their laptops after `az login`.

A malformed settlement file (a missing column, or an amount that is not a number) must not kill the night's run: skip that whole file, log which file was skipped, and keep going with the rest.

The SDKs are already installed; there is no network access in this environment.
