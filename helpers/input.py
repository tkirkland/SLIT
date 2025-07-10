"""Advanced input handling for the SLIT installer.

This module provides custom input functions with character-level control,
input validation, and cross-platform compatibility.
"""

import sys
import termios
import tty
from typing import Optional, Set


def _build_choice_set(choices: list, case_sensitive: bool) -> set:
    """Build a set of valid choices."""
    if case_sensitive:
        return {str(item) for item in choices}
    else:
        return {str(item).lower() for item in choices}


def _handle_enter(current_result: str) -> dict:
    """Handle Enter key press."""
    if current_result:  # Only accept Enter if something was typed
        return {"type": "submit"}
    return {"type": "ignore"}


def _handle_backspace(current_result: str) -> dict:
    """Handle Backspace key press."""
    if current_result:
        new_result = current_result[:-1]
        print('\b \b', end='', flush=True)
        return {"type": "backspace", "result": new_result}
    return {"type": "ignore"}


class InputHandler:
    """Advanced input handler with character-level control."""

    def __init__(self) -> None:
        """Initialize input handler."""
        self.is_windows = sys.platform.startswith('win')
        self.has_terminal = self._check_terminal_support()

    def _check_terminal_support(self) -> bool:
        """Check if we have proper terminal support for raw input.
        
        Returns:
            True if terminal supports raw character input
        """
        try:
            if self.is_windows:
                import msvcrt
                return True
            else:
                # Check if we can access terminal settings
                fd = sys.stdin.fileno()
                termios.tcgetattr(fd)
                return sys.stdin.isatty()
        except (ImportError, termios.error, OSError):
            return False

    def getch(self) -> str:
        """Get a single character from stdin without pressing Enter.
        
        Returns:
            Single character pressed
        """
        if not self.has_terminal:
            # Fallback for non-terminal environments
            response = input("(Enter character + Enter): ")
            return response[0] if response else ' '
            
        if self.is_windows:
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    def custom_input(
        self,
        prompt: str = "",
        single_char: bool = False,
        allow_space: bool = True,
        allow_numbers: bool = True,
        allow_letters: bool = True,
        allow_symbols: bool = False,
        allowed_chars: Optional[Set[str]] = None,
        forbidden_chars: Optional[Set[str]] = None,
        echo_char: Optional[str] = None,
        max_length: Optional[int] = None,
        case_sensitive: bool = True
    ) -> str:
        """Advanced custom input with character-level control.

        Args:
            prompt: Text to display before input
            single_char: If True, return after single character
            allow_space: Allow space character
            allow_numbers: Allow numeric characters (0-9)
            allow_letters: Allow alphabetic characters (a-z, A-Z)
            allow_symbols: Allow symbol characters (!@#$%^&*()_+-=[]{}|;:,.<>?)
            allowed_chars: Specific characters to allow (overrides other flags)
            forbidden_chars: Specific characters to forbid
            echo_char: Character to echo instead of actual input (for passwords)
            max_length: Maximum input length
            case_sensitive: If False, convert to lowercase

        Returns:
            User input string
        """
        if prompt:
            print(prompt, end='', flush=True)

        if single_char:
            return self._single_char_input(echo_char, case_sensitive)
        else:
            return self._multi_char_input(echo_char, case_sensitive, allow_space, 
                                        allow_numbers, allow_letters, allow_symbols, 
                                        allowed_chars, forbidden_chars, max_length)

    def _single_char_input(self, echo_char: Optional[str], case_sensitive: bool) -> str:  # type: ignore
        """Handle single character input."""
        while True:
            char = self.getch()
            
            # Handle escape sequences
            if char == '\x1b':  # ESC character
                self._consume_escape_sequence()
                continue
            
            # Filter out control characters except CR/LF
            if ord(char) < 32 and char not in ('\r', '\n'):
                continue
            
            # Display the character appropriately
            if echo_char is not None:
                print(echo_char, end='', flush=True)
            elif char in ('\r', '\n'):
                print('<Enter>')
                return str(char)
            else:
                print(char, end='', flush=True)
            
            print()  # Newline after single char
            result = char.lower() if not case_sensitive else char
            return str(result)

    def _multi_char_input(self, echo_char: Optional[str], case_sensitive: bool,
                         allow_space: bool, allow_numbers: bool, allow_letters: bool,
                         allow_symbols: bool, allowed_chars: Optional[Set[str]],
                         forbidden_chars: Optional[Set[str]], max_length: Optional[int]) -> str:
        """Handle multi-character input."""
        # Fallback for non-terminal environments
        if not self.has_terminal:
            result = input()
            return result.lower() if not case_sensitive else result

        result = ""
        
        while True:
            char = self.getch()
            
            action = self._process_char(char, result, echo_char, case_sensitive,
                                      allow_space, allow_numbers, allow_letters,
                                      allow_symbols, allowed_chars, forbidden_chars,
                                      max_length)
            
            if action["type"] == "submit":
                print()
                break
            elif action["type"] == "backspace":
                result = action["result"]
            elif action["type"] == "add_char":
                result = action["result"]
            elif action["type"] == "exit":
                print()
                raise KeyboardInterrupt

        return result

    def _process_char(self, char: str, current_result: str, echo_char: Optional[str],
                     case_sensitive: bool, allow_space: bool, allow_numbers: bool,
                     allow_letters: bool, allow_symbols: bool, 
                     allowed_chars: Optional[Set[str]], forbidden_chars: Optional[Set[str]],
                     max_length: Optional[int]) -> dict:
        """Process a single character and return action to take."""
        
        # Handle special characters first
        if char in ('\r', '\n'):
            return _handle_enter(current_result)
        elif char in ('\b', '\x7f'):
            return _handle_backspace(current_result)
        elif char == '\x03':
            return {"type": "exit"}
        elif char == '\x1b':
            self._consume_escape_sequence()
            return {"type": "ignore"}
        elif ord(char) < 32:
            return {"type": "ignore"}
        else:
            return self._handle_printable_char(char, current_result, echo_char, case_sensitive,
                                             allow_space, allow_numbers, allow_letters,
                                             allow_symbols, allowed_chars, forbidden_chars,
                                             max_length)

    def _handle_printable_char(self, char: str, current_result: str, echo_char: Optional[str],
                              case_sensitive: bool, allow_space: bool, allow_numbers: bool,
                              allow_letters: bool, allow_symbols: bool,
                              allowed_chars: Optional[Set[str]], forbidden_chars: Optional[Set[str]],
                              max_length: Optional[int]) -> dict:
        """Handle printable character input."""
        # Check if character is allowed
        if not self._is_char_allowed(char, allow_space, allow_numbers, 
                                   allow_letters, allow_symbols, 
                                   allowed_chars, forbidden_chars):
            return {"type": "ignore"}
            
        # Check max length
        if max_length and len(current_result) >= max_length:
            return {"type": "ignore"}
            
        # Add character to result
        display_char = char if case_sensitive else char.lower()
        new_result = current_result + display_char
        
        # Echo character
        if echo_char is not None:
            print(echo_char, end='', flush=True)
        else:
            print(display_char, end='', flush=True)
            
        return {"type": "add_char", "result": new_result}

    def _consume_escape_sequence(self) -> None:
        """Consume escape sequence (arrow keys, etc.)."""
        try:
            next_char = self.getch()
            if next_char == '[':
                self.getch()  # Consume the final character (A/B/C/D for arrows)
        except:
            pass

    def _is_char_allowed(
        self,
        char: str,
        allow_space: bool,
        allow_numbers: bool,
        allow_letters: bool,
        allow_symbols: bool,
        allowed_chars: Optional[Set[str]],
        forbidden_chars: Optional[Set[str]]
    ) -> bool:
        """Check if character is allowed based on rules.

        Args:
            char: Character to check
            allow_space: Allow space character
            allow_numbers: Allow numeric characters
            allow_letters: Allow alphabetic characters
            allow_symbols: Allow symbol characters
            allowed_chars: Specific allowed characters
            forbidden_chars: Specific forbidden characters

        Returns:
            True if character is allowed
        """
        # Check forbidden characters first
        if forbidden_chars and char in forbidden_chars:
            return False

        # If allowed_chars is specified, only allow those
        if allowed_chars:
            return char in allowed_chars

        # Check specific character types
        if char == ' ':
            return allow_space
        elif char.isdigit():
            return allow_numbers
        elif char.isalpha():
            return allow_letters
        elif char in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`"\'\\':
            return allow_symbols
        else:
            return False

    def confirm_input(self, prompt: str = "Continue? (y/n): ", 
                     default: Optional[bool] = None) -> bool:
        """Get yes/no confirmation with single character input.

        Args:
            prompt: Confirmation prompt
            default: Default value if user presses Enter

        Returns:
            True for yes, False for no
        """
        formatted_prompt = self._format_confirm_prompt(prompt, default)
        print(formatted_prompt, end='', flush=True)
        
        while True:
            char = self.getch()
            result = self._process_confirm_char(char, default)
            
            if result is not None:
                return result

    def _format_confirm_prompt(self, prompt: str, default: Optional[bool]) -> str:
        """Format confirmation prompt with default indicator."""
        if default is not None:
            default_str = "Y/n" if default else "y/N"
            return f"{prompt.rstrip(' :')} [{default_str}]: "
        else:
            return f"{prompt.rstrip(' :')} (y/n): "

    def _process_confirm_char(self, char: str, default: Optional[bool]) -> Optional[bool]:
        """Process confirmation character input."""
        # Handle Enter - use default
        if char in ('\r', '\n') and default is not None:
            default_char = 'Y' if default else 'n'
            print(default_char)
            return default
        # Handle y/Y
        elif char.lower() == 'y':
            print(char.upper())
            return True
        # Handle n/N  
        elif char.lower() == 'n':
            print(char.upper())
            return False
        # Handle Ctrl+C
        elif char == '\x03':
            print()
            raise KeyboardInterrupt
        # Handle escape sequences (ignore)
        elif char == '\x1b':
            self._consume_escape_sequence()
            return None
        # All other characters are ignored
        else:
            return None

    def password_input(self, prompt: str = "Password: ", 
                      confirm: bool = False) -> str:
        """Secure password input with hidden characters.

        Args:
            prompt: Password prompt
            confirm: If True, ask for confirmation

        Returns:
            Password string
        """
        while True:
            password = self.custom_input(
                prompt,
                echo_char='*',
                allow_space=True,
                allow_symbols=True
            )

            if not confirm:
                return password

            confirm_password = self.custom_input(
                "Confirm password: ",
                echo_char='*',
                allow_space=True,
                allow_symbols=True
            )

            if password == confirm_password:
                return password
            else:
                print("Passwords do not match. Please try again.")

    def numeric_input(self, prompt: str = "Enter number: ",
                     min_value: Optional[int] = None,
                     max_value: Optional[int] = None,
                     max_length: Optional[int] = None) -> int: # type: ignore
        """Get numeric input with validation.

        Args:
            prompt: Input prompt
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            max_length: Maximum input length

        Returns:
            Validated integer
        """
        while True:
            try:
                text = self.custom_input(
                    prompt,
                    allow_letters=False,
                    allow_symbols=False,
                    allow_space=False,
                    max_length=max_length
                )
                
                if not text:
                    continue
                    
                value = int(text)
                
                if min_value is not None and value < min_value:
                    print(f"Value must be at least {min_value}")
                    continue
                    
                if max_value is not None and value > max_value:
                    print(f"Value must be at most {max_value}")
                    continue
                    
                return value
                
            except ValueError:
                print("Please enter a valid number")

    def choice_input(self, prompt: str, choices: list,
                    single_char: bool = True,
                    case_sensitive: bool = True) -> str:
        """Get input from a list of choices.

        Args:
            prompt: Input prompt
            choices: List of valid choices
            single_char: If True, use single character input
            case_sensitive: If True, match exact case

        Returns:
            Selected choice
        """
        valid_choices = _build_choice_set(choices, case_sensitive)
        
        if single_char:
            return self._single_char_choice(prompt, valid_choices, case_sensitive)
        else:
            return self._multi_char_choice(prompt, choices, valid_choices, case_sensitive)

    def _single_char_choice(self, prompt: str, valid_choices: set, case_sensitive: bool) -> str:
        """Handle single character choice input."""
        print(prompt, end='', flush=True)
        while True:
            char = self.getch()
            
            # Handle Ctrl+C
            if char == '\x03':
                print()
                raise KeyboardInterrupt
            # Handle escape sequences (ignore)
            elif char == '\x1b':
                self._consume_escape_sequence()
            # Check if valid choice
            else:
                test_char = char if case_sensitive else char.lower()
                if test_char in valid_choices:
                    print(char)
                    return char
            # Invalid choice - silently ignore

    def _multi_char_choice(self, prompt: str, choices: list, valid_choices: set, case_sensitive: bool) -> str:
        """Handle multi-character choice input."""
        while True:
            response = self.custom_input(
                prompt,
                single_char=False,
                case_sensitive=case_sensitive
            )
            
            test_response = response if case_sensitive else response.lower()
            if test_response in valid_choices:
                return response
            else:
                print(f"Please choose from: {', '.join(map(str, choices))}")


# Global input handler instance
input_handler = InputHandler()

# Convenience functions
def getch() -> str:
    """Get single character input."""
    return input_handler.getch()

def confirm(prompt: str = "Continue? (y/n): ", default: Optional[bool] = None) -> bool:
    """Get yes/no confirmation."""
    return input_handler.confirm_input(prompt, default)

def password(prompt: str = "Password: ", confirm: bool = False) -> str:
    """Get password input."""
    return input_handler.password_input(prompt, confirm)

def numeric(prompt: str = "Enter number: ", min_val: Optional[int] = None, 
           max_val: Optional[int] = None, max_length: Optional[int] = None) -> int:
    """Get numeric input."""
    return input_handler.numeric_input(prompt, min_val, max_val, max_length)

def choice(prompt: str, choices: list, single_char: bool = True,
          case_sensitive: bool = True) -> str:
    """Get choice from list."""
    return input_handler.choice_input(prompt, choices, single_char, case_sensitive)