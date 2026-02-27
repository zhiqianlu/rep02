def greet(name):
    """
    A simple function that returns a greeting message.
    
    Args:
        name (str): The name of the person to greet
    
    Returns:
        str: A greeting message
    
    Example:
        >>> greet("Alice")
        'Hello, Alice! Welcome!'
    """
    return f"Hello, {name}! Welcome!"


if __name__ == "__main__":
    # Example usage
    print(greet("World"))
    print(greet("Python"))
