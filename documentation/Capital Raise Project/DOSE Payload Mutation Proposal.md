PolySaaS DOSE Enhancement Proposal
Intelligent Request Payload Mutation via Atomic Services
Version 1.2
Date: June 13, 2026
Author: Mike Oliver – Founder & Chief Architect

Executive Summary
DOSE already delivers powerful outbound orchestration. The proposed Request Payload Mutation capability will allow Atomic Services to inspect and modify/replace incoming POST/PUT payloads before they reach upstream systems.
This turns PolySaaS into a true AI-First intelligent middleware — capable of real-time content transformation, enrichment, sanitization, and policy enforcement.
Strategic Value: Extremely strong sales story. We can speak about it confidently now. When a prospect wants proof, we can build a targeted demo in minutes.

Powerful Real-World Example: AI Content Cleaning in Odoo
Scenario (perfect for demos and enterprise use):

User is creating/editing a record in Odoo (e.g. Sales Order, Project Task, Forum Post, Helpdesk Ticket, etc.).
They enter free-text in a field like Description, Notes, or Internal Comments.
A DOSE Instruction matches the POST request to that Odoo endpoint.
The instruction triggers a new GrokClean Atomic Service.
GrokClean:
Extracts the target text field (configurable via parameters).
Calls Grok to rewrite/clean the content (remove profanity, improve clarity, enforce brand tone, translate, summarize, etc.).
Returns the cleaned text as payload_new.

DOSE controller replaces the original payload with the cleaned version before it reaches Odoo.

Result: Odoo always receives clean, professional, brand-compliant content — with full audit trail and zero user friction.
Parameters Example (auto-populated in modal):
JSON{
  "field_to_clean": "description",
  "instructions": "Rewrite professionally, remove any profanity, improve clarity while keeping original meaning",
  "max_length": 2000
}
This single service beautifully demonstrates:

AI-First value proposition
Real-time content governance
Seamless integration with existing Odoo workflows
Security & quality control without extra user steps


Technical Approach
Core mutation logic will be added to the AtomicService superclass so every service can optionally return payload_new.
Individual services (like GrokClean) simply return:
Pythonreturn {
    "status": "success",
    "payload_new": modified_request_body,
    "cleaned_fields": ["description"],
    "message": "Content cleaned by Grok"
}

Additional High-Value Use Cases

Enrich payloads with AI-generated fields
Add tenant/user context tokens
Sanitize PII before external systems
Transform data formats between systems
Route or split requests based on content


Recommended Next Steps (Post-Demo)

Implement base mutation logic in AtomicService superclass.
Build GrokClean service as flagship example.
Add clear UI support in the orchestration modal.
Document + create demo script for Odoo content cleaning.


Status: Ready for implementation after current demo/video is complete. This feature significantly strengthens our competitive positioning.
