---
name: Streamlit workflow startup
description: A Replit workflow quirk that affects first-time Streamlit startup.
---

For Streamlit workflows in this workspace, run in headless mode and disable usage statistics so the first-run onboarding email prompt cannot block the process before it opens its port.

**Why:** Without those flags, a fresh Streamlit process can wait for interactive email input and cause the workflow health check to time out.

**How to apply:** Include `--server.headless true --browser.gatherUsageStats false` in the workflow command, along with an explicit bind address when serving the Replit preview.