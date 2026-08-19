PYTHON ?= python3
GITHUB_USER ?= itsmekhoathekid
QUEST ?=

.PHONY: help metrics render check card quest quest-sync sync

help:
	@printf '%s\n' \
	  'make card                         Fetch live metrics and render the SVG' \
	  'make quest QUEST="new quest"      Change Current Quest locally' \
	  'make quest-sync QUEST="new quest" Change Current Quest, render, commit and push' \
	  'make sync                         Refresh metrics, render, commit and push' \
	  'make check                        Validate the generated card'

metrics:
	@GH_TOKEN="$${GH_TOKEN:-$$(gh auth token 2>/dev/null || true)}" \
	  GITHUB_USER="$(GITHUB_USER)" \
	  $(PYTHON) scripts/fetch_github_metrics.py

render:
	bash scripts/render_profile_card.sh

check:
	$(PYTHON) scripts/test_profile_card.py

card: metrics render check

quest:
	@test -n "$(QUEST)" || (printf '%s\n' 'Usage: make quest QUEST="your new quest"' >&2; exit 2)
	$(PYTHON) scripts/update_profile.py current_quest "$(QUEST)"
	@printf 'Current Quest updated. Run `make card` to preview or `make sync` to publish.\n'

quest-sync:
	@$(MAKE) quest QUEST="$(QUEST)"
	@$(MAKE) sync

sync: card
	git add profile.json github-terminal.svg
	@if ! git diff --cached --quiet; then \
	  git commit -m "chore: refresh profile terminal card"; \
	else \
	  printf '%s\n' 'Nothing changed; pushing current branch.'; \
	fi
	git push
