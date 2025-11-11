I'm continuing the first incomplete phase of work from the roadmap described in $1
The roadmap points to a planning document for that phase. You should use that.

Context:

- Check the roadmap for current phase status
- Verify any prerequisite phases are merged (not just "in review")
- If unclear, fetch latest main and check merge status

Guidelines:

- Follow the relevant phase planning document as the single source of truth
- Use TDD when developing code: write tests → review with @agent-test-quality-reviewer → revise tests → implement code to pass
- After each major step:
  1. Update progress in phase planning document (DON’T create separate docs)
  2. Commit with @agent-git-commit-helper
- Follow CLAUDE.md guidelines (imports at top, etc.)
- If non-trivial problems are encountered, use @agent-debug-investigator to investigate
- Ask questions only if blocked or contradictory info found
- If the session context is over 80% full, stop work, update the phase plan, and commit changes, so that work can be resumed in a new session

When phase is complete:

- Use @agent-phase-completion-helper to finalize roadmap and plan documents

If the phase completes a branch that needs to be merged:

- Use @agent-pr-submission-helper to submit PR
- Do not wait for explicit approval to submit PR
- Note the PR number from the agent's output

When PR receives review feedback (user will notify you):

1. Use @agent-pr-feedback-handler <PR_number> to analyze all comments
2. Let agent run completely - it will ask clarifying questions directly to user
3. After agent returns with action plan, use TodoWrite to track implementation
4. Implement all recommendations from the agent's action plan
5. Commit changes with @agent-git-commit-helper
6. Push to PR branch with `git push`
7. Add explanatory comment to PR using `gh pr comment` documenting what was addressed

Start from: wherever marked as ⏳ NEXT
