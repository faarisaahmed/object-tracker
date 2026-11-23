# Object Tracker

Reframe a video to vertical, square, or any shape, with the crop following the
subject you pick.

**[▶ Open it: no install, nothing to sign up for](https://faarisaahmed.github.io/object-tracker/)**

Cropping landscape footage to 9:16 normally means picking one fixed centre and
hoping the subject stays in it. Here you draw a box around the subject and the
tool tracks it through the clip, moving the crop like a camera operator would.

Your video never leaves your machine. The page reads the file locally with the
browser's own video decoder. There's no server, no upload, and no account.

## Quick start

The steps along the top of the page show where you are. The hint on the video
tells you what to do next.

1. **Open a video.** Drop it on the page, or click **Choose a video**.
   Anything your browser can play works, and MP4 (H.264) is the safe bet.
2. **Select the subject.** Drag a box around the person or thing you want to
   follow. Fit it snugly, so it holds mostly subject and little background.
3. **Track.** Click the **Track** button that appears beside the box, or press
   **T**. The crop follows the subject as it goes, and the timeline shows the
   tracked stretch as a green band.
4. **Export.** Pick a **shape** and **camera** style in the panel, then
   **Export video**. **Save project** keeps your work as a `.json` file, which
   also gives you a frame-perfect render with ffmpeg (see [Export](#export)).

If tracking slips somewhere, go to that moment, box the subject again, and
track from there. Everything before that point is kept. **Ctrl/⌘+Z** undoes a
whole tracking run.

## Selecting the subject

Everything happens on the video:

| On the video | Effect |
|---|---|
| **drag** on empty video | box a new subject, or re-box it at this moment |
| **drag the box** | move the subject at this moment |
| **click** | move the subject here, keeping the box size |

The box does two jobs. Its position says where the subject is, and its size
tells the tracker what to lock onto. It also tells the camera how much room
the subject needs inside the shot. The panel shows a thumbnail of what's
selected.

You can also skip tracking and keyframe by hand. Box the subject at a few
moments where its motion changes direction, and the crop glides between those
points. Three or four is often enough for a simple shot.

## How tracking works

It samples the clip 20 times a second and picks one of two ways to find the
subject, based on what's in the box. The panel shows which one it chose while
it runs.

- **By colour**, when the subject's colours stand out from the scene: a red
  cloak, a team shirt, a ball. It learns which hues are far more common on the
  subject than around it, then follows that blob. This copes with fast
  motion, pose changes, and lighting shifts. If the subject vanishes, it
  searches the whole frame and picks it up again when it reappears.
- **By pattern**, otherwise. It matches the boxed patch frame to frame and
  checks each match against the subject's original look and its mirror image.
  That stops it from sliding onto static background or a game HUD.

It coasts through short flashes and occlusions. If the subject stays gone for
more than 1.5 s, tracking stops and shows the time, with a button to jump
there.

The result is reduced to a light set of keyframes at the points where the
motion bends. On the timeline these appear as a green band, while keyframes
you placed by hand get diamonds.

Tracking runs at seek speed rather than playback speed, so expect roughly
2–4× the clip's length, depending on the machine and the codec.

## Keyboard

| Key | Effect |
|---|---|
| **T** | track / stop (**Esc** stops too) |
| **Space** | play / pause |
| **← →** | step one frame (hold **Shift** for ten) |
| **Home** | go to the start |
| **K** | add a keyframe where the subject box is now |
| **Delete** | delete the selected keyframe |
| **Ctrl/⌘+Z** | undo (**Shift** to redo, or **Ctrl+Y**) |
| **O** | open a video |
| **?** | help |

On the timeline, drag to scrub. Click a diamond to select that keyframe and
jump to it, or drag the diamond to retime it.

## Settings

- **Shape**: 9:16, 4:5, 1:1, 16:9, or **Custom** for any ratio you type. The
  crop is the largest box of that shape that fits the source, so nothing is
  upscaled at zoom 1.
- **Zoom**: 1.00× to 3.00×, shrinking the crop below full fit. At 1.00× a
  9:16 crop of 16:9 footage is full height, so it can only pan sideways. Past
  1.00× it can pan on both axes.
- **Camera**: how the camera follows the subject. Keyframes always record where
  the subject *is*, and this setting decides how the camera reacts.
  - **Calm** (default): like a camera operator. It holds still while the
    subject moves around inside the shot, and pans only when the subject
    nears the edge of a zone around centre. It moves ahead of the subject
    instead of lagging behind.
  - **Smooth**: a tighter zone. It follows more closely but still filters out
    jitter.
  - **Steady**: the widest zone, with the least movement. A very fast subject
    can briefly leave the shot.
  - **Locked**: the crop centres exactly on the subject.

  Switching is instant and doesn't touch your keyframes.
- **Motion between keyframes** (under Keyframes):
  - **Smooth** (default): one continuous curve through the keys, which never
    overshoots.
  - **Ease**: slows into and out of every keyframe.
  - **Linear**: constant speed.
- **Height** and **Frame rate**: output size and frame rate for the in-browser
  export. **Native** uses the crop's own pixel height, with no resampling.

The timeline draws the camera's path over a filmstrip of the clip, in white
for horizontal and amber for vertical. Flat means the camera is holding still,
and a slope means it's panning.

## Export

Two paths out, and they produce the same framing.

### Export video: quick, no tools

Records the canvas in real time via `MediaRecorder`. It takes as long as the
clip runs and **can drop frames on a busy machine**. Original audio is passed
through. You get MP4 where the browser supports H.264 recording (Chrome, Edge,
Safari) and WebM where it doesn't (Firefox).

Good for a quick look or a short clip. Close other tabs while it records.

### Save project + ffmpeg: clean, frame-accurate

**Save project** writes a `.json` file named after your video. It holds the
crop geometry, the keyframes, and the finished camera path.
`track_to_ffmpeg.py` turns that into an ffmpeg render that's frame-accurate,
has no dropped frames, and runs faster than realtime:

```sh
python3 track_to_ffmpeg.py track.json input.mp4 output.mp4
```

Needs `ffmpeg` on your PATH (`brew install ffmpeg`, `apt install ffmpeg`) and
Python 3. It rebuilds the crop as an ffmpeg expression in `t`, interpolated the
same way the page does it. When the project includes a camera path (any
camera style but **Locked**), it renders that path exactly. Older `track.json`
files that only have `"ease"` still work.

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

### Open project: resume or reuse a track

**Open project** (or dropping a project `.json` onto the page) restores the
keyframes, subject box, shape, zoom, camera, and motion settings. Use it to pick up where you left
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
