# FX conversion

`convert(amount, currency, rates, latest_mode=False)` converts a minor-unit amount into GBP.

By default it uses the daily fixing published at 16:00. Pass `latest_mode=True` to use the
most recent intraday rate instead (checkout previews only — settlement always uses the fixing).
