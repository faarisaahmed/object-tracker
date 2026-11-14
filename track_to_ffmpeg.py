#!/usr/bin/env python3
"""Render a track.json from Object Tracker with ffmpeg.

    python3 track_to_ffmpeg.py track.json input.mp4 output.mp4

The in-browser "export video" records the canvas in real time, so it takes as
long as the clip and can drop frames. This rebuilds the same crop as an ffmpeg
filter instead: frame-accurate, no dropped frames, faster than realtime.

The keyframes are {t, x, y} subject centres in source pixels, so the crop is
expressed as x/y expressions in t and interpolated exactly the way the page
does it: "smooth" (a monotone cubic through the keys), "ease each" (smoothstep
per segment) or "linear" -- whichever "motion" was set to on export.

    --height N   output height (default: the JSON's crop height)
    --fps N      output frame rate (default: keep the source's)
    --crf N      quality, lower is better (default 18)
    --print      show the ffmpeg command and filter, run nothing
"""
import argparse, json, os, shlex, subprocess, sys


def tangents(pts):
    """Monotone cubic (Fritsch-Carlson) slopes, identical to tangents() in the page.

    Ends are 0 so the crop holds outside the keyed range; a key where the motion
    reverses also gets 0, so the path never overshoots a keyframe.
    """
    n = len(pts)
    d = [(pts[i + 1][1] - pts[i][1]) / max(pts[i + 1][0] - pts[i][0], 1e-6)
         for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            m[i] = (d[i - 1] + d[i]) / 2
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        al, be = m[i] / d[i], m[i + 1] / d[i]
        s = al * al + be * be
        if s > 9:
            tau = 3 / s ** 0.5
            m[i], m[i + 1] = tau * al * d[i], tau * be * d[i]
    return m


def interp(keys, axis, crop, frame, mode):
    """Nested if() over t giving the crop's leading edge on one axis.

    Keyframes are subject centres, so the edge is centre - crop/2, clamped so
    the box stays inside the frame -- exactly what the page does before drawing.
    """
    edge = lambda k: min(max(k[axis] - crop / 2, 0), frame - crop)
    pts = [(k['t'], edge(k)) for k in sorted(keys, key=lambda k: k['t'])]
    m = tangents(pts) if mode == 'spline' else None
    expr = '%.3f' % pts[-1][1]
    for i in reversed(range(len(pts) - 1)):
        (t0, v0), (t1, v1) = pts[i], pts[i + 1]
        h = max(t1 - t0, 1e-6)
        u = '((t-%.4f)/%.4f)' % (t0, h)
        if mode == 'spline':
            # cubic Hermite written as a polynomial in u
            a, b = h * m[i], h * m[i + 1]
            c2, c3 = 3 * (v1 - v0) - 2 * a - b, 2 * (v0 - v1) + a + b
            seg = '(%.3f+%s*(%.4f+%s*(%.4f+%s*%.4f)))' % (v0, u, a, u, c2, u, c3)
        else:
            if mode == 'ease':
                u = '(%s*%s*(3-2*%s))' % (u, u, u)   # smoothstep, same as the page
            seg = '(%.3f+(%.3f)*%s)' % (v0, v1 - v0, u)
        expr = 'if(lt(t,%.4f),%s,%s)' % (t1, seg, expr)
    expr = 'if(lt(t,%.4f),%.3f,%s)' % (pts[0][0], pts[0][1], expr)
    return 'clip(%s,0,%d)' % (expr, frame - crop)


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
    mode = tr.get('interp')
    if mode not in ('spline', 'ease', 'linear'):   # older exports only had ease
        mode = 'ease' if tr.get('ease', True) else 'linear'

    # even dimensions, or H.264 refuses the frame size
    oh = a.height or chh
    oh -= oh % 2
    ow = round(oh * cw / chh / 2) * 2

    chain = ['crop=w=%d:h=%d:x=\'%s\':y=\'%s\'' % (
        cw, chh, interp(keys, 'x', cw, W, mode), interp(keys, 'y', chh, H, mode))]
    if (ow, oh) != (cw, chh):
        chain.append('scale=%d:%d:flags=lanczos' % (ow, oh))
    if a.fps:
        chain.append('fps=%d' % a.fps)

    cmd = ['ffmpeg', '-y', '-i', a.input, '-vf', ','.join(chain),
           '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf),
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '192k', a.output]

    print('%d keyframes  %dx%d crop  ->  %dx%d  %s' % (
        len(keys), cw, chh, ow, oh, {'spline': 'smooth', 'ease': 'ease each'}.get(mode, mode)))
    if a.dry:
        print('\n' + ' '.join(shlex.quote(c) for c in cmd))
        return
    if not os.path.exists(a.input):
        raise SystemExit('no such input: %s' % a.input)
    sys.exit(subprocess.call(cmd))


if __name__ == '__main__':
    main()
