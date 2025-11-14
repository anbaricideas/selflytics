I'm continuing the first incomplete phase of work from the roadmap described in $1

**Step 1: Verify Phase Status**

- Check the roadmap for current phase (marked ⏳ NEXT or IN PROGRESS)
- Read the phase plan document
- Verify prerequisite phases are merged to main (not just "in review")

**Step 2: Understand What to Do**

The phase plan is the **single source of truth**. It contains:
- **Step-by-step checkboxes**: Authoritative task list
- **Session summaries**: Informal notes only (not authoritative)
- **Deliverables**: Files/features to create
- **Success criteria**: Requirements for completion

**If you see contradictory information** (session notes say done, but checkboxes unchecked):
- **Checkboxes are authoritative** - trust them over session notes
- Ask user to clarify if uncertain

Start from: wherever marked as ⏳ NEXT in the phase plan

**Step 3: Implementation Workflow**

For each step in the phase plan:

1. **Update checkbox to in-progress** (if tracking granularly)
2. **Use TDD when developing code**:
   - Write tests first
   - Review with @agent-test-quality-reviewer
   - Revise tests based on feedback
   - Implement code to pass tests
3. **After completing step**:
   - Check the checkbox ✅ in phase plan
   - Commit with @agent-git-commit-helper
   - Update progress in phase plan (DON'T create separate docs)
4. **Follow CLAUDE.md guidelines** (imports at top, PII redaction, etc.)

**Debugging workflow (IMPORTANT - use agents first to avoid rabbit holes)**:

**Use @agent-debug-investigator IMMEDIATELY when:**
- ≥3 tests failing with similar error pattern
- Test failures have unclear root cause
- Multiple theories exist but uncertain which is correct
- Behavior works manually but fails in tests
- Timeout errors without obvious cause
- Any unclear/complex problem that could lead to guessing

**How to use the agent**:
- Provide: error pattern, suspected issue, what you've tried (if anything)
- Don't manually debug first - let agent investigate systematically
- Agent will run tests in headed mode, gather evidence, identify root cause
- Only proceed with fixes AFTER receiving agent's analysis and recommendations

**For e2e test debugging specifically**:
- Check CLAUDE.md "Common Playwright/HTMX Patterns" section first
- May save investigation time if it's a known pattern
- Use @agent-debug-investigator if pattern not listed or unclear

**If you encounter other problems**:
- Ask user if blocked or find contradictory information

**If session context >80% full**:
- Stop work, update phase plan with progress
- Commit changes
- Work can be resumed in new session

**Step 4: Phase Completion Verification**

**BEFORE using @agent-phase-completion-helper**, verify ALL of:

1. ✅ **Every step checkbox** in phase plan is checked (not just session summaries)
2. ✅ **Every deliverable file exists** on filesystem (verify with `find`/`ls`/`grep`)
3. ✅ **All success criteria** checkboxes are checked
4. ✅ **All validation checks pass** (tests, coverage ≥80%, lint, security scan)

**If any verification fails**:
- Mark step status honestly: ❌ NOT DONE, ⚠️ PARTIAL, ✅ DONE
- ASK user: "Steps X-Y incomplete. Should I: (A) complete them, (B) defer them, (C) other?"
- Document user's decision in plan
- **NEVER defer scope without explicit user approval**

**Only when ALL verifications pass**:
- Use @agent-phase-completion-helper to finalize

**Step 5: PR Submission (if phase completes a branch)**

- Use @agent-pr-submission-helper to submit PR
- Do not wait for explicit approval to submit PR
- Note the PR number from the agent's output

**Step 6: PR Review Feedback (user will notify you)**

1. Use @agent-pr-feedback-handler <PR_number> to analyze all comments
2. Let agent run completely - it will ask clarifying questions directly to user
3. After agent returns with action plan, use TodoWrite to track implementation
4. Implement all recommendations from the agent's action plan
5. Commit changes with @agent-git-commit-helper
6. Push to PR branch with `git push`
7. Add explanatory comment to PR using `gh pr comment` documenting what was addressed
