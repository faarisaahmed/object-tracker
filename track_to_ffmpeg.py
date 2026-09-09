#!/usr/bin/env python3
"""Render a track.json from Object Tracker with ffmpeg.

    python3 track_to_ffmpeg.py track.json input.mp4 output.mp4

The in-browser "export video" records the canvas in real time, so it takes as
long as the clip and can drop frames. This rebuilds the same crop as an ffmpeg
filter instead: frame-accurate, no dropped frames, faster than realtime.

The keyframes are {t, x, y} subject centres in source pixels, so the crop is
expressed as x/y expressions in t and interpolated exactly the way the page
does it -- smoothstep when "ease" was on, linear when it was off.

    --height N   output height (default: the JSON's crop height)
    --fps N      output frame rate (default: keep the source's)
    --crf N      quality, lower is better (default 18)
    --print      show the ffmpeg command and filter, run nothing
"""
import argparse, json, os, shlex, subprocess, sys


def interp(keys, axis, crop, frame, ease):
    """Nested if() over t giving the crop's leading edge on one axis.

    Keyframes are subject centres, so the edge is centre - crop/2, clamped so
    the box stays inside the frame -- exactly what the page does before drawing.
    """
    edge = lambda k: min(max(k[axis] - crop / 2, 0), frame - crop)
    pts = [(k['t'], edge(k)) for k in sorted(keys, key=lambda k: k['t'])]
    expr = '%.3f' % pts[-1][1]
    for (t0, v0), (t1, v1) in reversed(list(zip(pts, pts[1:]))):
        u = '((t-%.4f)/%.4f)' % (t0, max(t1 - t0, 1e-6))
        if ease:
            u = '(%s*%s*(3-2*%s))' % (u, u, u)   # smoothstep, same as the page
        seg = '(%.3f+(%.3f)*%s)' % (v0, v1 - v0, u)
        expr = 'if(lt(t,%.4f),%s,%s)' % (t1, seg, expr)
    return 'if(lt(t,%.4f),%.3f,%s)' % (pts[0][0], pts[0][1], expr)


def main():
    p = argparse.ArgumentParser(usage=__doc__.split('\n')[2].strip())
    p.add_argument('track'), p.add_argument('input'), p.add_argument('output')
    p.add_argument('--height', type=int), p.add_argument('--fps', type=int)
    p.add_argument('--crf', type=int, default=18)
    p.add_argument('--print', action='store_true', dest='dry')
    a = p.parse_args()

    with open(a.track) as f:
        tr = json.load(f)
    keys = tr.get('keys') or []
    if not keys:
        raise SystemExit('%s has no keyframes' % a.track)
    cw, chh = int(tr['crop']['w']), int(tr['crop']['h'])
    W, H = int(tr['width']), int(tr['height'])
    ease = bool(tr.get('ease', True))

    # even dimensions, or H.264 refuses the frame size
    oh = a.height or chh
    oh -= oh % 2
    ow = round(oh * cw / chh / 2) * 2

    chain = ['crop=w=%d:h=%d:x=\'%s\':y=\'%s\'' % (
        cw, chh, interp(keys, 'x', cw, W, ease), interp(keys, 'y', chh, H, ease))]
    if (ow, oh) != (cw, chh):
        chain.append('scale=%d:%d:flags=lanczos' % (ow, oh))
    if a.fps:
        chain.append('fps=%d' % a.fps)

    cmd = ['ffmpeg', '-y', '-i', a.input, '-vf', ','.join(chain),
           '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf),
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '192k', a.output]

    print('%d keyframes  %dx%d crop  ->  %dx%d  %s' % (
        len(keys), cw, chh, ow, oh, 'smoothstep' if ease else 'linear'))
    if a.dry:
        print('\n' + ' '.join(shlex.quote(c) for c in cmd))
        return
    if not os.path.exists(a.input):
        raise SystemExit('no such input: %s' % a.input)
    sys.exit(subprocess.call(cmd))


if __name__ == '__main__':
    main()
