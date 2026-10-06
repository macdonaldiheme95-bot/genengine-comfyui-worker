# From reference to shot recipe to prompt

## Contents
- Reading a still
- The shot recipe
- Writing generation prompts
- This repo's pipeline (GenEngine ComfyUI worker)
- Formats and timing for commercials

## Reading a still

Genery's tags give only shot size, angle and an auto caption. The useful part
of a reference is everything the tags miss, so after opening a still, note:

- **Frame**: true shot size (medium close-up, cowboy, two-shot...), camera
  height vs eyeline, roll or Dutch tilt, aspect ratio.
- **Lens feel**: wide (deep space, stretched edges, ~18-28mm), normal (~35-50mm),
  long (compressed background, ~85mm+); depth of field (deep, shallow,
  split focus); anamorphic cues (oval bokeh, horizontal flares).
- **Composition**: where the subject sits (thirds, centred, edge), headroom and
  lead room, symmetry, negative space, leading lines, frame-within-frame,
  foreground layers.
- **Blocking**: who faces where, eyelines, distance between characters, which
  character dominates the frame and why (height, size, focus, light).
- **Light**: key direction and height, hard or soft, contrast ratio, fill,
  back/rim light, practicals in frame, motivation (window, neon, sun), time of day.
- **Colour**: dominant palette, warm/cool contrast, saturation, black level
  (crushed or lifted), skin rendering.
- **Texture**: grain, haze, smoke, rain, flares, halation, motion blur.
- **Motion** (from the technique tag and clip length, not visible in a still):
  what moves, in which direction, at what speed, and where the move ends.

A reference earns its place by contributing one or two of these clearly.
Say which ones: "lighting and palette from ref 2, blocking from ref 3".

## The shot recipe

Write each shot in this shape. Keep it in your own words: it describes the
technique, never the source footage.

```
### Shot 3 — The reveal (0:08-0:11, 3s)
Beat: what this shot does for the story or the product
Frame: Wide, low angle (~15° below eyeline), slight Dutch left, 2.39:1
Lens: 24mm feel, deep focus, light anamorphic flare
Camera: slow arc right ~45°, ends locked on the bottle
Blocking: model camera-left third, back to lens, bottle on plinth right third
Light: hard backlight through haze, cool fill from left, no front key
Colour: teal shadows, amber highlights, crushed blacks
Texture: drifting haze, fine grain
Technique: arc (genery: /effects/arc), into match-cut to shot 4
Transition out: match-cut on the bottle silhouette
References: 
  - ref A: <Title (Year)>, <shot/angle tags>, https://genery.io/title/<slug>
    (clip 1.0-7.6s) took: haze-backlight and palette
  - ref B: ...
Keyframe prompt: ...
Motion prompt: ...
Post: retime 100%→40% at the peak; grade teal/amber; letterbox 2.39
```

## Writing generation prompts

Write prompts from the recipe, not from the reference. Video models respond to
concrete visual description far better than to "in the style of [film]", and
naming films, directors, actors or brands in a prompt invites likeness and IP
problems in a commercial deliverable.

**Keyframe / text-to-video prompt** order: shot size + angle + lens, subject
and what they're doing, setting, light, colour, texture, mood. One sentence
per idea; specific beats adjectives ("hard backlight through haze" beats
"dramatic lighting").

**Motion prompt** (image-to-video): the starting image already holds the look,
so spend the words on movement. Name one camera move with direction, speed
and end point ("slow dolly in, ends on a tight close-up of the cap"), then the
subject's action and secondary motion (hair, fabric, smoke, liquid). Asking
for two camera moves in one 5s clip usually gets you neither.

**Negative prompt** (where supported): warped hands, extra fingers, text
artifacts, logo distortion, flicker, jitter, sudden cuts, morphing faces.

**Edit-made techniques** (speed-ramp, whip-pan transitions, match-cuts,
quick-cuts, freeze-frame): generate the pieces so they join cleanly. Give the
outgoing and incoming clips matching motion direction, screen position and
scale, and note the join in the Post line.

## This repo's pipeline (GenEngine ComfyUI worker)

The worker in this repo (see Dockerfile/README) runs:

- **Keyframe**: RealVisXL V5 (SDXL) for the still, PuLID for a consistent face
  across shots, ControlNet OpenPose for blocking, IP-Adapter as a fallback for
  identity.
- **Motion**: Wan 2.2 image-to-video at 480p. Plan clips around ~5s per
  generation and cut tighter in the edit.
- **Finish**: 4x-UltraSharp upscale, then edit, retime and grade outside ComfyUI.

So each shot gets a keyframe prompt (SDXL, full look description) and a motion
prompt (Wan, movement only). For blocking with OpenPose, author the pose
yourself (pose a 3D mannequin, photograph a stand-in, or draw the skeleton).
Don't extract poses, depth or edges from genery frames: that's a derivative
use of their footage.

If the user generates elsewhere (Higgsfield, Kling, Veo, Runway, Sora), the
same two prompts carry over. Platforms with named camera-move presets
usually have one matching the genery technique, so mention it.

## Formats and timing for commercials

- **Lengths**: 6s bumper (2-3 shots), 15s (4-7 shots), 30s (8-14 shots), 60s (15-25).
- **Aspect**: 16:9 for TV and YouTube; 9:16 for Reels, TikTok and Shorts; 4:5 for feed; 2.39:1
  letterboxed for a cinematic look. Compose for the delivery ratio, since a 9:16
  crop of a 16:9 composition rarely works.
- **Structure** that works for most spots: hook (first 1-2s must stop the
  scroll), build, product hero, payoff, end card with logo and line.
- **Product hero shots** need clean, readable silhouettes. Good fits: void
  backgrounds, lazy-susan turns, slow dolly-ins, bolt-cam passes and
  bullet-time freezes.
