#!/usr/bin/env python3
"""Screen capture HTTP server for live monitoring.

Captures the main display using CoreGraphics (works on macOS Sonoma+)
and serves JPEG frames over HTTP. The Mini App polls /frame for live updates.

Endpoints:
    GET /         — MJPEG stream (multipart/x-mixed-replace)
    GET /frame    — Single JPEG frame (for JS polling, iOS-compatible)
    GET /status   — JSON health check

Usage:
    python3 screen_stream.py          # starts on port 9999
    python3 screen_stream.py 8888     # starts on port 8888
"""
import json
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import Quartz
from AppKit import NSBitmapImageRep, NSJPEGFileType
from CoreFoundation import CFDataGetBytes, CFDataGetLength, CFRangeMake

FPS = 10
QUALITY = 0.5
SCALE = 0.5


def capture_jpeg():
    """Capture screen and return JPEG bytes."""
    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectInfinite,
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault,
    )
    if image is None:
        return None

    bitmap = NSBitmapImageRep.alloc().initWithCGImage_(image)

    if SCALE != 1.0:
        w = int(bitmap.pixelsWide() * SCALE)
        h = int(bitmap.pixelsHigh() * SCALE)
        scaled = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, w, h, 8, 4, True, False, Quartz.NSDeviceRGBColorSpace, 0, 0,
        )
        ctx = Quartz.NSGraphicsContext.graphicsContextWithBitmapImageRep_(scaled)
        Quartz.NSGraphicsContext.setCurrentContext_(ctx)
        bitmap.drawInRect_(((0, 0), (w, h)))
        Quartz.NSGraphicsContext.setCurrentContext_(None)
        bitmap = scaled

    props = {Quartz.NSImageCompressionFactor: QUALITY}
    data = bitmap.representationUsingType_properties_(NSJPEGFileType, props)
    length = CFDataGetLength(data)
    buf = bytearray(length)
    CFDataGetBytes(data, CFRangeMake(0, length), buf)
    return bytes(buf)


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/frame":
            self._serve_frame()
        elif self.path == "/status":
            self._serve_status()
        elif self.path == "/":
            self._serve_mjpeg()
        else:
            self.send_error(404)

    def _serve_frame(self):
        """Single JPEG frame — used by Mini App JS polling."""
        jpeg = capture_jpeg()
        if not jpeg:
            self.send_error(503, "Capture failed")
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpeg)))
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(jpeg)

    def _serve_mjpeg(self):
        """Continuous MJPEG stream — works in desktop browsers."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        interval = 1.0 / FPS
        try:
            while True:
                start = time.monotonic()
                jpeg = capture_jpeg()
                if jpeg:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                elapsed = time.monotonic() - start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_status(self):
        """Health check endpoint."""
        body = json.dumps({"status": "ok", "fps": FPS, "scale": SCALE}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
    server = HTTPServer(("0.0.0.0", port), StreamHandler)
    print(f"Screen stream server on http://0.0.0.0:{port}/")
    print(f"  /frame  — single JPEG (for Mini App)")
    print(f"  /       — MJPEG stream (for desktop)")
    print(f"  /status — health check")
    server.serve_forever()


if __name__ == "__main__":
    main()
