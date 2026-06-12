# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySaaS → Mattermost one-way theme sync — commit 10427a4d

"""
Built-in Mattermost theme JSON presets for PolySaaS → MM one-way theme sync.

Values from Mattermost docs (Customize your theme) — Denim-like light and Onyx-like dark.
"""

# Classic Mattermost light (docs: "Mattermost" preset)
MM_THEME_LIGHT_JSON = (
    '{"sidebarBg":"#145dbf","sidebarText":"#ffffff","sidebarUnreadText":"#ffffff",'
    '"sidebarTextHoverBg":"#4578bf","sidebarTextActiveBorder":"#579eff",'
    '"sidebarTextActiveColor":"#ffffff","sidebarHeaderBg":"#1153ab",'
    '"sidebarTeamBarBg":"#0b428c","sidebarHeaderTextColor":"#ffffff",'
    '"onlineIndicator":"#06d6a0","awayIndicator":"#ffbc42","dndIndicator":"#f74343",'
    '"mentionBg":"#ffffff","mentionColor":"#145dbf","centerChannelBg":"#ffffff",'
    '"centerChannelColor":"#3d3c40","newMessageSeparator":"#ff8800","linkColor":"#2389d7",'
    '"buttonBg":"#166de0","buttonColor":"#ffffff","errorTextColor":"#fd5960",'
    '"mentionHighlightBg":"#ffe577","mentionHighlightLink":"#166de0","codeTheme":"github"}'
)

# Onyx-like dark (docs: Discord Dark New — matches MM v11 default dark palette)
MM_THEME_DARK_JSON = (
    '{"sidebarBg":"#121214","sidebarText":"#ffffff","sidebarUnreadText":"#ffffff",'
    '"sidebarTextHoverBg":"#1d1d1e","sidebarTextActiveBorder":"#ffffff",'
    '"sidebarTextActiveColor":"#ffffff","sidebarHeaderBg":"#121214",'
    '"sidebarHeaderTextColor":"#ffffff","sidebarTeamBarBg":"#121214",'
    '"onlineIndicator":"#43a25a","awayIndicator":"#ca9654","dndIndicator":"#d83a42",'
    '"mentionBg":"#6e84d2","mentionColor":"#ffffff","centerChannelBg":"#1a1a1e",'
    '"centerChannelColor":"#efeff0","newMessageSeparator":"#ff4d4d","linkColor":"#2095e8",'
    '"buttonBg":"#5865f2","buttonColor":"#ffffff","errorTextColor":"#ff6461",'
    '"mentionHighlightBg":"#a4850f","mentionHighlightLink":"#a4850f","codeTheme":"monokai"}'
)
