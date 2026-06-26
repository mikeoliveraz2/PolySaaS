PolySaaS AI Chat Enhancement Proposal
Context-Aware Gemini Chat Box Everywhere
Version 1.0
Date: June 13, 2026
Author: Mike Oliver – Founder & Chief Architect

Executive Summary
Make the PolySaaS AI chat widget (available on every page) context-aware by automatically feeding it rich information about the current page when it loads. Power it with Google Gemini to create a deeply intelligent assistant that understands exactly where the user is in the platform.
This turns a simple chat box into a true AI co-pilot that knows the tenant, current screen, open Mattermost channel, active Odoo record, orchestration state, etc.
Strategic Goal: Heavy Gemini usage to gain Google’s attention, strengthen our Google for Startups relationship, and demonstrate real AI integration.

Business & Demo Value

User Experience: Users can ask natural questions like:
“Summarize this Odoo Sales Order”
“What does this Mattermost plugin do?”
“How do I set up orchestration for this page?”
“Explain the recent changes in this tenant”

Google Angle:
Significant Gemini API usage (positive signal)
Showcases deep integration with Google’s latest models
Strengthens positioning for Google Cloud credits and potential partnership

Competitive Edge: Most platforms have generic chat. Ours will be context-aware and feel like a native part of the operating system.
Monetization: Premium “AI Co-Pilot” tier with higher Gemini usage and advanced context.


Technical Approach

Page Context Collection (on load)
Current URL / Action Path
Page title and section
Tenant info
Active service (Mattermost, Odoo, etc.)
Green bar / orchestration state
Optional: Recent logs, open records, etc.

Frontend Hook
When the PolySaaS AI chat opens, include the context in the system prompt sent to Gemini.

Backend
Route PolySaaS AI chat requests to Gemini (with context injected)
Optional: Add a “Use Current Page Context” toggle

Example System PrompttextYou are Geronimo, the PolySaaS AI assistant. 
Current context: Tenant=PolySaaS Test 154, Page=Mattermost Town Square, Action Path=...
Be helpful, concise, and suggest orchestration actions when relevant.


Recommended Next Steps

Implement basic context passing + Gemini backend routing
Add smart context collection (especially for Mattermost and Odoo)
Create demo flows showing context-aware questions
Monitor Gemini usage and include in Google for Startups reporting