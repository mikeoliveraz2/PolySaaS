# PolySaaS Development Kanban Board

> **Last Updated:** 2026-05-19  
> **Active Sprint:** Mattermost Polish + Tooling

---

## 📋 Board Columns

| Backlog | To Do | In Progress | Review / Testing | Done |
|---------|-------|-------------|------------------|------|
| See below | See below | See below | See below | See below |

---

## 🔙 Backlog

### 3. Build PolySniffer 2.0
**Priority:** Medium | **Effort:** 5 days

Dedicated inspection window with Passthrough + Direct modes for capturing and analyzing traffic patterns from bundled applications.

**Acceptance Criteria:**
- [ ] Standalone inspection UI accessible from Django admin
- [ ] Passthrough mode: captures proxied requests through `/pt/admin/` paths
- [ ] Direct mode: captures direct upstream requests for comparison
- [ ] Request/response diff viewer with syntax highlighting
- [ ] Export captured patterns as YAML/JSON for handler configuration
- [ ] Session recording and playback for debugging

---

### 4. Implement Passthrough Instruction Attachments / Action Events
**Priority:** Medium | **Effort:** 3 days

Allow Instructions model to define event-triggered passthrough actions (e.g., "when message contains X, forward to external endpoint Y").

**Acceptance Criteria:**
- [ ] New `InstructionEvent` model with trigger conditions
- [ ] Admin UI for configuring event rules per instruction
- [ ] Real-time event matching in passthrough middleware
- [ ] Action execution with proper error handling and logging
- [ ] Event history/audit trail in admin

---

### 5. Create Pub/Sub Topic Browser
**Priority:** Low | **Effort:** 2 days

Admin interface for browsing and managing MQTT/pub-sub topics, subscriptions, and message history.

**Acceptance Criteria:**
- [ ] Topic tree browser with subscription counts
- [ ] Live message feed per topic
- [ ] Publish test message functionality
- [ ] Subscription management (create/delete)
- [ ] Message history search and filtering

---

### 7. Improve Overall Passthrough Performance and Reliability
**Priority:** Medium | **Effort:** 4 days

Systematic performance optimization across all passthrough handlers.

**Acceptance Criteria:**
- [ ] Response caching layer for static assets
- [ ] Connection pooling for upstream requests
- [ ] Streaming response support for large payloads
- [ ] Circuit breaker pattern for failing upstream services
- [ ] Performance metrics dashboard in admin
- [ ] Load testing suite with baseline benchmarks

---

## 📝 To Do

### 6. Fake or Fix Nextcloud Provisioning for Clean Demo
**Priority:** High | **Effort:** 2 days

Resolve Nextcloud provisioning issues to enable clean demo experience. Either fix the provisioning flow or implement a demo-mode fake provisioning.

**Acceptance Criteria:**
- [ ] Option A: Fix real provisioning (SSO, user creation, token management)
- [ ] Option B: Implement demo-mode with pre-configured credentials
- [ ] Clean UI flow from subscription to embedded dashboard
- [ ] No console errors or broken assets in embedded view
- [ ] Documentation updated with known limitations if faking

---

## 🔄 In Progress

### 1. Fix Remaining WebSocket + Dynamic Fetch Escaping in Mattermost Passthrough
**Priority:** High | **Effort:** 1 day (partial)

Resolve edge cases in WebSocket reconnection and dynamic fetch URL escaping that cause intermittent disconnections and API failures.

**Acceptance Criteria:**
- [ ] WebSocket auto-reconnects after network hiccup
- [ ] Dynamic fetch URLs properly escaped for all special characters
- [ ] No memory leaks from reconnection attempts
- [ ] Graceful degradation when upstream is unreachable
- [ ] Integration tests for reconnection scenarios

**Current Status:** Investigating WebSocket heartbeat timeout configuration.

---

### 2. Make AI Chat Widget Fully Functional Inside Mattermost Embedded View
**Priority:** High | **Effort:** 1 day (partial)

Ensure the PolySaaS AI chat dock works seamlessly when Mattermost is embedded via passthrough, with proper API routing and authentication.

**Acceptance Criteria:**
- [ ] Chat dock renders correctly in passthrough context
- [ ] Tenant chat API used (not admin-only endpoint)
- [ ] CSRF tokens properly handled in embedded context
- [ ] Messages send and receive without 403 errors
- [ ] Mobile-responsive layout in embedded view
- [ ] No console errors or failed requests

**Current Status:** Core functionality working; polishing edge cases in mobile layout.

---

### 8. Add AI Peers (Dedicated Bots) with Proper Town Square Integration
**Priority:** High | **Effort:** 2 days (partial)

Complete the AI peers system with Supergrok, Gemini, and Windsurf bots that respond to mentions in Town Square via outgoing webhooks.

**Acceptance Criteria:**
- [ ] All three bots (Supergrok, Gemini, Windsurf) present in Town Square
- [ ] Outgoing webhook correctly routes mentions to AI peers handler
- [ ] Trigger aliases work: `@supergrok`, `@gem`, `@grok`, `@gemini`, `@windsurf`, `@ws`
- [ ] Responses posted back to channel without duplicates
- [ ] No feedback loops between bots
- [ ] Provider tokens properly configured in deployed environment
- [ ] E2E validation passes all 8 checklist items from EOD-2026-05-18

**Current Status:** Code complete; awaiting webhook token configuration and E2E validation.

---

## ✅ Done

*(Completed items will be moved here with completion date)*

---

## 📊 Metrics

| Metric | Value |
|--------|-------|
| Total Cards | 8 |
| Backlog | 5 |
| To Do | 1 |
| In Progress | 3 |
| Review / Testing | 0 |
| Done | 0 |

## 🏷️ Priority Legend

- **High:** Blocks demos, affects core user experience, or is a known regression
- **Medium:** Important for platform completeness but not blocking
- **Low:** Nice-to-have features or polish items

## 📏 Effort Legend

- **1 day:** Small fix or polish
- **2 days:** Feature with moderate complexity
- **3 days:** Feature with multiple components
- **4+ days:** Major feature or system overhaul