# Codex Agent Rules

## Output

Unless the user explicitly asks for another format, reply with JSON as the
response body.

Wrap JSON in a fenced `json` code block so indentation is preserved. Use tab
indentation inside the JSON block.

Default shape:

```json
{
	"goal": "user's goal for this turn",
	"status": "planning | running | blocked | done | failed",
	"current_phase": "understanding | coding | testing | reviewing | waiting_user",
	"summary": "short result or current state",
	"scope": {
		"include": [],
		"exclude": []
	},
	"blocker": {
		"type": "none | missing_info | missing_dependency | permission_denied | tool_failure | validation_failed | unclear_requirement",
		"details": []
	},
	"questions_for_user": [],
	"verification": {},
	"next_step": {
		"owner": "agent | user",
		"action": "next action"
	}
}
```
