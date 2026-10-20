# Solution — Exercise 01

## What the extras on this branch do

`main` gives you the four steps. This branch adds two things worth having:

- **`--per-turn-delta`** — shows how much each turn *added* to the total,
  which makes the resend cost obvious in a way the cumulative column doesn't.
- **`analysis.py`** — finds the biggest single jump in the conversation and
  tells you which turn caused it. Usually a pasted file, and usually the
  moment the conversation started going wrong.

## What I found

I ran it on the Claude Code session where I was preparing this course's
launch. It was 69 turns long and had about 16k tokens of text in it.

```
  len(text)/4 estimate :    15,982
  actual (API)         :    22,945
  off by               :    +6,963  (+30.3% of actual)

  claude-opus-5 context window: 1,000,000 tokens
  This conversation uses 2.3% of it.
```

**The guess was 30% low, and it was low everywhere.** The session had
almost no code, so I expected the heuristic to do well. It didn't. Turn by
turn, plain prose came out 31–36% under the real count. The best case was a
long bulleted list (24% under). The worst was a reply with Windows file paths
in a code block (44% under). Short messages also did badly: my 60-character
opening message was 39% under, because every message carries a fixed
overhead that `len/4` can't see. Content type mattered less than I expected.
The heuristic was off on everything.

**The biggest jump wasn't anything I pasted.** Turn 25 added 9,710 tokens in
one go, 42% of the whole conversation. It was the environment block the tool
injects: working directory, platform, available tools and skills. Turn 24
(+2,695) was my global instructions file, injected the same way.

**Most of what the model saw, I never typed.** Turns 24–64 are 41
consecutive "user" turns, and none of them were me. They were system
reminders, environment updates, tool and skill lists, MCP servers
connecting and disconnecting, and 25 copies of a `<total_tokens>` counter.
Split by who wrote it:

| Source | Tokens | Share |
|---|---:|---:|
| Context the tool injected | ~18,200 | 79% |
| Model replies | ~4,350 | 19% |
| What I actually typed | ~400 | 2% |

I'd assumed context was *my* conversation. In an agent session, my
conversation was the smallest part of it.

**This is still an undercount.** The loader keeps text blocks only. Tool
calls and tool results (file reads, command output) are dropped, and in an
agent session those are usually the largest items. The session's own system
prompt isn't in the transcript at all. So the real window at the end was
larger than 22,945, and 2.3% is a floor.
