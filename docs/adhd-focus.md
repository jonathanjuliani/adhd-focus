## What it does

Shapes every reply so a reader with ADHD can act on it. The answer or next action is on the first line, multi-step work is numbered, the reply ends with one next action, and the preamble, recap, tangents, and closing pleasantries are gone. No diagnosis is needed to want it.

Depth is opt-in. Ask for a breakdown and you get a structured shape for that one request: a project brief with 15 to 90 minute tasks, a ranged estimate, an overwhelm sort, a resume note, a work-session plan, or a status, meeting, PR, or weekly-review template. The next reply is lean again.

It is adapted from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT) and extended with executive-function practices.

## When to reach for it

You invoke this by typing `/adhd-focus:adhd-focus`, and the agent will not reach for it on its own. Reach for it at the start of a session when you want answers you can act on rather than read. It stays on until you say "stop adhd mode" or "normal mode".

Pick one of this and caveman, not both. If both are on, the skill says so and follows the one that was on first.

## Asking for depth

Say "break it down", "plan this", "explain", "walk me through", "estimate this", or start a message with `breakdown:`. Portuguese works too: "detalha", "quebra isso", "explica melhor", "planeja". A request for a status update, meeting summary, PR description, or weekly review also counts.

## Common questions

**Does it make the agent think less?**
No. The five-item list cap and the short replies shape what is shown, never what is analyzed, searched, or considered.

**Does it override safety checks?**
No. A destructive action is still confirmed first, and harness rules still win. The shape applies to the prose around them.

**Does it remove the `align-first` reading or the `verify-before-done` proof?**
No. Both stay intact; the next action comes after them.

## Invoking it

A plugin install namespaces the command: `/adhd-focus:adhd-focus` in Claude Code and Cursor, and `@adhd-focus:adhd-focus` in Codex. Installed as files with `npx skills`, the command stays unscoped: `/adhd-focus`.

## It's working if

- Reading only the first and last line of a reply tells you what happened and what to do next.
- No reply opens with "Great question" or ends with "Let me know if".
- A long, structured answer appears only after you asked for one, and the following reply is short again.
- Estimates come as ranges in units, with the biggest unknown named.
