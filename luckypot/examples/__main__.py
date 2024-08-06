from pathlib import Path
import importlib.util


def main():
    # Find all examples

    examples = [
        path
        for path in Path(__file__).parent.glob("*.py")
        if not path.name.startswith("_")
    ]

    print("Examples:")
    for i, example in enumerate(examples):
        print(f"{i}. {example.stem}")

    # Ask for the example to run
    example_number = int(input("Enter the number of the example to run: "))
    example = examples[example_number]

    # Import the example
    example_name = example.stem
    spec = importlib.util.spec_from_file_location(example_name, example)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Run the example
    module.main()


if __name__ == "__main__":
    main()