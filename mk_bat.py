import yaml

def extract_run_blocks_with_env(yaml_file, output_batch_file):
    # Open and parse the YAML file
    with open(yaml_file, 'r') as file:
        workflow = yaml.safe_load(file)

    # Extract global environment variables
    global_env = workflow.get('jobs', {}).get('build', {}).get('env', {})

    # Extract all "run" blocks
    run_commands = []
    for job in workflow.get('jobs', {}).values():
        for step in job.get('steps', []):
            if 'run' in step:
                run_commands.append(step['run'])

    # Write the batch file
    with open(output_batch_file, 'w') as batch_file:
        # Add a header for the batch file
        batch_file.write("@echo off\n\n")

        # Write global environment variables as `set` commands
        for key, value in global_env.items():
            batch_file.write(f"set {key}={value}\n")
        batch_file.write("\n")

        # Write all extracted `run` commands
        for command in run_commands:
            batch_file.write(command + "\n\n")

    print(f"Batch file created: {output_batch_file}")


# Example usage
yaml_file = ".github/workflows/bld_cmd_ci_py3129_vs22_x64_dbg.yml"
output_batch_file = "output.bat"
extract_run_blocks_with_env(yaml_file, output_batch_file)
