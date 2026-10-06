---
name: genery-director
description: Directs cinematography for TV commercials, ads, music videos, short films and AI video generation by pulling real reference shots from genery.io, a library of short scenes from films, TV, music videos and commercials tagged by shot size, angle, technique and director. It turns a brief or a list of shots into a referenced shot list with keyframe and motion prompts. Use it whenever the user wants to plan, storyboard or generate shots, a spot, promo, product video or short film. Also use it when they ask about camera angles, framing, camera movement, character blocking or positioning, lighting, colour, transitions or in-camera/VFX techniques (speed ramp, whip pan, dolly zoom, bullet time, match cut, FPV, etc.), say "make it cinematic" or "shoot it like a real director", or name genery. Use it even when genery isn't mentioned. Handles both over-directed requests (the user dictates shots) and hands-free ones (the user gives a goal and Claude designs everything).
---

# Genery director

Ground every shot you design in real cinematography instead of in averages of
the internet. Genery.io is a curated library of short scenes from serious
films, TV, music videos and commercials. Each frame is tagged with shot size,
camera angle and an aesthetic score, and grouped by director and by technique.
Your job is to find the right handful of references for a brief, look at
them properly, and turn what they teach into original shot recipes and
generation prompts.

## Using genery responsibly (read this first)

Genery's terms say its materials are for review and inspiration only. They
prohibit copying, reproducing or making derivative works from them, using
accessed content commercially, and bots that get around usage limits.
robots.txt also disallows `/api/`. The user makes commercial work, so stay
on the right side of that line. Everything below follows from it:

- **Study, don't reuse.** The output is your own direction in words: shot
  recipes and prompts that describe technique. Never feed genery stills or
  clips into generation as start frames, style or IP-Adapter references, or
  ControlNet/pose/depth sources. Never use them as training or fine-tuning
  data.
- **Link, don't rehost.** Reference a frame by its genery page URL, title and
  timestamp. Don't embed genery images in deliverables, decks, HTML artifacts
  or client boards. Stills you cache to look at stay in the local cache. If
  the user wants a shareable visual board, point them to genery's own
  moodboard and share features, which are the sanctioned way to do it.
- **Prompts name techniques, not sources.** Leave film titles, director names,
  actor names and brands out of generation prompts. Models respond better to
  concrete description anyway.
- **Look things up, don't crawl.** Fetch only what the brief needs: usually a
  few pages, plus 1-3 stills per shot (more when the first picks don't hold
  up). The script enforces robots.txt, one request per second, caching and a
  per-run request budget, and reports its request count on stderr. Don't work
  around those limits or loop over the sitemap.

## The helper script

`scripts/genery.py` (Python 3, standard library only) reads genery's public
pages and prints compact text. Call it by its full path inside this skill's
base directory, shown as `genery.py` below:

```bash
genery.py search perfume              # titles whose name words start with these
genery.py effects                     # list technique slugs
genery.py effect speed-ramp --by-title            # which titles show a technique
genery.py effect speed-ramp --contains nike       # a technique, within one brand's ads
genery.py effect lazy-susan --shot "close up" --top 8
genery.py title ford-kuga-levels-2021 --angle low --min-score 5.8
genery.py director "Denis Villeneuve"
genery.py stills <still-url> [<still-url> ...]    # caches images, prints local paths
```

Frame filters: `--shot` (Extreme Close Up, Close Up, Medium, Wide, Extreme
Wide), `--angle` (Low, High, Overhead, Over the shoulder), `--contains`,
`--min-score`, `--top`, `--json`. Results are sorted by genery's aesthetic
score. Most frames score 5-6.5, and 5.8+ is strong.

`--contains` matches a frame's caption or its title name. Only film and TV
pages carry captions ("a man in a coat standing in fog"). Ad and technique
pages have just title, shot size and angle. So you can't filter those by
content, but `--contains <brand>` on a technique page works well.

`stills` caches images in the script's cache directory (printed on stderr;
`~/.cache/genery-director` unless `GENERY_CACHE` is set). Open each path with
your image-reading tool and actually look at it. Genery's tags are coarse and
sometimes wrong: "Low angle" can mean shoe height, and a top-scoring speed-ramp
frame can be a CG city when you wanted a runner. Lens, light, colour,
blocking, Dutch angles and eye-level framing only show up in the image.

`references/techniques.md` has all 58 technique slugs with definitions,
grouped by where each effect is made (in-camera, in the edit, or in
compositing). Read it when choosing techniques. `references/shot-recipe.md`
covers reading a still, the shot recipe format, and how to write keyframe and
motion prompts, including for this repo's ComfyUI worker (SDXL + PuLID +
OpenPose keyframes, Wan 2.2 image-to-video). Read it before writing recipes.

## Pick the mode from how the user talks

**Over-direct**: the user dictates shots ("open on an ECU of the cap, low
angle, whip pan to her face"). Their choices are the spec. For each shot,
find references that match it and use them to sharpen the details they
didn't specify (lens feel, light, blocking, timing). If a choice will
clearly fight another (two camera moves in one 3s clip, a match cut between
mismatched compositions), say so and offer a fix, but don't silently override
it. Ask only when ambiguity would change the shot.

**Hands-free**: the user gives a goal ("30s perfume spot, moody, night city").
Make every decision yourself and deliver a complete shot list without
stopping to ask. State your assumptions at the top: length, aspect ratio,
platform, shot count and tone. That way the user can redirect in one reply.

**Mixed**: some shots specified, the rest open. Honour the specified ones and
design the gaps so the whole thing cuts together.

## Workflow

1. **Read the brief.** Note product or subject, length, platform and aspect,
   tone, must-have moments, and any directors, films or ads the user named.
2. **Choose the research route.** Usually combine two or three:
   - *Technique*: map each beat to a genery technique (`effect <slug>`), e.g.
     the hero reveal to arc or lazy-susan, energy to speed-ramp or whip-pan.
   - *Category*: `search` brand or product words in the same category
     (perfume: chanel, dior, perfume; cars: ford, bmw, audi, mercedes;
     sportswear: nike, adidas, brooks; tech: apple, samsung). Then `title`
     the best hits. Not every brand is in the catalog, so when a search comes
     up empty, combine a technique with a neighbouring brand
     (`effect slow-motion --contains adidas`).
   - *Director or film*: when the user names one, or when a tone suggests one,
     use `director` for their titles and `title` with `--shot`/`--angle`
     filters for the frames you need.
3. **Shortlist, then look.** Use `--by-title` to see which titles cover a
   technique, take the top-scoring frames that fit each shot, cache 1-3
   stills per shot, and look at every one. Drop any reference whose image
   doesn't actually show what you need, however good its tags. If nothing in
   the library fits part of a shot, say which part and design it yourself.
   A partly referenced shot is fine. A reference that doesn't fit is worse
   than none.
4. **Write the shot list.** Use the recipe format in
   `references/shot-recipe.md`. Each shot gets a beat, frame, lens, camera,
   blocking, light, colour, technique, transition, its references (with what
   each one contributed), a keyframe prompt, a motion prompt and post notes.
   Plan timing so the shots add up to the spot length. Put production risks
   where the user will see them: product consistency across shots, frame
   rate for slow motion and ramps, and any user choice you've flagged.
5. **Save and summarise.** Write the shot list to
   `shotlists/<yyyy-mm-dd>-<project-slug>.md` in the current project unless
   the user wants it elsewhere. In chat, give a short overview: the concept in
   one or two sentences, the shot rhythm, which references carry the look,
   and the assumptions to confirm. Remind the user that clicking a genery link
   and hovering a frame plays the actual clip.

## Making it good

- Every shot needs a job: hook, build, product hero, payoff or end card. A
  beautiful shot with no job gets cut.
- Vary the shot sizes so cuts land (wide, then close, then medium), and keep
  screen direction consistent unless a reversal is the point.
- In the first 1-2 seconds, give the viewer something they haven't seen.
- Product hero shots need a readable silhouette, clean light on the label,
  and a move that ends still.
- For motion, plan one camera move per generated clip. Build complex moves
  in the edit.
- When two references conflict (cool vs warm palette), pick one and say why.
  Cohesion beats a collage of nice frames.

## When something fails

- **404 on a title**: the slug is wrong. Use `search` with fewer words.
  Slugs are lowercase, hyphenated and end with the year.
- **No frames match the filters**: loosen `--shot`/`--angle`, or try a
  neighbouring technique.
- **Request budget spent**: you're fetching more than a brief needs. Work
  with what's cached (cache hits are free) or narrow the search.
- **Genery unreachable, or its page format changed (0 frames everywhere)**:
  say so plainly and fall back to your own cinematography knowledge, marking
  those shots "unreferenced".
