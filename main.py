import argparse
from parser.parse_tournament import read_tournament
from parser.parse_match import read_match


def main():
    parser = argparse.ArgumentParser(
        description="Description of your Dota 2 prediction project."
    )
    parser.add_argument(
        "command",
        choices=["read_tournament", "read_match"],
        help="The command to execute.",
    )

    parser.add_argument(
        "--file_name", help="The name of the file to read for read_match command."
    )

    args = parser.parse_args()

    if args.command == "read_tournament":
        read_tournament()
    elif args.command == "read_match":
        if args.file_name:
            read_match(args.file_name)
        else:
            print(
                "Error: For the 'read_match' command, you need to provide the '--file_name' argument."
            )


if __name__ == "__main__":
    main()
