import subprocess


def getoutput(command):
    """Execute a shell command and return the output as a list of strings."""
    try:
        # Execute the command, capture the output
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        # Split the output into lines and return as a list
        return output.strip().split("\n")
    except subprocess.CalledProcessError as e:
        # Return error output if command execution fails
        return e.output.strip().split("\n")


def system(command):
    """Execute a shell command, displaying the output directly to the console."""
    try:
        # Execute the command and display output directly to console
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        # Print error message if command execution fails
        print(f"Command failed with return code {e.returncode}")
