# Save this as test_console.py in your project directory
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    console.print(Panel("Testing console interaction", title="Test"))
    project_name = input("Enter project name: ")
    console.print(f"You entered: {project_name}")

if __name__ == "__main__":
    main()