# Member 2 — TODO: input sanitization / prompt-injection filtering.
#
# Suggested shape:
#
#   def sanitize_input(text: str) -> str | None:
#       """Return cleaned text, or None if the input should be blocked."""
#
# Keep the blocklist/patterns in a config file (like
# backend/agents/nlp_agent/config.json) rather than hardcoded in this
# module, so it can be extended without a code change.
