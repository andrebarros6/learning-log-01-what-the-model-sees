# Solution — Exercise 01

> **STATUS: NOT YET RUN.** The code on this branch is complete and its
> offline tests pass, but the findings section below is a placeholder.
> Per the production rule this whole project runs on — do the exercise
> yourself before anyone else sees it — this file must be filled in from a
> real run before issue 1 ships. Do not publish it with the placeholder text.

## What the extras on this branch do

`main` gives you the four steps. This branch adds two things worth having:

- **`--per-turn-delta`** — shows how much each turn *added* to the total,
  which makes the resend cost obvious in a way the cumulative column doesn't.
- **`analysis.py`** — finds the biggest single jump in the conversation and
  tells you which turn caused it. Usually a pasted file, and usually the
  moment the conversation started going wrong.

## What I found

> **[TO WRITE — from your own run.]**
>
> Fill this in after running it against your own longest working chat.
> Specifics that matter:
>
> - the actual gap between `len(text)/4` and the real count, as a percentage
> - what kind of content made the gap worst
> - which turn caused the biggest jump, and what was in it
> - what percentage of the context window the conversation ended up using
> - whether the turn you *remembered* as the moment quality dropped matched
>   what the numbers said
>
> The last one is the most interesting if they disagree. Write what actually
> happened, including if the answer is boring.
