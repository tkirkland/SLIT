# Python Style Guide

This style guide follows Google's Python Style Guide with best practices for writing clean, maintainable Python code.

## Table of Contents

- [General Guidelines](#general-guidelines)
- [Code Formatting](#code-formatting)
- [Imports](#imports)
- [Naming Conventions](#naming-conventions)
- [Documentation](#documentation)
- [Language Features](#language-features)
- [Type Annotations](#type-annotations)
- [Error Handling](#error-handling)

## General Guidelines

### Code Quality Tools

- Use **Black** or **Pyink** auto-formatter to avoid formatting debates
- Run **pylint** over your code using the provided pylintrc
- Enable Python type analysis when updating code

### Line Length

- Maximum line length is **80 characters**
- Use implicit line joining inside parentheses, brackets, and braces
- Avoid backslash line continuation (except in strings)

```python
# Yes
foo_bar(self, width, height, color='black', design=None, x='foo',
        emphasis=None, highlight=0)

# Yes
if (width == 0 and height == 0 and
    color == 'red' and emphasis == 'strong'):

# No
if width == 0 and height == 0 and \
    color == 'red' and emphasis == 'strong':
```

## Code Formatting

### Indentation

- Use **4 spaces** for indentation (never tabs)
- Align wrapped elements vertically or use hanging 4-space indent

```python
# Yes - aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Yes - 4-space hanging indent
foo = long_function_name(
    var_one, var_two, var_three,
    var_four)
```

### Whitespace

- No whitespace inside parentheses, brackets, or braces
- No whitespace before commas, semicolons, or colons
- Surround binary operators with single spaces
- No trailing whitespace

```python
# Yes
spam(ham[1], {'eggs': 2}, [])
if x == 4:
    print(x, y)

# No
spam( ham[ 1 ], { 'eggs': 2 }, [ ] )
if x == 4 :
    print(x , y)
```

### Blank Lines

- Two blank lines between top-level definitions
- One blank line between method definitions
- Single blank lines as appropriate within functions

## Imports

### Import Style

```python
# Yes
import os
import sys
from typing import Any, NewType

# No
import os, sys
```

### Import Order

1. Python future import statements
2. Python standard library imports
3. Third-party module imports
4. Code repository sub-package imports

```python
from __future__ import annotations

import os
import sys

import tensorflow as tf

from myproject.backend import huxley
```

### Import Guidelines

- Use `import x` for packages and modules
- Use `from x import y` where x is package prefix and y is module name
- Use `from x import y as z` when needed to avoid conflicts
- Use full package names (avoid relative imports)

## Naming Conventions

| Type | Public | Internal |
|------|--------|----------|
| Packages | `lower_with_under` | |
| Modules | `lower_with_under` | `_lower_with_under` |
| Classes | `CapWords` | `_CapWords` |
| Exceptions | `CapWords` | |
| Functions | `lower_with_under()` | `_lower_with_under()` |
| Global/Class Constants | `CAPS_WITH_UNDER` | `_CAPS_WITH_UNDER` |
| Global/Class Variables | `lower_with_under` | `_lower_with_under` |
| Instance Variables | `lower_with_under` | `_lower_with_under` |
| Method Names | `lower_with_under()` | `_lower_with_under()` |
| Function/Method Parameters | `lower_with_under` | |
| Local Variables | `lower_with_under` | |

### Naming Guidelines

- Names should be descriptive
- Avoid abbreviations
- Use descriptive names proportional to scope of visibility
- Internal items use single underscore prefix (`_internal`)
- Avoid double underscore (`__dunder`) names

## Documentation

### Docstrings

Use triple-quoted strings (`"""`) for all docstrings:

```python
def fetch_data(table_handle: Table, keys: Sequence[str]) -> Mapping[str, tuple]:
    """Fetches rows from a table.
    
    Retrieves rows pertaining to the given keys from the Table instance.
    
    Args:
        table_handle: An open table instance.
        keys: A sequence of strings representing row keys to fetch.
        
    Returns:
        A dict mapping keys to the corresponding table row data.
        Each row is represented as a tuple of strings.
        
    Raises:
        IOError: An error occurred accessing the table.
    """
```

### Module Docstrings

```python
"""A one-line summary of the module or program, terminated by a period.

Leave one blank line. The rest of this docstring should contain an
overall description of the module or program. Optionally, it may also
contain a brief description of exported classes and functions.

Typical usage example:
    foo = ClassFoo()
    bar = foo.function_bar()
"""
```

### Comments

- Use comments for tricky parts of code
- Comments should be complete sentences with proper punctuation
- Inline comments should be at least 2 spaces away from code

```python
# We use binary search to find the position efficiently.
if i & (i-1) == 0:  # True if i is 0 or a power of 2.
```

## Language Features

### String Formatting

Use f-strings, `%` operator, or `format()` method:

```python
# Yes
x = f'name: {name}; score: {n}'
x = '%s, %s!' % (imperative, expletive)
x = '{}, {}'.format(first, second)

# No
x = 'name: ' + name + '; score: ' + str(n)
```

### Boolean Expressions

Use implicit false when possible:

```python
# Yes
if foo:
if not users:
if foo is None:

# No
if foo != []:
if len(users) == 0:
if foo == None:
```

### Default Arguments

Don't use mutable objects as default values:

```python
# Yes
def foo(a, b=None):
    if b is None:
        b = []

# No
def foo(a, b=[]):
    ...
```

### Comprehensions

Keep comprehensions simple:

```python
# Yes
result = [mapping_expr for value in iterable if filter_expr]

# No - too complex
result = [(x, y) for x in range(10) for y in range(5) if x * y > 10]
```

### Exception Handling

```python
# Yes
try:
    value = collection[key]
except KeyError:
    handle_missing_key(key)

# No - too broad
try:
    value = collection[key]
except:
    handle_missing_key(key)
```

## Type Annotations

### Basic Annotations

```python
def func(a: int, b: str = 'default') -> list[int]:
    return [a] * len(b)

# Variable annotation
count: int = 0
```

### Complex Types

```python
from collections.abc import Mapping, Sequence
from typing import Any, Union

def process_data(
    data: Sequence[dict[str, Any]],
    config: Mapping[str, str] | None = None,
) -> list[str]:
    ...
```

### Type Aliases

```python
from typing import TypeAlias

_LossAndGradient: TypeAlias = tuple[tf.Tensor, tf.Tensor]
ComplexMapping: TypeAlias = Mapping[str, _LossAndGradient]
```

### Generic Types

```python
from typing import TypeVar

T = TypeVar('T')

def get_first(items: list[T]) -> T | None:
    return items[0] if items else None
```

## Error Handling

### Exception Guidelines

- Use built-in exception classes when appropriate
- Don't use `assert` for validating preconditions in production code
- Custom exceptions should inherit from existing exception classes
- Exception names should end in "Error"

```python
# Yes
if minimum < 1024:
    raise ValueError(f'Min. port must be at least 1024, not {minimum}.')

# No
assert minimum >= 1024, 'Minimum port must be at least 1024.'
```

### Resource Management

Use context managers for resource management:

```python
# Yes
with open("hello.txt") as hello_file:
    for line in hello_file:
        print(line)

# For resources without context manager support
import contextlib
with contextlib.closing(urllib.urlopen("http://example.com/")) as page:
    for line in page:
        print(line)
```

## Main Guard

Always use the main guard pattern:

```python
def main():
    # Main program logic
    pass

if __name__ == '__main__':
    main()
```

## TODO Comments

Format TODO comments consistently:

```python
# TODO: crbug.com/192795 - Investigate cpufreq optimizations.
```

## Consistency

**BE CONSISTENT**. When editing existing code:

- Follow the existing style in the file
- If the existing style conflicts with this guide, prefer updating to the new style
- Local consistency matters, but don't use it to justify outdated practices

---



Remember: The goal is readable, maintainable code that follows consistent patterns across the codebase.