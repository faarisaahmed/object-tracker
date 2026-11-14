# Object Tracker

Reframe a video to a different aspect ratio by keyframing where the subject is.

**[▶ Open it — no install, nothing to sign up for](https://faarisaahmed.github.io/object-tracker/)**

Landscape footage cropped to 9:16 normally means picking one fixed centre and hoping
the subject stays in it. This lets you mark the subject at a few moments; the crop
glides between them, so it follows the action instead of losing it off the side.

Your video never leaves your machine. The page reads the file locally with the
browser's own video decoder — there is no server, no upload, and no account.

## Quick start

1. Open **<https://faarisaahmed.github.io/object-tracker/>**.
2. Drag a video file onto the page (or click **Choose File**). Anything your
   browser can play works — MP4/H.264 is the safe bet.
3. Pick your target shape under **aspect**. It starts on 9:16 vertical.
4. **Drag on the left-hand frame** to put the crop box on your subject. That
   single drag creates your first keyframe. The right-hand panel is the live
   result.
5. Scrub the timeline to a moment where the subject has moved somewhere else,
   and drag on the frame again. That's keyframe two — the crop now travels
   between them on its own.
6. Repeat only at the moments where the motion actually changes direction.
7. Hit **export video** for the reframed clip, or **export json** to render a
   cleaner encode with ffmpeg (see [Export](#export)).

Three or four keyframes is usually a whole clip. You are marking the *corners*
of the movement, not every frame.

Or let it do the work: put the crop on the subject, then hit **auto-track**
(or press **t**). See [Auto-track](#auto-track).

### A worked example

A 20-second clip of someone walking left to right across the frame, going to 9:16:

| At | Do |
|---|---|
| `0:00` | drag the box onto them on the left of frame |
| `0:08` | they've reached the middle — drag the box onto them again |
| `0:15` | they stop on the right — drag once more |

That's it: three keyframes. The crop pans right in step with the walk and holds
still after `0:15`, because the last keyframe extends to the end of the clip.
If the pan feels like it lags behind them, add one keyframe between the two it
lags between — never more than that at a time.

## Auto-track

For subjects that move a lot, such as sport, pets, or anything handheld,
hand-keyframing gets tedious. Auto-track follows the subject for you:

1. Scrub to where you want tracking to start and drag the crop onto the subject.
2. Adjust **target** so the dashed square sits snugly on the subject. It
   should cover mostly subject, with little background.
3. Hit **auto-track** (or **t**). The crop follows live as it goes. **Esc** or
   **stop** ends it early.

It samples the clip 20 times a second and picks one of two ways to find the
subject, based on what's in the dashed square. The status line shows which one
it chose.

- **By colour**, when the subject's colours stand out from the scene: a red
  cloak, a team shirt, a ball. It learns which hues are far more common on the
  subject than around it, then follows that blob. This copes with fast
  motion, pose changes, and lighting shifts. If the subject vanishes, it
  searches the whole frame and picks it up again when it reappears.
- **By pattern**, otherwise. It matches the dashed patch frame to frame and
  checks each match against the subject's original look and its mirror image.
  That stops it from sliding onto static background or a game HUD.

Then it reduces that path to a light set of normal keyframes at the points
where the motion actually bends, so you can fix any of them by hand afterwards. Keyframes before the start point are kept, and so are any after the
point where tracking stopped. Everything in between is replaced. **ctrl+z**
undoes the whole run.

It coasts through short flashes and occlusions. If the subject stays gone for
more than 1.5 s, tracking stops and tells you the time instead of drifting onto
the background. Scrub there,
drag the crop back onto the subject, and track again from that point.

Tracking runs at seek speed rather than playback speed: roughly 2–4× the clip's
length, depending on the machine and the codec. Everything still happens
locally.

## Controls

Everything happens on the video frame and the timeline underneath it.

| Input | Effect |
|---|---|
| **drag on the frame** | set the subject centre at the current time (creates or moves a keyframe) |
| **drag the timeline** | scrub |
| **drag a diamond** | retime that keyframe |
| **click a diamond** | select it and jump there |
| **space** | play / pause |
| **← →** | step back / forward 1/60 s (hold **shift** for ten steps) |
| **k** | add a keyframe at the current time, at wherever the crop already is |
| **⌫** / **delete** | delete the selected keyframe |
| **t** | auto-track from the current time (**esc** stops it) |
| **ctrl/⌘+z** | undo (**shift** to redo, or **ctrl+y**) |

Buttons in the bar do the same jobs: **set keyframe**, **delete**, **clear all**
(resets to a single centred keyframe), **↶ ↷** undo/redo, and the transport
controls.

A keyframe at `t=0` is created for you when the video loads, centred, so the
crop is always defined for the whole clip. Dragging within ~0.04 s of an
existing keyframe edits that one instead of stacking a second on top of it.
The last remaining keyframe can't be deleted.

### Settings

- **aspect** — 9:16, 4:5, 1:1, 16:9, 21:9, or **custom…** for any ratio you
  type. The crop is the largest box of that shape that fits the source, so
  nothing is upscaled at zoom 1.
- **zoom** — 1.00× to 3.00×, shrinking the crop below full fit. At exactly
  1.00× a 9:16 crop of 16:9 footage is full height, so it can only pan
  sideways. Past 1.00× it has room to pan on *both* axes, which is what makes
  this a tracker rather than a horizontal pan.
- **camera**: how closely the camera follows the subject. Keyframes always
  record where the subject *is*; this decides how the camera reacts to it.
  - **calm** (default): like a camera operator. It holds still while the
    subject moves around inside the shot, and pans only when the subject nears
    the edge of a zone around centre. The camera moves ahead of the subject
    instead of lagging behind it.
  - **smooth**: a tighter zone, so it follows more closely but still filters
    out jitter.
  - **steady**: the widest zone, with the least movement. A very fast subject
    can briefly leave the shot.
  - **locked on**: the crop centres exactly on the keyframe path.

  The setting is instant and doesn't touch your keyframes, so switch freely
  after tracking. **export json** includes the finished camera path, which is
  what `track_to_ffmpeg.py` renders.
- **motion**: how the crop travels between keyframes.
  - **smooth** (default): one continuous curve through all the keys. It
    flows through a key when the motion carries on in the same direction,
    and eases to a stop only where the motion reverses or ends. It never
    overshoots a keyframe.
  - **ease each**: eases in and out of *every* keyframe, so the crop briefly
    pauses at each one. This was the behaviour before **smooth** existed.
  - **linear**: constant speed. It reads more mechanical, but it's easier to
    match to a beat.
- **height** — 1920, 1280 (default), 1080, or **native** (the crop's own pixel
  height, no resampling). Width follows from the aspect.
- **fps** — 30 or 60, for the in-browser export.

### Reading the timeline

The timeline draws a filmstrip of the clip so you can find moments by eye, with
the pan curves laid over it: **green is horizontal, pink is vertical**. Flat
means the crop is holding still; sloped means it's moving. A curve only appears
on an axis that actually has room to pan — at zoom 1.00× you'll usually see
green only.

Those curves are the fastest way to spot a mistake. A sharp kink is a lurch, and
a slope where the subject isn't moving means a keyframe is in the wrong place.

## Export

Two paths out, and they produce the same framing.

### export video — quick, no tools

Records the canvas in real time via `MediaRecorder`. It takes as long as the
clip runs and **can drop frames on a busy machine**. Original audio is passed
through. You get MP4 where the browser supports H.264 recording (Chrome, Edge,
Safari) and WebM where it doesn't (Firefox).

Good for a quick look or a short clip. Close other tabs while it records.

### export json + ffmpeg — clean, frame-accurate

`export json` writes `track.json`: the crop geometry plus the raw keyframes.
`track_to_ffmpeg.py` turns that into an ffmpeg render — frame-accurate, no
dropped frames, and faster than realtime:

```sh
python3 track_to_ffmpeg.py track.json input.mp4 output.mp4
```

Needs `ffmpeg` on your PATH (`brew install ffmpeg`, `apt install ffmpeg`) and
Python 3. It rebuilds the crop as an ffmpeg expression in `t`, interpolated the
same way the page does it, matching whatever **motion** was set to when you
exported. Older `track.json` files that only have `"ease"` still work.

```
--height N   output height (default: the crop's native height)
--fps N      output frame rate (default: keep the source's)
--crf N      quality, lower is better (default 18)
--print      show the ffmpeg command and exit, so you can adapt it
```

Use `--print` if you'd rather hand-edit the filter or drive it from another
tool. Auto-tracked clips can have hundreds of keyframes, which is too long for
one command-line argument, so long filters are written to
`<output>.filter.txt` and passed with `-filter_script:v`.

The keyframes are `{t, x, y}` subject centres in source pixels, so the JSON
stays meaningful at any output size. They record where the subject *is*, even
on an axis the crop can't pan. At 9:16 on 16:9 footage, `y` is still the
subject's height in frame. The crop is clamped into the frame only when it's
rendered, so changing zoom or aspect later doesn't lose anything:

```json
{
  "source": "clip.mp4",
  "width": 1920, "height": 1080,
  "crop": { "w": 608, "h": 1080 },
  "aspect": 0.5625, "zoom": 1, "interp": "spline", "ease": true,
  "keys": [
    { "t": 0,     "x": 304,  "y": 540 },
    { "t": 3.5,   "x": 960,  "y": 540 },
    { "t": 8.25,  "x": 1616, "y": 540 }
  ]
}
```

### import json: resume or reuse a track

**import json** (or dropping a `track.json` onto the page) restores the
keyframes, aspect, zoom, and motion setting. Use it to pick up where you left
off, or to apply one track to a different encode of the same footage. If the
video is a different size, such as a half-resolution proxy, the keyframes are
rescaled to fit. If you drop the JSON before the video, it's applied as soon as
the video loads.

## Running it locally

You don't need to — the hosted page is the same single file, and it works
offline once loaded. But if you want to run your own copy:

```sh
git clone https://github.com/faarisaahmed/object-tracker.git
cd object-tracker
python3 serve.py            # http://localhost:8777, opens your browser
```

`index.html` is self-contained with no dependencies and no build step, so
opening it directly from `file://` works too.

The one thing a server buys you is `?v=`, which loads a video straight from
disk instead of dropping it each time — handy for a fixed workflow:

```sh
python3 serve.py            # then visit:
# http://localhost:8777/?v=clips/interview.mp4
```

`serve.py` implements HTTP Range, which Python's `SimpleHTTPRequestHandler`
does not. Without it a browser cannot seek a served video, and scrubbing is
unusable. Pass a port as the first argument (`python3 serve.py 9000`); it walks
upward if that port is busy. `--no-open` skips launching the browser.

## Browser support

| | Editing | export video |
|---|---|---|
| Chrome / Edge | yes | MP4 (H.264) |
| Safari | yes | MP4 (H.264) |
| Firefox | yes | WebM (VP9) |

Chrome is the one to reach for if the export matters. The editor itself is fine
anywhere; on a phone or tablet the drag targets are small but they do work.

## Troubleshooting

**The page says it can't load the video.** The browser can't decode that file —
common with 10-bit HEVC, ProRes, or MKV. Transcode it first:
`ffmpeg -i in.mkv -c:v libx264 -crf 18 -c:a aac out.mp4`

**Scrubbing is choppy on a long or high-bitrate clip.** The browser is seeking
a large file. Keyframe against a smaller proxy, then apply the same
`track.json` to the original with `track_to_ffmpeg.py` — the coordinates are in
source pixels, so make the proxy the *same dimensions* at a lower bitrate:
`ffmpeg -i original.mp4 -crf 30 -c:a copy proxy.mp4`

**export video dropped frames or came out juddery.** Real-time recording
couldn't keep up. Use the ffmpeg path instead — same framing, no dropped frames.

**export video is silent.** The source has no audio track, or the browser
refused to capture it. `track_to_ffmpeg.py` copies the original audio.

**Nothing happens when I drop the file.** Drop it onto the page body, and check
it's a video the browser recognises — the drop handler ignores non-video files.

**Using `?v=` and export produces a black or empty video.** The video is
cross-origin, which taints the canvas and blocks reading pixels back out. Serve
the video from the same origin as the page, or just drop the file in.

**The filmstrip never fills in.** Thumbnails are generated by seeking a hidden
copy of the video, which some codecs stall on. Cosmetic only — everything else
still works.

## License

MIT — see [LICENSE](LICENSE).
