# Learning Log — Exercise 01: What the model actually sees

**Issue 1 of 30 · Working with the models** · [Read the issue](https://barrosbuilds.com/log) · [All exercises](https://github.com/andrebarros6/learning-log)

**Kind:** script · **Needs:** Python 3.10+, git, an Anthropic API key (separate from a Claude subscription) · **Cost:** free — token counting and model lookup aren't billed

Measure what a conversation actually costs to send, and find out how wrong your mental estimate was.

---

## The theory

Every call to a model is stateless. There's no session on the other side, nothing that persists between requests. Your entire conversation — every message, from the top — is packaged up and sent again, in full, on every turn. The model reads that flat sequence and predicts what comes next. Then it's gone.

The chat interface hides this well. It looks like continuity. It isn't. You're re-submitting a document that grows by two paragraphs each time you hit enter.

Two things follow.

**The unit is the token, not the word.** Text is split into tokens before the model sees it — roughly word-sized, but not reliably. Common words are one token; rare words split into several; whitespace, punctuation and code all tokenize differently from prose. The rule of thumb people repeat — four characters per token — was derived from English prose and breaks precisely where you need it, on code, JSON, tables, and non-English text.

**The window is a shared budget.** System prompt, full history, pasted documents, and the space reserved for the response all come out of one allowance. It doesn't reset between turns.

So long conversations fail two different ways that look identical from outside. **Eviction:** you cross the limit, the oldest content goes, and that's where you set up the task and stated your constraints. **Burial:** well before any limit, an instruction from turn three is competing with forty turns of accumulated noise — technically present, functionally invisible. Burial is why quality degrades noticeably *before* anything breaks.

Once you see it this way the usual fixes stop being folklore. A fresh conversation works because you're rebuilding context deliberately. Restating constraints works because you moved them from turn three to turn forty-one.

## What you'll do

This one is a script you run in a terminal, against the API. That's not a preference: the chat window never shows you a token count, and the API is the only place the real number exists. Not every exercise is like this — about half happen inside Claude or Claude Code.

1. **Count a conversation properly** — real token counts from the API, per turn, not a character heuristic.
2. **Watch the cost grow** — cumulative tokens per turn. The shape is the point: it climbs faster than you'd guess, because every turn resends everything before it.
3. **Compare the guess to the number** — run `len(text)/4` against the real count and measure the gap. If your conversation has code in it, the gap will be worse than you expect.
4. **Find where it broke** — locate the turn where quality dropped, then look at what was in the window at that moment.

## When this is not the right tool

Don't optimise context before you've measured it.

Most problems that look like context problems are prompt problems. A vague instruction produces vague output at turn three or turn thirty, and restructuring your context management to fix an under-specified request is a lot of work for nothing — worse, it teaches you the wrong lesson about what went wrong.

Measure first. If the count is comfortable and the output is still poor, the problem is what you asked, not how much you sent.

---

## Setup

```bash
git clone https://github.com/andrebarros6/learning-log-01-what-the-model-sees
cd learning-log-01-what-the-model-sees
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

You'll need an API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # Windows: set ANTHROPIC_API_KEY=...
```

Never commit your key. `.env` is gitignored.

## Run it

```bash
python -m src.main data/example-conversation.json
```

The example conversation is included so the repo works immediately. It deliberately contains code, so you can see the heuristic fail on the sample before you try your own.

Output looks like:

```
turn  role       this turn     sent  growth
------------------------------------------------------------------------------
   1  user              22       22  █
   2  assistant        118      142  ███
   ...

==============================================================================
The guess vs the number
==============================================================================
  len(text)/4 estimate :       489
  actual (API)         :       ...
  off by               :       ...
```

## Checking your work

```bash
pytest
```

Ten tests covering transcript parsing and the cumulative-counting logic. They use a fake client, so they run without an API key and without spending anything — you shouldn't have to pay to know your parsing works.

That split is itself part of the lesson: test what you can test cheaply, and don't skip testing something because part of the system is remote.

## The solution

```bash
git checkout solution
```

Try it yourself first.

## Bring your own conversation

The example is scaffolding. **The exercise is your own longest working chat** — the one you actually rely on.

Export it and point the script at it:

```bash
python -m src.main path/to/your-export.json
```

`load_transcript` handles a few common export shapes: a plain list of messages, `{"messages": [...]}`, and JSONL. Exports change without warning, so if yours isn't handled, add a branch — that's a legitimate part of the exercise, not a detour from it.

Your own exports are gitignored by default. Don't commit your conversations to a public repo.

---

## A note on the numbers

This exercise deliberately doesn't hardcode context window sizes. They change between model versions, and anything written down goes stale — including anything written here.

`context_window()` asks the API instead. That habit is the durable skill; the current number isn't.

Same reason the code doesn't use `tiktoken`. It's a good library and it's built for a different model family — for Claude it undercounts by roughly 15–20% on typical text, and considerably more on code. A plausible number that quietly disagrees with what you're actually billed is worse than no number.

## Questions, corrections, things that broke

[Discussions on the hub repo](https://github.com/andrebarros6/learning-log/discussions) — one place for all exercises.

Found a step that's gone stale as a tool changed? Open an issue here. Corrections are genuinely welcome; things breaking in public is the format.

## Licence

MIT — see [LICENSE](LICENSE). The exercise is yours to keep.
