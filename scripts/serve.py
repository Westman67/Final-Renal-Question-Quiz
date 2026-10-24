"""Serve this app only on loopback. No uploads, external requests, or dependencies."""
import argparse, functools, http.server, mimetypes, webbrowser, json, urllib.request
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8783);parser.add_argument('--open',action='store_true');parser.add_argument('--bank',choices=['physiology','pathology','both'],default=None);args=parser.parse_args()
launch_url=f'http://127.0.0.1:{args.port}/'+(f'?bank={args.bank}' if args.bank else '')
root=Path(__file__).resolve().parents[1]
mimetypes.add_type('image/webp','.webp');mimetypes.add_type('text/javascript','.js')
try:
    server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)))
except OSError:
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/data/question-bank.json',timeout=2) as response:
            running=json.load(response)
        if running.get('title')!='Renal Visual Questions':raise ValueError('Different service')
        print(f'Renal Visual Questions is already running at http://127.0.0.1:{args.port}')
        if args.open:webbrowser.open(launch_url)
        raise SystemExit(0)
    except (OSError,ValueError):
        raise SystemExit(f'Port {args.port} is busy. Run with --port 8784 to choose another port.')
print(f'Renal Visual Questions at {launch_url}',flush=True)
if args.open:webbrowser.open(launch_url)
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
