# SIS ROSE OUTRO — permanent branding (read before every video)

Every TikTok video in this project ends with the **SIS ROSE OUTRO**:

- Component: `compositions/sis-rose-outro.html` (5 s, 1080 × 1920). Mount it as the LAST scene in
  `index.html`, with `data-start` = the end of the video's main content, and raise the root's
  `data-duration` by 5 s. Never change the video's existing content to add it.
- Still version: `renders/sis-rose-outro-poster.png` (the outro's final frame).
- Photo: `assets/brand/sis-rose-original.jpg` is Sis Rose's original photograph. Use it exactly as is:
  never regenerate, beautify, retouch, reshape or replace her face, glasses, hijab or outfit. Only the
  CSS crop/position in the outro may change.
- Layout, top to bottom (do not alter): 288 px circular portrait with a thin champagne-gold ring →
  "Sis Rose" (Playfair Display Bold, deep rose with a champagne-gold edge) → "Ikon Leader Umar
  Jewelleries" (Poppins SemiBold, deep plum) → glossy deep-rose "Follow Sis Rose" button (Poppins Bold,
  white, TikTok icon on the left, curved arrow and pointing hand) → "Real Talk. Real Story." (Poppins
  SemiBold, deep plum) → "Dari Hati ♡" (Playfair Display Italic, deep rose).
- Exact wording and capitalisation as above, never ALL CAPS; "Ikon", not "Icon".
- Look: rose pink / warm ivory gradient, lavender accents, champagne-gold shimmer and delicate sparkles.
- Animation: background fades in → portrait zooms into the centre → gold ring shimmers → "Sis Rose"
  reveal → title → "Follow Sis Rose" soft pop with arrow and hand → tagline → gentle hold to 5 s.
- Sound: soft whoosh (`assets/sfx/outro-whoosh.mp3`) → gold cling (`outro-gold-cling.mp3`) →
  crystal ting (`outro-crystal-ting.mp3`), already synced inside the component.
- No other text, names or logos beyond the lines above.
- All videos are vertical 9:16, 1080 × 1920. No background music unless requested.

# HyperFrames Composition Project

This folder is a [HyperFrames](https://hyperframes.heygen.com) video: HTML, CSS and seekable
animations (GSAP by default) that the `hyperframes` CLI previews in the browser and renders to
MP4.

## Skills — read these first

**Invoke the relevant skill before writing or modifying compositions.** Skills encode framework-specific patterns (e.g., `window.__timelines` registration, `data-*` attribute semantics, shader-compatible CSS rules) that generic web docs don't cover, so compositions written without them break.

**Doing anything with HyperFrames?** Start at `/hyperframes`. Make any video by asking for it; the `/hyperframes` skill carries the contract and the references (each kind of film, story, motion, look, sound, review, captions, overlays). Read it first, especially when there's no project context to orient you.

- `/hyperframes` — read first for any request to make, edit, animate or render a video, motion graphic, captions or overlays. Holds the render contract and the work loop.
- `/hyperframes-cli` — the CLI by job: scaffold, check, look at frames, edit the timeline, preview, render, publish, project history.
- `/hyperframes-registry` — ready-made blocks and components installed as editable source. Search it before hand-building any named visual.
- `/media-use` — get or make any media (music, sound effects, images, voiceover, avatar and generated video, transcripts, cutouts, colour grades) and mix placed audio.
- `/reverse-any-video` — rebuild any video file as an editable HyperFrames project and check it against the original frame by frame (HyperFrames Pro).
- `/style-sampling` — make a new episode on your topic in one of five proven styles (HyperFrames Pro).
- `/figma` — bring a Figma design, frame, logo or brand into a video.
- `/slideshow` — a presentation or pitch deck. Output is a navigable deck, not a rendered MP4.
- `/remotion-to-hyperframes` — bring existing video code or footage into HyperFrames (Remotion first; also Motion Canvas, Lottie, Three.js, canvas, or renders from other tools) and verify it frame by frame against the original.

**Changing how real footage or images look or reveal?** Load `/media-use` and read its `references/media-treatments.md` before editing, even when the request only says dark, flat, boring, retro, private, or “make the reveal cooler.” It governs how footage is treated, never whether media may be used. Use canonical media treatments and seek-safe motion; do not improvise equivalent CSS/SVG filters or overlays.

> **Tailwind v4 projects** (`hyperframes init --tailwind`): see `hyperframes-cli/references/init-and-scaffold.md` (Tailwind).

> **Using a HyperFrames plugin?** Load skills from that installed bundle and follow
> its `hyperframes/references/plugin-installation.md` execution rules. The person updates
> the plugin through its plugin manager; the standalone commands below do not apply.
>
> **Standalone skill missing or stale?** Installing and updating skills is the person's step:
> tell them which skill is missing or stale, and do not run the install yourself. For the user:
> `npx hyperframes skills update <name>` installs/refreshes that skill, and bare
> `npx hyperframes skills update` refreshes the core set plus everything already installed —
> neither pulls the full set. Newly installed skills load in a new agent session.

## Commands

```bash
npm run dev          # human-operated foreground preview (blocks until stopped)
npx hyperframes preview --background  # agent-safe persistent Studio preview
npx hyperframes preview --status      # verify the persistent preview is listening
npx hyperframes preview --stop        # stop it when review is finished
npm run check        # lint + runtime + layout + motion + contrast (one command)
npx hyperframes snapshot --at 1,3,5  # PNG frames at those seconds, to look at before rendering
npm run render       # render to MP4
npm run publish      # publish and get a shareable link
npx hyperframes lint --verbose  # include info-level findings
npx hyperframes lint --json     # machine-readable output for CI
npx hyperframes docs <topic> # reference docs in terminal
```

> **Agents must use `npx hyperframes preview --background` for Studio handoff.** Do not rely
> on a shell/tool `run_in_background` wrapper around `npm run dev`: that foreground process
> remains owned by the invoking session and can disappear while the browser stays open,
> leaving refreshes at `ERR_CONNECTION_TIMED_OUT`. Verify with `preview --status`. The desktop
> app can't edit the project while this preview runs, so `npx hyperframes open` stops it first.
> If you hand the project to the app another way, run `preview --stop` before you do. Otherwise keep it
> alive through review, and stop it explicitly with `preview --stop` afterward.

> **Back from the desktop app.** Once this project was opened in the HyperFrames desktop app, run `npx hyperframes catch-up` before your next change here: it lists what the person asked Framey in the app and which files changed since.

> **Pinned CLI version.** These scripts pin an exact `hyperframes@X.Y.Z` so this project re-renders identically over time. Weeks later that pin lags fixes shipped since. To move up: `npx hyperframes@latest upgrade --project . --check` (shows the delta), then `npx hyperframes@latest upgrade --project .` to rewrite the pins. Always unpinned — the pinned script re-runs the old version against itself.

## Documentation

**For quick reference**, use the local CLI docs command (no network required):

```bash
npx hyperframes docs <topic>
```

Topics: `data-attributes`, `gsap`, `compositions`, `rendering`, `examples`, `troubleshooting`

**For full documentation**, discover pages via the machine-readable index — do NOT guess URLs:

```
https://hyperframes.heygen.com/llms.txt
```

## Project Structure

- `index.html` — main composition (root timeline)
- `compositions/` — sub-compositions referenced via `data-composition-src`
- `meta.json` — project metadata (id, name)
- `transcript.json` — whisper word-level transcript (if generated)

## Linting — ALWAYS RUN AFTER CHANGES

After creating or editing any `.html` composition, **always** run the full check before considering the task complete:

```bash
npm run check
```

Fix all errors before presenting the result. Warnings should be reviewed before rendering.

Then look at what you changed: `npx hyperframes snapshot --at <seconds>` (or `--range START,END`, `--composition <id>`) at the moments you edited, and read the frames before you reply. A passing check does not show how it looks.

## Key Rules

1. Every timed element needs `data-start` and a duration. `data-start` is what marks it as timed; `data-track-index` is an optional Studio display lane the render never reads
2. Give timed visual elements `class="clip"`. The framework keys visibility off `data-start`, not the class, but the shared `.clip` CSS is what gives a scene its full-frame box, and `lint` warns without it
3. Register one paused root timeline per composition on `window.__timelines`:
   ```js
   window.__timelines = window.__timelines || {};
   window.__timelines["composition-id"] = gsap.timeline({ paused: true });
   ```
   Scene timelines manually added to this root must not be paused. A paused
   child does not advance when the root is seeked. The runtime activates
   registered composition siblings, not arbitrary nested scene timelines.
4. A video with sound keeps it on the `<video>` (`data-has-audio="true"`, no `muted`). Use a separate `<audio>` for music, voiceover, replacement audio, J/L cuts, or audio detached in Studio. Silent footage and b-roll: `muted`.
5. Sub-compositions use `data-composition-src="compositions/file.html"` to reference other HTML files
6. Only deterministic logic — no `Date.now()`, no `Math.random()`, no network fetches
