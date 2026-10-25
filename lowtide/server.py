from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'/index.html','/web/style.css','/web/app.js','/web/core.mjs',
           '/reports/benchmark/results.json','/reports/benchmark/windows.csv.gz',
           '/reports/benchmark/schedule-journal.csv'}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/':
            path = '/index.html'
        if path not in ALLOWED:
            self.send_error(404)
            return None
        self.path = path
        return super().send_head()

def serve(port=8791):
    with ThreadingHTTPServer(('127.0.0.1',port),Handler) as server:
        print(f'Lowtide: http://127.0.0.1:{port}/',flush=True)
        server.serve_forever()
