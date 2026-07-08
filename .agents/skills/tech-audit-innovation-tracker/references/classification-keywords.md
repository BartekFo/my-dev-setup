# Classification Keywords Reference

Use these keyword lists to auto-classify work items when explicit labels aren't available.
Match against project names, epic titles, task descriptions, and any tags/labels.

## Maintenance Keywords

### High Confidence (almost certainly maintenance)
- bug, bugfix, hotfix, defect, incident
- patch, security patch, CVE, vulnerability
- upgrade, version upgrade, dependency update
- compliance, audit, regulatory, SOX, GDPR remediation
- backup, disaster recovery, DR test
- monitoring, alerting, health check
- license renewal, subscription renewal
- support ticket, helpdesk, service request
- infrastructure maintenance, server maintenance
- performance tuning (existing systems)
- tech debt, technical debt, refactor (existing)
- EOL, end of life, decommission
- SLA, uptime, availability

### Medium Confidence (likely maintenance, verify context)
- migration (could be strategic — check if forced or chosen)
- optimization (existing system vs new capability)
- testing (regression vs new feature)
- documentation (existing vs new)
- training (on existing tools vs new platform)
- integration fix, sync issue

## Innovation Keywords

### High Confidence (almost certainly innovation)
- new feature, new functionality, new capability
- new product, new service, new platform
- greenfield, net-new, from scratch
- proof of concept, PoC, prototype, MVP
- R&D, research, experiment
- AI, ML, machine learning, automation (new)
- digital transformation, modernization (strategic)
- new integration, new API, new connector
- UX redesign, UI overhaul (strategic)
- new market, expansion, growth initiative
- analytics platform, data lake (new build)
- customer-facing (new)
- revenue-generating (new)

### Medium Confidence (likely innovation, verify context)
- platform migration (strategic choice vs forced)
- cloud migration (strategic transformation vs version end)
- redesign (strategic vs cosmetic)
- process improvement (new automation vs fixing broken process)
- dashboard (new analytics vs fixing existing)

## Ambiguous — Always Ask User
- "migration" without context
- "improvement" without context
- "update" (feature update vs security update)
- "integration" (new vs fixing existing)
- "optimization" (new capability vs keeping existing alive)
- "automation" (new initiative vs maintaining existing automation)

## Classification Decision Tree

```
1. Does the item have an explicit type/label?
   → Yes: Use it (bug=maintenance, feature=innovation)
   → No: Continue to 2

2. Does the item name match HIGH CONFIDENCE keywords?
   → Yes: Classify accordingly
   → No: Continue to 3

3. Does the item name match MEDIUM CONFIDENCE keywords?
   → Yes: Classify with a flag for user review
   → No: Continue to 4

4. Does the item description give context?
   → Yes: Use judgment, flag if unsure
   → No: Default to MAINTENANCE (conservative)
```
