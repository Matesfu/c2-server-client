# Simple C2 Server and Agent

> **Ethical testing only.** This project is an educational command-and-control (C2) for controlled security labs, approved penetration tests, and systems you own or are explicitly authorized to assess. 

Simple C2 Server and Agent is a project that demonstrates a polling-based command-and-control workflow. A Python server registers agents, tracks their recent activity, and queues commands. A Go agent polls the server over HTTP, executes received commands on its own host, and returns the combined output in its next request.

This repository is intended to help contributors study the basic moving parts of a C2-style communication loop, not to provide a production-ready remote administration tool.

## Features

- HTTP-based agent registration and polling
- Per-host, server-issued session identifiers
- In-memory agent records with hostname, status, last-seen time, and queued command
- Interactive server console to list agents and queue a command for one agent or all agents
- Go agent that reports command output back to the server
- Threaded Python HTTP server for handling concurrent requests

## Architecture

```text
Python server (port 8000)                   Go agent
-------------------------                   --------
1. Records hostname and issues an ID  <---  GET / with host-name header
2. Queues a command from the console
3. Validates agent ID and returns command ---> POST / with output from prior command
4. Displays returned output                <--- next polling POST
```

The agent polls every 10 seconds by default. State is held only in memory.

## Requirements

- Python 3.9 or newer
- Go version specified in `go.mod` (or a compatible installed version)
- Python package providing `concurrent_collections.ConcurrentDictionary`

The server uses the third-party `concurrent_collections` module; install the appropriate package for your environment before running it.

## Local lab setup

Run these steps only on a disposable local lab machine or an isolated test network you are authorized to use.

1. Clone the repository and change into its directory.
2. Create and activate a Python virtual environment (recommended).
3. Install the server dependency for `concurrent_collections`.
4. Start the server:

   ```powershell
   python c2_server.py
   ```

5. In a second terminal, build or run the agent:

   ```powershell
   go run c2_implant.go
   ```

By default, the agent connects to `http://localhost:8000`. Keep this default for local testing. If contributors change the endpoint for an approved isolated lab, they must update `baseURL` in `c2_implant.go`, rebuild the agent, and ensure network access is limited to that lab.

## Server console

When the server starts, its console accepts the following commands:

| Command | Description |
| --- | --- |
| `help` | Show available console commands. |
| `agent --list` | List registered agents and their current metadata. |
| `agent --hostname NAME` | Show details for one agent. |
| `agent --hostname NAME --cmd "COMMAND"` | Queue a command for one registered agent. |
| `exit` | Stop the server. |
| `COMMAND` | Queue a command for all registered agents. |


## How it works

1. The agent obtains its hostname and sends a `GET` request with a `host-name` header.
2. The server creates or updates an in-memory host record and returns an identifier in the `Authorization` response header.
3. The agent polls using `POST` requests carrying its hostname, identifier, and output from the previous command.
4. The server verifies the identifier, prints any returned output, and replies with the pending command for that hostname.
5. The agent runs that command, waits 10 seconds, and posts the output during the next poll.

## Contributing

- Document behavioral or protocol changes in the README.
- Test Python and Go changes independently before submitting them.
- Open focused pull requests with a clear description of the change and its security implications.

## Responsible use

By using or contributing to this project, you agree to use it only where you have clear authorization. The maintainers and contributors are not responsible for misuse.

## License

This project is released under the [MIT License](LICENSE).
