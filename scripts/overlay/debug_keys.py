#!/usr/bin/env python3
"""
Debug script to see what pynput receives.
Press Ctrl+C to exit (in the terminal that launched this).
"""

from pynput import keyboard
import sys

print("Listening for keys... (Ctrl+C in terminal to stop)")
print("Press any keys to see what pynput detects:")
print("-" * 50)

def on_press(key):
    try:
        char = key.char
        print(f"PRESS: char='{char}' | key={key} | type={type(key).__name__}")
    except AttributeError:
        print(f"PRESS: special key={key} | type={type(key).__name__}")

    # Check for escape
    if key == keyboard.Key.escape:
        print(">>> ESCAPE DETECTED - would exit")
        return False  # Stop listener

    sys.stdout.flush()

def on_release(key):
    pass

# Try WITHOUT suppress first
print("\nMode: suppress=False (keys pass through)")
print("=" * 50)

with keyboard.Listener(on_press=on_press, on_release=on_release, suppress=False) as listener:
    listener.join()

print("\nListener stopped.")
