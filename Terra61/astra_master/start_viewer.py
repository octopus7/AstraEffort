"""Run with Python 3 to open the offline local 3D preview."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import os,webbrowser
os.chdir(Path(__file__).resolve().parent)
server=ThreadingHTTPServer(('127.0.0.1',0),SimpleHTTPRequestHandler)
url=f'http://127.0.0.1:{server.server_port}/web/'
print(url);webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:server.server_close()
