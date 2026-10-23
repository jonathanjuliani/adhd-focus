# adhd-focus

A session-long output style for a reader with ADHD. Lean by default: the answer first, no noise, one next action. A structured breakdown only when asked.

Adapted from [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) (MIT).

| Plugin | What it is | Version |
| --- | --- | --- |
| `adhd-focus` | Answer first, no noise, one next action. | 0.1.3 |

## Install

Pick one. A plugin install and `npx skills` together load the skill twice.

Commands for every tool are in [Install](docs/install.md). That is the page an agent should fetch.

### Native plugin

Claude Code:

```text
/plugin marketplace add jonathanjuliani/adhd-focus
/plugin install adhd-focus@adhd-focus
```

Codex:

```bash
codex plugin marketplace add jonathanjuliani/adhd-focus
codex plugin add adhd-focus@adhd-focus
```

Cursor: Customize, then Plugins, then From GitHub Repository, then `https://github.com/jonathanjuliani/adhd-focus`.

GitHub Copilot:

```bash
copilot plugin marketplace add jonathanjuliani/adhd-focus
copilot plugin install adhd-focus@adhd-focus
```

Antigravity, from a clone of this repo:

```bash
agy plugin install ./plugins/adhd-focus
```

Gemini CLI:

```bash
gemini extensions install https://github.com/jonathanjuliani/adhd-focus
```

After a plugin install, start a new session. The command is `/adhd-focus:adhd-focus`.

### Skills only

`npx skills` copies the skill and stays unscoped. The command is `/adhd-focus`.

```bash
npx skills add jonathanjuliani/adhd-focus
```

Devin: `npx skills add jonathanjuliani/adhd-focus -a devin`.

## Update

Update the marketplace, then start a new session. Claude Code: `/plugin marketplace update adhd-focus`, then `/plugin update adhd-focus@adhd-focus`. The other tools are in [Install](docs/install.md). A marketplace user receives a change only after a version bump.

## Release

On a clean `main`, run `python3 scripts/version.py patch` (or `minor` / `major`), then `git push --follow-tags`. The version lives in the harness manifests and moves with the changelog.

## The skill

User-invoked. It stays on until "stop adhd mode" or "normal mode". What it does, and what working looks like: [adhd-focus](docs/adhd-focus.md).

## What a reply looks like

Three generic prompts, each answered twice on 2026-10-16. The skill was loaded only for the right column. The replies did not look at a local project. The counts are words in that reply. The table is the summary. Open a row's section for the full prompt and both replies.

| Prompt | Without the skill | With the skill |
| --- | --- | --- |
| [A non-fast-forward push](#a-non-fast-forward-push) | 172 words. The cause first, then fetch, rebase, and `--force-with-lease`. | 58 words. The command is line one. The last line is the one next action. |
| [A dark mode toggle](#a-dark-mode-toggle) | 401 words. Four sections: theme variables, a preload script, a hook, and the button. | 274 words. The decision and a time range on line one. The last line names one file to create. |
| [Cursor pagination, broken down](#cursor-pagination-broken-down) | 801 words. A day range, then the work split into seven parts and a cut line. | 218 words. Best, likely, and worst, then the one fact that changes the range. |

### A non-fast-forward push

<details>
<summary>Full prompt and replies</summary>

**Prompt**

Why does `git push` fail with "rejected, non-fast-forward", and what should I run?

**Without the skill**

`git push` fails with **rejected, non-fast-forward** when the remote branch has commits your local branch does not. Git will only fast-forward the remote tip when your history already contains that tip. A push that would drop or rewrite those remote commits is refused.

That usually means someone else pushed to the same branch, or you rewrote local history (rebase, amend, reset) after those commits were already on the remote.

Update your branch, then push again:

```bash
git fetch
git pull --rebase
git push
```

`git pull --rebase` replays your local commits on top of the remote ones, so the following push is a fast-forward. If the rebase stops on a conflict, fix the files, then run `git add` on them and `git rebase --continue`.

If you meant to replace the remote history with your rewritten local history, and you are sure nobody else needs the commits you are dropping:

```bash
git push --force-with-lease
```

`--force-with-lease` still refuses the push if the remote moved since your last fetch, which is safer than `--force`.

**With the skill**

Run `git pull --rebase`, then `git push`.

The remote branch has commits your local branch does not. Git rejected the push so those commits stay. A force push can delete them. If the rebase stops on a conflict, leave it and send the file names.

Next: run `git pull --rebase` in the repo. About 1 to 5 minutes.

</details>

### A dark mode toggle

<details>
<summary>Full prompt and replies</summary>

**Prompt**

Add a dark mode toggle to a React app.

**Without the skill**

A dark mode toggle is a class on the document plus CSS variables for the colors. The component only switches that class and remembers the choice.

**1. Define both themes with CSS variables**

```css
:root {
  color-scheme: light;
  --bg: #ffffff;
  --text: #1a1a1a;
  --surface: #f4f4f5;
  --border: #e4e4e7;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0f1115;
  --text: #f4f4f5;
  --surface: #1a1d24;
  --border: #2a2e37;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
}
```

Use `var(--bg)`, `var(--text)`, and the rest everywhere you would have written a color. `color-scheme` tells the browser to paint form controls and scrollbars to match.

**2. Apply the theme before React paints**

Put this script in `index.html`, before the app bundle, so the first paint already has the right theme and there is no flash:

```html
<script>
  (function () {
    var stored = localStorage.getItem("theme");
    var theme =
      stored === "light" || stored === "dark"
        ? stored
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
    document.documentElement.dataset.theme = theme;
  })();
</script>
```

**3. A hook that owns the toggle**

```tsx
import { useCallback, useSyncExternalStore } from "react";

type Theme = "light" | "dark";

function getTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

function subscribe(onStoreChange: () => void) {
  const observer = new MutationObserver(onStoreChange);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
  return () => observer.disconnect();
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getTheme, () => "light" as Theme);

  const toggleTheme = useCallback(() => {
    const next: Theme = getTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
  }, []);

  return { theme, toggleTheme };
}
```

`useSyncExternalStore` keeps every component that reads the theme in sync, because the source of truth is the DOM attribute, not React state.

**4. The button**

```tsx
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? "Light" : "Dark"}
    </button>
  );
}
```

`aria-pressed` tells assistive tech the button is a toggle. The label names the action that will happen, which is the opposite of the current theme.

Drop `<ThemeToggle />` anywhere in the tree. No provider is required: the attribute on `<html>` is the shared state, and the inline script plus `localStorage` keep the choice across reloads. A visitor with no saved choice follows their system setting until they click the button.

**With the skill**

Set `data-theme` on `<html>` from one button, and save the choice in `localStorage`. 15 to 30 minutes. No theme library.

1. Save this as `useTheme.ts` next to the app root.

```tsx
import { useEffect, useState } from "react";

type Theme = "light" | "dark";

function readTheme(): Theme {
  const saved = localStorage.getItem("theme");
  if (saved === "dark" || saved === "light") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(readTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggle() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  return { theme, toggle };
}
```

2. Call the hook once in the header and render the button.

```tsx
const { theme, toggle } = useTheme();

<button type="button" onClick={toggle} aria-pressed={theme === "dark"}>
  {theme === "dark" ? "Use light mode" : "Use dark mode"}
</button>
```

3. Add this to the global stylesheet, and put the script first inside `<head>` in `index.html` so the first paint matches.

```css
:root {
  color-scheme: light;
  background: #fff;
  color: #111;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  background: #111;
  color: #eee;
}
```

```html
<script>
  (function () {
    var saved = localStorage.getItem("theme");
    var theme =
      saved === "dark" || saved === "light"
        ? saved
        : window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
    document.documentElement.dataset.theme = theme;
  })();
</script>
```

After step 3, click the button: the page colors switch and stay after a reload.

`index.html` is the default for Vite or Create React App. A Next.js app needs confirmation: the script goes in the root layout, and `localStorage` cannot run during server render.

Next: create `useTheme.ts` and paste step 1.

</details>

### Cursor pagination, broken down

<details>
<summary>Full prompt and replies</summary>

**Prompt**

Break it down: estimate adding cursor pagination to a REST list endpoint.

**Without the skill**

Adding cursor pagination to one existing REST list endpoint is usually **1.5 to 3 days** for one person who already knows the service. Call it **2 days** if the list is a straightforward filtered query with a stable sort. It stretches toward **4 to 5 days** if the current query is offset-based, the sort is unstable, or clients must keep working during a migration.

That assumes one endpoint, an existing auth model, a relational database, and no new product behavior beyond "return the next page." It does not include redesigning filters, search, or every other list in the API.

**What the work actually is**

**Contract (2 to 4 hours).** Decide the request and response before touching the query. Typical shape: the client sends `limit` plus an opaque `cursor`; the server returns `items`, `next_cursor` (null on the last page), and sometimes `has_more`. Write down whether `cursor` is required, the max `limit`, and what happens when the cursor is expired, malformed, or no longer matches the filters. If the endpoint already uses `page` / `offset`, decide whether both stay for a while or the old params start returning 400.

**Cursor format (2 to 4 hours).** The cursor should be opaque. Base64-encode a small payload of the sort keys from the last row (for example `created_at` + `id`), not an offset. Sign or HMAC it if you do not want clients to forge positions. Do not put raw SQL, internal ids you would not otherwise expose, or filter state the client can already change, unless you intentionally snapshot the filters inside the cursor and reject mismatches.

**Query (4 to 8 hours).** Replace `OFFSET` with a keyset predicate: "rows strictly after this sort position," with the same `ORDER BY` and `LIMIT`. Ties need a unique tiebreaker (`id`, or another unique column) or pages skip and repeat rows. Filters, search, and tenant scope stay in the `WHERE` and must be identical to the query that produced the cursor. This is the part that blows up if the current list is a join, a `DISTINCT`, or an in-memory sort after the database returns rows.

**Index (1 to 3 hours, plus review).** The sort columns plus the tiebreaker need to match an index that also serves the common filters, or the "fix" is slower than offset on large tables. Confirm the plan with a realistic `EXPLAIN` on production-shaped data. Adding the index may be a separate migration with its own deploy risk.

**Edge behavior (2 to 4 hours).** Rows inserted or deleted between requests should not duplicate or skip in a surprising way; document the guarantee you actually provide (stable for a snapshot is harder than "best effort keyset"). Reject cursors when sort, filter, or tenant does not match. Cap `limit`. Return an empty page with `next_cursor: null` rather than an error when the caller is already past the end. Define behavior for a cursor that points at a deleted row: resume from the next key, do not 404 the whole list.

**Tests (4 to 6 hours).** Cover the first page, a middle page, the last page, a page size of 1, the max limit, an invalid cursor, a cursor from another tenant or filter set, duplicate sort keys, and a row that disappears between pages. One integration test that walks until `next_cursor` is null is worth more than many unit tests of the encoder.

**Clients and docs (2 to 4 hours).** Update the API doc and any generated client. If something already pages with offset, ship a compatibility window or a versioned path. Call out that total count is no longer free; if the UI still shows "page 3 of 40," that is a separate, often expensive, `COUNT`.

**What changes the number**

| Situation | Effect |
| --- | --- |
| One table, sort by `(created_at, id)`, index already matches | Low end, about 1.5 days |
| Offset exists and mobile/web clients must move in the same release | Add 0.5 to 1 day |
| Sort is not unique, or ordering happens in application code | Add 0.5 to 1.5 days |
| Several filters combine into different indexes | Add 1 to 2 days |
| You also need exact total count or bidirectional cursors | Add 0.5 to 1 day |
| Every list endpoint in the API, not just one | Multiply, but the second one is cheaper after the cursor helper exists |

A shared cursor helper is worth extracting only if a second endpoint is already in scope. For one endpoint, keep the encoder next to that handler.

**Suggested cut**

Ship forward-only pagination: opaque cursor, `limit`, `next_cursor`, stable `(sort_key, id)` order, and no total count. Leave `prev_cursor` and "jump to page N" out. Those two are what turn a two-day change into a redesign of the list UI.

**With the skill**

**Likely 6 to 10 hours** for one list endpoint. Best **2 to 4 hours**. Worst **3 to 5 days**.

**Estimate**

| Case | Time | Assumes |
| --- | --- | --- |
| Best | 2 to 4 hours | One endpoint. The sort is already a unique indexed key. Callers switch in this change. |
| Likely | 6 to 10 hours | Opaque cursor, keyset query, tests, and the API contract. One pass to check existing callers. |
| Worst | 3 to 5 days | The sort is not unique or not indexed. Filters change the order. Callers keep `offset` and `total`. More than one client. |

These times need confirmation. They assume one person who already knows the endpoint.

**Biggest unknown**

Whether the list sorts by a unique indexed key, and whether any caller still needs `offset` and `total`.

Default if you build now: an opaque cursor of `(created_at, id)`, `next_cursor` null on the last page, the same limit as today, and `offset` and `total` removed. Needs confirmation.

**What shrinks the range**

The sort columns, the index on them, and a yes or no on `total`. That is what separates 2 to 4 hours from 3 to 5 days.

Reply with the sort columns and whether any caller reads `offset` or `total`.

</details>
