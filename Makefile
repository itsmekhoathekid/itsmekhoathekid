PYTHON ?= python3
GITHUB_USER ?= itsmekhoathekid
QUEST ?=

.PHONY: help metrics render check card quest quest-sync sync

help:
	@printf '%s\n' \
	  'make card                         Preview live metrics in .cache/' \
	  'make quest QUEST="new quest"      Change Current Quest locally' \
	  'make quest-sync QUEST="new quest" Change Current Quest and publish it' \
	  'make sync                         Publish config; Actions updates the live SVG' \
	  'make check                        Validate the local preview'

metrics:
	@GH_TOKEN="$${GH_TOKEN:-$$(gh auth token 2>/dev/null || true)}" \
	  GITHUB_USER="$(GITHUB_USER)" \
	  $(PYTHON) scripts/fetch_github_metrics.py

render:
	bash scripts/render_profile_card.sh .cache/github-terminal-preview.svg

check:
	$(PYTHON) scripts/test_profile_card.py .cache/github-terminal-preview.svg

card: metrics render check

quest:
	@test -n "$(QUEST)" || (printf '%s\n' 'Usage: make quest QUEST="your new quest"' >&2; exit 2)
	$(PYTHON) scripts/update_profile.py current_quest "$(QUEST)"
	@printf 'Current Quest updated. Run `make card` to preview or `make sync` to publish.\n'

quest-sync:
	@$(MAKE) quest QUEST="$(QUEST)"
	@$(MAKE) sync

sync: card
	$(PYTHON) scripts/sync_profile.py
