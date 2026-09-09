#!/usr/bin/env python3
"""Local dev server for Object Tracker.

    python3 serve.py [port]

Serves this folder over http://localhost:<port>. Defaults to 8777 and walks
upward if that port is taken.

Only needed if you want to load a video by URL (?v=path). Dropping a file onto
the page works from file:// too, since the browser reads it locally.

Implements HTTP Range, which SimpleHTTPRequestHandler does not — without it a
browser cannot seek a served video and scrubbing is unusable.
"""
import functools, http.server, os, socket, socketserver, sys, webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.js': 'text/javascript', '.json': 'application/json',
                      '.png': 'image/png', '.html': 'text/html'}

    def send_head(self):
        """Range support, so <video> can seek instead of refetching the whole file."""
        rng = self.headers.get('Range')
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        try:
            unit, _, spec = rng.partition('=')
            start_s, _, end_s = spec.partition('-')
            size = os.path.getsize(path)
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)
            if unit.strip() != 'bytes' or start > end:
                raise ValueError
        except ValueError:
            self.send_error(416)
            return None
        f = open(path, 'rb')
        f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.end_headers()
        self._range = (start, end)
        return f

    def copyfile(self, source, outputfile):
        rng = getattr(self, '_range', None)
        if not rng:
            return super().copyfile(source, outputfile)
        start, end = rng
        self._range = None
        remaining = end - start + 1
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def end_headers(self):
        # always revalidate — these files are regenerated constantly
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def log_message(self, fmt, *args):
        if '404' in (args[1] if len(args) > 1 else ''):
            sys.stderr.write('  404 %s\n' % (args[0] if args else ''))


def free_port(start):
    for p in range(start, start + 40):
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    raise SystemExit('no free port near %d' % start)


def main():
    want = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    port = free_port(want)
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(Handler, directory=ROOT)
    with socketserver.ThreadingTCPServer(('127.0.0.1', port), handler) as httpd:
        url = f'http://localhost:{port}/'
        print(f'serving {ROOT}\n  {url}')
        for page in ('index.html',):
            if os.path.exists(os.path.join(ROOT, page)):
                print(f'  {url}{page}')
        print('\nCtrl-C to stop')
        if '--no-open' not in sys.argv:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nstopped')


if __name__ == '__main__':
    main()
