from mdrender._utils import escape_attr


def tracking_link(url: str, campaign_id: str, label: str) -> str:
    return f'<a href="{escape_attr(url)}" data-campaign="{escape_attr(campaign_id)}">{label}</a>'
