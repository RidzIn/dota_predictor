import argparse

from data_processing.models_feedback import update_models_feedback
from data_processing.train_model import evaluate_models, train_xgb_model
from data_processing.winrates_calculator import update_winrates
from parser.parse_match import read_match
from parser.parse_tournament import read_tournament


def main():
    parser = argparse.ArgumentParser(
        description="Scripts for this project"
    )
    parser.add_argument(
        "command",
        choices=[
            "read_tournament",
            "read_match",
            "update_winrates",
            "evaluate_models",
            "train_xgb_model",
            "update_models_feedback",
        ],
        help="The command to execute.",
    )

    parser.add_argument(
        "--file_name", help="The name of the file to read for read_match command."
    )
    parser.add_argument("--file_path", help="File path of your DataFrame file")

    args = parser.parse_args()

    if args.command == "read_tournament":
        read_tournament()
    elif args.command == "read_match":
        if args.file_name:
            read_match(args.file_name)
        else:
            print(
                "Default file name is 'test', you need to provide the '--file_name' argument, in case you want another file name"
            )
            read_match()
    elif args.command == "update_winrates":
        if args.file_path:
            update_winrates(args.file_path)
        else:
            print(
                "Winrates are updating from default file in data/datasets folder. If you want your own file provide '--file_path' argument"
            )
            update_winrates()
    elif args.command == "evaluate_models":
        evaluate_models()

    elif args.command == "train_xgb_model":
        train_xgb_model()

    elif args.command == "update_models_feedback":
        update_models_feedback()


if __name__ == "__main__":
    main()
