# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Geronimo Chat Integration — 2026-09-02

"""Geronimo chat preset prompts per endpoint.

Each endpoint (Odoo, Nextcloud, Mattermost, HubSpot, Slack) has curated preset questions
that guide users toward common tasks. Presets are rendered as quick buttons
in the Geronimo dock; clicking one injects the question into the chat input.

Presets include:
- label: short button text (e.g., "Summarize")
- template: the full question sent to LLM
- category: prompt type (data_exploration, bulk_action, analysis, navigation)
- icon: optional Font Awesome icon class (e.g., "fas fa-chart-bar")
"""


ODOO_INVOICES_PROMPTS = [
    {
        "label": "Summarize",
        "template": "Give me a summary of these invoices — total count, sum of amounts, status breakdown.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Find overdue",
        "template": "Which invoices are past due or approaching due date? Highlight the oldest ones.",
        "category": "analysis",
        "icon": "fas fa-exclamation-triangle",
    },
    {
        "label": "Top 5 by amount",
        "template": "What are the 5 largest invoices by amount? Include customer names and due dates.",
        "category": "data_exploration",
        "icon": "fas fa-sort-amount-down",
    },
    {
        "label": "Group by status",
        "template": "How many invoices are in each status (draft, open, paid, cancelled)? Show percentages.",
        "category": "analysis",
        "icon": "fas fa-list",
    },
]

ODOO_CONTACTS_PROMPTS = [
    {
        "label": "Summarize",
        "template": "Give me a summary of these contacts — total count, key industries, top locations.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Recent activity",
        "template": "Which contacts have recent activity? Show last interaction date and activity type.",
        "category": "analysis",
        "icon": "fas fa-clock",
    },
    {
        "label": "By location",
        "template": "Group these contacts by city/country. Show count and top contacts per region.",
        "category": "data_exploration",
        "icon": "fas fa-map-marker-alt",
    },
    {
        "label": "Find inactive",
        "template": "Which contacts are inactive or haven't been contacted in 90+ days?",
        "category": "analysis",
        "icon": "fas fa-user-slash",
    },
]

ODOO_SALES_PROMPTS = [
    {
        "label": "Pipeline summary",
        "template": "Summarize the sales pipeline — total opportunities, sum by stage, average deal size.",
        "category": "data_exploration",
        "icon": "fas fa-funnel",
    },
    {
        "label": "At risk deals",
        "template": "Which opportunities are at risk or stalled? Show reason, owner, and timeline.",
        "category": "analysis",
        "icon": "fas fa-exclamation-circle",
    },
    {
        "label": "Top deals",
        "template": "Show the top 10 deals by amount. Include stage, probability, and expected close date.",
        "category": "data_exploration",
        "icon": "fas fa-star",
    },
    {
        "label": "Win rate analysis",
        "template": "What's the win rate by rep? Which reps have the most closed deals this quarter?",
        "category": "analysis",
        "icon": "fas fa-trophy",
    },
]

NEXTCLOUD_FILES_PROMPTS = [
    {
        "label": "Folder summary",
        "template": "Summarize the contents of this folder — file count, size distribution, file types.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Large files",
        "template": "Which files are taking up the most space? Show file names, sizes, and last modified date.",
        "category": "analysis",
        "icon": "fas fa-weight",
    },
    {
        "label": "Organize by type",
        "template": "Group these files by type (documents, images, videos, etc.). Show count and total size per group.",
        "category": "data_exploration",
        "icon": "fas fa-filter",
    },
    {
        "label": "Recently modified",
        "template": "What files have been modified in the last 7 days? Show editor and edit timestamp.",
        "category": "analysis",
        "icon": "fas fa-clock",
    },
    {
        "label": "Shared status",
        "template": "Which files are shared externally? Show share permissions and who has access.",
        "category": "analysis",
        "icon": "fas fa-share-alt",
    },
]

MATTERMOST_CHANNELS_PROMPTS = [
    {
        "label": "Channel activity",
        "template": "Summarize recent activity in this channel — message count, active members, top topics.",
        "category": "data_exploration",
        "icon": "fas fa-chart-bar",
    },
    {
        "label": "Top contributors",
        "template": "Who are the most active members in this channel? Show message counts and last activity.",
        "category": "analysis",
        "icon": "fas fa-users",
    },
    {
        "label": "Recent threads",
        "template": "What are the recent discussion threads? Summarize the main topics and unresolved issues.",
        "category": "data_exploration",
        "icon": "fas fa-comments",
    },
    {
        "label": "Participation rate",
        "template": "What's the participation rate? Which members are lurkers vs. active? Any inactive members?",
        "category": "analysis",
        "icon": "fas fa-user-check",
    },
]

MATTERMOST_TEAMS_PROMPTS = [
    {
        "label": "Team summary",
        "template": "Summarize this team — member count, channels, activity level, team health.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Member status",
        "template": "Show team member list with status (online, away, offline). Highlight inactive members.",
        "category": "analysis",
        "icon": "fas fa-user-shield",
    },
    {
        "label": "Channel breakdown",
        "template": "List all channels in this team with message counts and recent activity.",
        "category": "data_exploration",
        "icon": "fas fa-list",
    },
]

HUBSPOT_CONTACTS_PROMPTS = [
    {
        "label": "Summarize",
        "template": "Give me a summary of these contacts — total count, key properties, engagement status.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Recent activity",
        "template": "Which contacts have recent activity? Show last interaction date and type.",
        "category": "analysis",
        "icon": "fas fa-clock",
    },
    {
        "label": "Engagement status",
        "template": "Group contacts by engagement (high, medium, low). Show count and characteristics.",
        "category": "analysis",
        "icon": "fas fa-signal",
    },
    {
        "label": "Find inactive",
        "template": "Which contacts are inactive or haven't been contacted in 90+ days?",
        "category": "analysis",
        "icon": "fas fa-user-slash",
    },
    {
        "label": "By lifecycle stage",
        "template": "Break down contacts by lifecycle stage (subscriber, lead, MQL, SQL, customer, evangelist, other).",
        "category": "data_exploration",
        "icon": "fas fa-funnel",
    },
]

HUBSPOT_DEALS_PROMPTS = [
    {
        "label": "Pipeline summary",
        "template": "Summarize the deals pipeline — total deals, sum by stage, average deal value.",
        "category": "data_exploration",
        "icon": "fas fa-funnel",
    },
    {
        "label": "At risk deals",
        "template": "Which deals are at risk or stalled? Show stage, owner, and days in current stage.",
        "category": "analysis",
        "icon": "fas fa-exclamation-circle",
    },
    {
        "label": "Top deals",
        "template": "Show the top 10 deals by amount. Include stage, owner, and close date.",
        "category": "data_exploration",
        "icon": "fas fa-star",
    },
    {
        "label": "Close date outlook",
        "template": "What deals are closing this month or next? Show by week.",
        "category": "analysis",
        "icon": "fas fa-calendar-check",
    },
    {
        "label": "Win/loss analysis",
        "template": "What's the win rate? Show won vs. lost deals by owner and stage.",
        "category": "analysis",
        "icon": "fas fa-trophy",
    },
]

SLACK_CHANNELS_PROMPTS = [
    {
        "label": "Channel activity",
        "template": "Summarize recent activity in this channel — message count, active members, sentiment.",
        "category": "data_exploration",
        "icon": "fas fa-chart-bar",
    },
    {
        "label": "Top contributors",
        "template": "Who are the most active members in this channel? Show message counts and activity frequency.",
        "category": "analysis",
        "icon": "fas fa-users",
    },
    {
        "label": "Recent discussions",
        "template": "What are the recent discussion threads? Summarize main topics and any open questions.",
        "category": "data_exploration",
        "icon": "fas fa-comments",
    },
    {
        "label": "Engagement rate",
        "template": "What's the member engagement? Show active members vs. lurkers and total conversation count.",
        "category": "analysis",
        "icon": "fas fa-user-check",
    },
]

SLACK_TEAMS_PROMPTS = [
    {
        "label": "Team snapshot",
        "template": "Summarize this Slack team — member count, channel count, activity level, health.",
        "category": "data_exploration",
        "icon": "fas fa-chart-pie",
    },
    {
        "label": "Member status",
        "template": "Show team member list with status (active, away, disabled). Highlight inactive members.",
        "category": "analysis",
        "icon": "fas fa-user-shield",
    },
    {
        "label": "Channel activity",
        "template": "List the most active channels. Show message count, member count, and recent activity.",
        "category": "data_exploration",
        "icon": "fas fa-list",
    },
    {
        "label": "Growth analysis",
        "template": "How is the team growing? Show member onboarding trends and channel creation rate.",
        "category": "analysis",
        "icon": "fas fa-chart-line",
    },
]


# Registry: maps endpoint action keys to their preset prompts
PROMPT_REGISTRY = {
    # Odoo
    "odoo.invoices": ODOO_INVOICES_PROMPTS,
    "odoo.contacts": ODOO_CONTACTS_PROMPTS,
    "odoo.sales": ODOO_SALES_PROMPTS,
    # Nextcloud
    "nextcloud.files": NEXTCLOUD_FILES_PROMPTS,
    # Mattermost
    "mattermost.channels": MATTERMOST_CHANNELS_PROMPTS,
    "mattermost.teams": MATTERMOST_TEAMS_PROMPTS,
    # HubSpot
    "hubspot.contacts": HUBSPOT_CONTACTS_PROMPTS,
    "hubspot.deals": HUBSPOT_DEALS_PROMPTS,
    # Slack
    "slack.channels": SLACK_CHANNELS_PROMPTS,
    "slack.teams": SLACK_TEAMS_PROMPTS,
}


def get_prompts_for_endpoint(endpoint_key: str) -> list:
    """Retrieve preset prompts for a given endpoint.
    
    Args:
        endpoint_key: vendor-qualified action key (e.g. "odoo.invoices")
    
    Returns:
        List of preset prompt dicts, or empty list if not found.
    """
    return PROMPT_REGISTRY.get(endpoint_key, [])


def get_context_hint_for_endpoint(endpoint_key: str) -> str:
    """Retrieve LLM context hint for a given endpoint.
    
    This hint describes what data is available to the LLM and how to use it.
    
    Args:
        endpoint_key: vendor-qualified action key (e.g. "odoo.invoices")
    
    Returns:
        Context hint string or empty string if not defined.
    """
    hints = {
        # Odoo
        "odoo.invoices": (
            "You are analyzing Odoo invoices. Each row includes: invoice number, date, customer, amount, "
            "status (draft/open/paid/cancelled), due date, and payment terms. Use this data to answer questions "
            "about payment status, overdue items, revenue trends, and invoice distribution."
        ),
        "odoo.contacts": (
            "You are analyzing Odoo contacts. Each row includes: contact name, company, email, phone, address, "
            "last interaction date, and tags. Use this to answer questions about contact segmentation, activity, "
            "location distribution, and relationship history."
        ),
        "odoo.sales": (
            "You are analyzing Odoo sales opportunities. Each row includes: opportunity name, customer, amount, "
            "stage (prospect/qualified/proposal/negotiation/closed-won/closed-lost), probability, owner, and "
            "expected close date. Use this to analyze pipeline health, deal progress, rep performance, and forecast."
        ),
        # Nextcloud
        "nextcloud.files": (
            "You are analyzing Nextcloud files in a shared folder. Each row includes: file name, type, size, "
            "last modified date, owner, and sharing status (private/shared-internal/shared-external). Use this to "
            "help with file organization, storage management, and access control analysis."
        ),
        # Mattermost
        "mattermost.channels": (
            "You are analyzing a Mattermost channel. Data includes: member list, recent messages, topic, creation "
            "date, and member activity. Use this to assess channel health, member engagement, and conversation trends."
        ),
        "mattermost.teams": (
            "You are analyzing a Mattermost team. Data includes: member list, channel list, member status, and recent "
            "activity across all channels. Use this to assess team structure, member availability, and overall team health."
        ),
        # HubSpot
        "hubspot.contacts": (
            "You are analyzing HubSpot contacts. Each row includes: contact name, email, phone, company, lifecycle stage, "
            "lead status, last activity date, and custom properties. Use this to analyze contact engagement, segmentation, "
            "and sales readiness."
        ),
        "hubspot.deals": (
            "You are analyzing HubSpot deals. Each row includes: deal name, amount, stage (negotiation, qualified to buy, "
            "decision maker bought-in, etc.), close date, owner, and associated contacts. Use this to analyze pipeline health, "
            "sales velocity, and forecast accuracy."
        ),
        # Slack
        "slack.channels": (
            "You are analyzing a Slack channel. Data includes: channel name, member list, message count, creation date, topic, "
            "and member activity. Use this to assess channel health, engagement, and conversation trends."
        ),
        "slack.teams": (
            "You are analyzing a Slack team (workspace). Data includes: member list, channel list, member status, and recent "
            "activity across all channels. Use this to assess team structure, member availability, communication patterns, and workspace health."
        ),
    }
    return hints.get(endpoint_key, "")
