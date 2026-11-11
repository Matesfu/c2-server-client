from typing import Optional
import shlex

def get_agent(user_input, hostname=None):
    if not user_input:
        print("No hosts registered.")
        return

    if hostname is None:
        # Display all agents
        for host, record in user_input.items():
            print(f"\nHostname: {host}")
            print(f"- Status: {record.get('status')}")
            print(f"- Last seen: {record.get('last_seen')}")
            print(f"- Command to send: {record.get('command')}")
        return

    # Display a specific agent
    record = user_input.get(hostname)

    if record is None:
        print(f"Host '{hostname}' not found.")
        return

    print(f"\nHostname: {hostname}")
    print(f"- Status: {record.get('status')}")
    print(f"- Last seen: {record.get('last_seen')}")
    print(f"- Command to send: {record.get('command')}")


def send_command(user_input, command: str, hostname: Optional[str] = None) -> None:
    if not command or not command.strip():
        print("Error: Command cannot be empty.")
        return

    # Case 1: Specific hostname provided -> update only that host
    if hostname:
        if hostname in user_input:
            with user_input.get_locked(hostname) as host_data:
                host_data["command"] = command.strip()
        else:
            print(f"Error: Host '{hostname}' not found.")

    # Case 2: No hostname provided -> broadcast to all hosts
    else:
        for host in list(user_input.keys()):
            if host in user_input:
                with user_input.get_locked(host) as record:
                    record["command"] = command.strip()



def show_help():
    print("""
Available commands:

    help                       Display available commands
    exit                       Stop the application

    agent --list                        List registered devices
    agent --hostname NAME               Show a specific device
    agent --hostname NAME --cmd CMD     Send command to specific User

Examples:

    agent --list
    agent --hostname DESKTOP-001
    help
    exit
""")


def handle_agent_command(args, user_input):
    if not args:
        print("""Usage: agent --list OR agent --hostname NAME OR agent --hostname NAME --cmd CMD""")
        return

    option = args[0].lower()

    if option == "--list":
        if len(args) != 1:
            print("Usage: agent --list")
            return

        get_agent(user_input)

    elif option == "--hostname":
        if len(args) < 2:
            print("""Usage: 
                            agent --hostname NAME
                            agent --hostname NAME --cmd CMD
                            agent --hostname NAME --cmd "CMD"
            """)
            return
        if len(args) == 2:
            get_agent(user_input, args[1])
            return
        option2 = args[2].lower()
        if option2 == "--cmd":
            if len(args) < 4:
                print("""Usage: 
                                agent --hostname Name --cmd CMD 
                                agent --hostname NAME --cmd "CMD"
                """)
                return
            if len(args) == 4:
                command = args[3].lower()
                send_command(user_input, command, args[1])
                return
            elif len(args) == 5:
                command = " ".join(args[3:])
                command = command.lower()
                send_command(user_input, command, args[1])

    else:
        print(f"Unknown agent option: {option}")


def handle_command(server_command, user_input):
    try:
        parts = shlex.split(server_command)
    except ValueError as error:
        print(f"Invalid input: {error}")
        return True

    if not parts:
        return True

    command = parts[0].lower()
    args = parts[1:]

    commands = {
        "help": show_help,
    }

    if command == "exit":
        return False

    elif command == "agent":
        handle_agent_command(args, user_input)

    elif command in commands:
        if args:
            print(f"'{command}' does not accept arguments.")
        else:
            commands[command]()

    else:
        send_command(user_input, server_command)
        print("command sent to all the available agents")

    return True





