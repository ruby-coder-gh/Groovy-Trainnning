"""
🧮 Calculator Tool

Performs basic arithmetic operations: add, subtract, multiply, divide.

Part 3 of Day 13 — Basic tool with multiple operations.
"""

from typing import Union, Optional

# ──────────────────────────────────────────────────────────────
# Core arithmetic functions
# ──────────────────────────────────────────────────────────────


def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Add two numbers together."""
    return a + b


def subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Subtract b from a."""
    return a - b


def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Multiply two numbers."""
    return a * b


def divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Divide a by b. Returns error message if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


# ──────────────────────────────────────────────────────────────
# Unified calculator dispatcher
# ──────────────────────────────────────────────────────────────

OPERATIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}


def calculate(a: Union[int, float], b: Union[int, float], operation: str) -> Union[int, float]:
    """
    Unified calculator entry point.

    Args:
        a: First number
        b: Second number
        operation: One of "add", "subtract", "multiply", "divide"

    Returns:
        Result of the operation

    Raises:
        ValueError: If operation is unknown or division by zero
    """
    if operation not in OPERATIONS:
        valid = ", ".join(OPERATIONS.keys())
        raise ValueError(f"Unknown operation '{operation}'. Valid: {valid}")

    return OPERATIONS[operation](a, b)


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "calculator",
    "description": "Perform basic arithmetic calculations — add, subtract, multiply, divide",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "First number",
            },
            "b": {
                "type": "number",
                "description": "Second number",
            },
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The arithmetic operation to perform",
            },
        },
        "required": ["a", "b", "operation"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🧮 Calculator Tool Tests")
    print("-" * 40)
    print(f"  45 + 12 = {calculate(45, 12, 'add')}")
    print(f"  100 - 37 = {calculate(100, 37, 'subtract')}")
    print(f"  245 × 88 = {calculate(245, 88, 'multiply')}")
    print(f"  144 ÷ 12 = {calculate(144, 12, 'divide')}")
    print(f"  0 ÷ 100 = {calculate(0, 100, 'divide')}")
    try:
        calculate(10, 0, "divide")
    except ValueError as e:
        print(f"  Division by zero → {e}")
    try:
        calculate(10, 5, "power")
    except ValueError as e:
        print(f"  Unknown op → {e}")
