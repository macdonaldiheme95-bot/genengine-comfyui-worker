# Genery technique library

The 58 technique slugs on genery.io/effects, grouped by where the effect is
actually made. That grouping matters more than the definition: a video model
can only do what you can describe inside one continuous shot, so an "edit" or
"comp" technique has to be planned as several generated pieces that get
assembled afterwards.

- **prompt**: in-camera; describe it in the generation prompt
- **edit**: happens in the cut; generate the pieces so they join cleanly
- **comp**: layering or post-processing on top of generated footage
- **hybrid**: generate the base move, finish in edit or comp

Look up live examples with `genery.py effect <slug>`. Counts in brackets are
roughly how many example frames genery shows (as of October 2026); a technique with very few
examples gives you less to choose from.

## Contents
- Camera movement
- Point of view and rigs
- Time and speed
- Editing and transitions
- Optics, framing and look
- Compositing, VFX and mixed media
- Shot size and angle tags

## Camera movement

| slug | made in | what it is | commercial use |
|---|---|---|---|
| dolly [100] | prompt | camera tracks toward/away from subject | the default "premium" move: slow push-in on product or face |
| arc [84] | prompt | camera curves around the subject | hero reveal of a car, bottle, or athlete; builds intensity |
| pan [33] | prompt | horizontal rotation from a fixed point | follow action, reveal a second element |
| zoom [57] | prompt | focal length change, camera static | punch-in for emphasis, documentary energy |
| dolly-zoom [39] | hybrid | dolly and zoom in opposite directions (Vertigo effect) | the "realisation" moment; models often fail at it, so plan retries or build it in 3D/post |
| double-dolly [23] | prompt | subject and camera glide together (Spike Lee) | dreamlike walk-and-talk, character floats through a world |
| camera-roll [75] | prompt | rotation on the lens axis | disorientation, energetic fashion and music spots |
| whip-pan [59] | hybrid | very fast pan, motion-blurred | the classic energetic transition; end shot A and start shot B on matching whips, join in the cut |
| fixed-cam [100] | prompt | locked-off, no movement | tableau framing, deadpan comedy, product on plinth |
| locked-on [43] | prompt | camera stays fixed on a moving subject; background moves | car ads (rig shots), running athlete, surreal travel |
| lazy-susan [59] | prompt | subject or camera rotates on a turntable | product spins, fashion turnarounds; models handle "rotates on a turntable, locked camera" well |
| bolt-cam [33] | hybrid | high-speed robotic arm move | food, beverage, product splashes; pair with speed-ramp |
| worms-eye [42] | prompt | extreme low angle looking up | make a product or person monumental |

## Point of view and rigs

| slug | made in | what it is | commercial use |
|---|---|---|---|
| first-person-pov [84] | prompt | camera is the character's eyes | immersive app/game/travel spots |
| object-pov [59] | prompt | camera is an object (inside a fridge, a ball) | playful brand spots, humour |
| snorricam [37] | prompt | rig on the actor's body, actor centred, world swings | intoxication, panic, music videos; models are hit and miss |
| fpv-drone [70] | prompt | agile first-person drone flight | real estate, automotive, sports; models do FPV dives fairly well |
| pass-through [52] | hybrid | camera moves through a wall or object | one-take "impossible" journeys; often stitched from two shots at the occluding object |

## Time and speed

| slug | made in | what it is | commercial use |
|---|---|---|---|
| slow-motion [100] | prompt / edit | slowed action | hair, liquid, fabric, athletes; prompt "slow motion" and/or retime in post |
| fast-motion [100] | edit | sped-up action | time passing, busy routines |
| speed-ramp [89] | edit | speed changes within a shot | sports and car spots; generate continuous action with a clear peak, retime in the editor |
| bullet-time [40] | prompt | frozen moment while camera orbits | product suspended mid-splash; prompt a still subject and an orbit |
| freeze-frame [28] | edit | hold a single frame | title card moments, character intros |
| step-print [16] | comp | repeated frames, strobing slow motion | Wong Kar-wai-style dreaminess |
| echo-print [68] | comp | ghost trails of motion | dance, memory, music videos |
| stop-motion [100] | prompt / comp | frame-by-frame animation | handcrafted, tactile brand stories |

## Editing and transitions

| slug | made in | what it is | commercial use |
|---|---|---|---|
| match-cut [100] | edit | cut between shots with matching shape or motion | product-to-lifestyle links; keep subject position and scale identical across the cut |
| match-motion [100] | edit | movement continues across the cut | seamless montage; outgoing and incoming motion share direction and speed |
| match-split [51] | edit / comp | mirrored or parallel compositions | before/after, two worlds |
| jump-cut [55] | edit | deliberate continuity break | social-first, vlog, youthful energy |
| flash-cut [100] | edit | abrupt short insert | shock, memory, beat hits |
| quick-cuts [100] | edit | rapid montage | sizzle, sports, launch spots; generate many short pieces |
| cut-ins [64] | edit | close detail inserts inside a scene | product details: stitching, buttons, texture |
| light-flash [52] | edit / comp | burst of light as punctuation or transition | beat-synced transitions, reveals |

## Optics, framing and look

| slug | made in | what it is | commercial use |
|---|---|---|---|
| fisheye [42] | prompt | ultra-wide bulging lens | skate, streetwear, hip-hop video |
| color-shift [37] | comp / prompt | palette changes to mark a mood shift | before/after, emotional turn |
| void [100] | prompt | subject in empty black or white space | luxury, minimal product, beauty |
| photography [52] | prompt | stills-style composition in motion | fashion, editorial looks |
| shadow-box [28] | prompt / comp | layered diorama framing | theatrical, playful set pieces |
| double-exposure [35] | comp | two images overlaid | memory, identity, emotional brand films |
| x-ray [14] | comp | x-ray imaging style | showing inside a product |

## Compositing, VFX and mixed media

| slug | made in | what it is | commercial use |
|---|---|---|---|
| split-screen [55] | comp | frame divided into parallel actions | comparisons, two characters, A/B |
| screen-in-screen [78] | comp | multiple screens inside the frame | tech, social, surveillance looks |
| collage [100] | comp | layered photos, textures, illustration | fashion, music, youth brands |
| mixed-media [65] | comp | live action plus animation or drawings | playful explainers |
| datamosh [32] | comp | compression-glitch melts between clips | music videos, edgy launches |
| slit-scan [43] | comp | time-space smear | trippy transitions |
| morphing [16] | prompt / comp | one thing transforms into another | product evolution; first/last-frame video models do this well |
| duplication [100] | comp / prompt | clones of a subject | product range shots, comedy |
| projections [49] | prompt | imagery projected on surfaces or people | music, fashion, tech |
| object-portal [100] | hybrid | passing through a portal to another world | "step into the world of the product" |
| altered-state [29] | comp | hallucinatory distortion | music videos, energy drinks |
| magical-realism [98] | prompt | quiet magic in a real setting | emotional brand films |
| anthropo [19] | prompt | objects or animals given human traits | mascots, playful products |
| conveyor [73] | prompt / comp | looping, repeating motion | routine, manufacturing, satisfying loops |
| photogrammetry [3] | comp | 3D environments built from photos | thin library; use for ideas only |
| wigglegram [3] | comp | two-frame stereo wobble | thin library; social novelty |
| zoetrope [10] | prompt / comp | looping rotating-cylinder animation | retro, handcrafted |

## Shot size and angle tags

Every genery frame carries exactly one of each:

- **Shot size**: Extreme Close Up, Close Up, Medium, Wide, Extreme Wide
- **Angle**: Low, High, Overhead, Over the shoulder

Genery has no tags for eye level, Dutch/canted angle, medium close-up, cowboy,
two-shot, lens, light or colour. Those only come from looking at the still, so
look at every still before you use it as a reference.
