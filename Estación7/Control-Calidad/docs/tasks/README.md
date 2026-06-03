# 📋 OpenSymphony Task Management

This directory contains the canonical source for all project tasks, milestones, and phases using OpenSymphony contract.

## 📁 Directory Structure

```
docs/tasks/
├── README.md                    (this file)
├── task-package.yaml            (canonical task definition)
├── milestones.md                (milestone timeline)
├── 001-backend-api-wave1.md
├── 002-maestros-wave1.md
├── 003-frontend-wave1.md
├── 004-frontend-wave2.md
├── 005-offline-sync-wave2.md
├── 006-offline-sync-wave3.md
└── linear-sync.log             (generated: Linear sync status)
```

## 📜 OpenSymphony Contract

### Source of Truth: `task-package.yaml`

The `task-package.yaml` file is the **canonical source** for:
- Wave definitions and timelines
- Unit/Phase structure and dependencies
- Milestone definitions and dates
- Team assignments
- Success criteria
- Story point estimation

### Task Files Format: `NNN-unit-wave.md`

Each task markdown file represents a unit's work for a specific wave:

```markdown
# [Unit Name] — Wave [N]

## Overview
- Duration: X days
- Team: N people
- Story Points: X
- Dependencies: [list]

## Phases

### Phase 1: [Name]
- Duration: X days
- Acceptance Criteria:
  - [ ] Criterion 1
  - [ ] Criterion 2
  
### Phase 2: [Name]
...

## Deliverables
- [List of outputs]

## Success Metrics
- [List of metrics]

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
```

## 🔄 Workflow

### 1. **Planning** (Manual)
- Update `task-package.yaml` with:
  - New phases
  - Updated story points
  - Changed dependencies
  - Revised timelines

### 2. **Generation** (Automated)
When ready to sync to Linear:
```bash
# Option A: Using OpenSymphony skills (if available)
# This would run: create-implementation-plan + convert-tasks-to-linear
# Generates individual task files from task-package.yaml

# Option B: Manual generation
# Each task file is created/updated based on task-package.yaml
```

### 3. **Sync to Linear** (Automated)
The `convert-tasks-to-linear` skill syncs:
- Task files → Linear Issues
- Milestones → Linear Cycles/Milestones
- Dependencies → Linear issue relationships
- Acceptance criteria → Issue descriptions

### 4. **Tracking** (Linear)
- Daily: Update task status in Linear
- Weekly: Run sync to pull changes back
- On change: Update `task-package.yaml` → sync again

## 📊 Current Status

### Wave 1 (Jun 1 - Jun 30)
- [ ] Backend API
- [ ] Maestros
- [ ] Frontend Wave 1

### Wave 2 (Jul 1 - Jul 31)
- [ ] Frontend Wave 2 (Analysis)
- [ ] Offline-Sync Wave 2

### Wave 3 (Aug 1 - Aug 31)
- [ ] Offline-Sync Wave 3
- [ ] Production Readiness

## 🚀 Quick Links

- **Milestones**: [milestones.md](milestones.md)
- **Master Plan**: [task-package.yaml](task-package.yaml)
- **Backend Tasks**: [001-backend-api-wave1.md](001-backend-api-wave1.md)
- **Maestros Tasks**: [002-maestros-wave1.md](002-maestros-wave1.md)
- **Frontend Tasks**: [003-frontend-wave1.md](003-frontend-wave1.md)

## 📞 Roles & Responsibilities

| Role | Responsibility |
|------|---|
| **Product Owner** | Approve milestones, prioritize tasks |
| **Tech Lead** | Review phases, verify estimates |
| **Developers** | Update task status in Linear daily |
| **QA Lead** | Define acceptance criteria, verify completion |
| **DevOps Lead** | Milestone ownership (deployment gates) |

## 🔗 Integration with Linear

### Manual Sync to Linear
If skills are not available, manually create Linear issues based on:
1. Copy the task file content
2. Create issue in Linear with:
   - Title: Phase name
   - Description: Task markdown content
   - Estimate: Story points from task-package.yaml
   - Assignee: Team member
   - Cycle: Corresponding wave milestone

### Automatic Sync (When Skills Available)
```bash
# This would be run when OpenSymphony skills are configured
convert-tasks-to-linear --source task-package.yaml --workspace [linear-url]
```

## 📝 Updating Tasks

### If requirements change:
1. Update `task-package.yaml`
2. Regenerate task files (manual or automatic)
3. Sync to Linear (manual or automatic)
4. Notify team of changes

### If scope changes:
1. Update affected task file
2. Update dependencies in `task-package.yaml`
3. Recalculate story points
4. Update milestones if needed
5. Escalate to Product Owner

## ✅ Success Criteria

All milestones complete when:
- [ ] All phases finished with acceptance criteria met
- [ ] Code reviewed and merged
- [ ] Tests passing (>80% coverage minimum)
- [ ] Documentation complete
- [ ] Deployed to staging successfully
- [ ] Linear issue marked "Done"
- [ ] Stakeholders approve

---

**Last Updated**: 2026-06-01  
**Next Review**: 2026-06-07
