#!/usr/bin/env python3
"""
Compiler Tool
Wraps `javac` to check for syntax errors in Java files.
"""

import subprocess
import tempfile
import os
import sys

def check_syntax(file_path: str) -> str:
    """
    Checks Java syntax for a given file using `javac`.
    Returns "OK" if compilation succeeds (or only has classpath errors we ignore),
    or the error message if there are syntax errors.
    """
    if not file_path.endswith(".java"):
        return "Error: Not a Java file"
        
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"

    # Create a temporary directory for class output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Construct javac command
        # -Xlint:none : Disable warnings
        # -nowarn : Disable warnings
        # -d : Output directory
        # -proc:none : Disable annotation processing (speeds it up)
        cmd = ["javac", "-Xlint:none", "-nowarn", "-d", temp_dir, "-proc:none", file_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return "OK"
            else:
                # Filter output?
                # Without classpath, we will get many "cannot find symbol" errors.
                # We want to prioritize "expected ';'" or "invalid method declaration" etc.
                
                errors = result.stderr.strip()
                
                # Simple heuristic: If it's just "cannot find symbol", it might be due to missing classpath.
                # But for now, we return the raw errors so the agent can see them.
                # The agent should be instructed that "cannot find symbol" for known libraries is expected if env is not set up.
                return f"Compilation Failed:\n{errors}"
                
        except FileNotFoundError:
            return "Error: `javac` not found in PATH."
        except Exception as e:
            return f"Error running compiler: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(check_syntax(sys.argv[1]))
    else:
        print("Usage: python3 compiler_tool.py <path_to_java_file>")
