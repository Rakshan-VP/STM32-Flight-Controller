from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class PWMHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the request URL
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/connect":
            print("🔗 /connect request received")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")

        elif path == "/send_pwm":
            pwm = {
                'ch1': query.get('ch1', [''])[0],
                'ch2': query.get('ch2', [''])[0],
                'ch3': query.get('ch3', [''])[0],
                'ch4': query.get('ch4', [''])[0],
                'ch5': query.get('ch5', [''])[0],
                'ch6': query.get('ch6', [''])[0],
            }

            print("🎮 PWM received via GET:")
            for key, value in pwm.items():
                print(f"   {key}: {value}")

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            print(f"❌ Unknown GET path: {path}")
            self.send_error(404, "Not Found")

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 5000), PWMHandler)
    print("🚀 PWM HTTP Server running on port 5000 (GET only)...")
    server.serve_forever()
