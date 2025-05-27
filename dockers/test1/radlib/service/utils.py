import yaml

def parse_script(script_path):
    with open(script_path) as file:
        script = yaml.safe_load(file)

        return script

def generate_docker_call(script):
    return "run"

