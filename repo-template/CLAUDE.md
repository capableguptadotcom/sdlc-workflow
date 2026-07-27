<!-- ai-sdlc:workflow:start -->
@AGENTS.md

# Claude adapter

The canonical skill implementations are under `.agents/skills/`.
`.claude/commands/` contains thin invocation adapters only. Follow the canonical
skill named by an adapter and resolve its relative references from that skill's
directory. Do not add behavior to an adapter; change the canonical skill and
its evaluation instead.
<!-- ai-sdlc:workflow:end -->
