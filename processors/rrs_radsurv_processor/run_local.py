import processor_app
import sys

radservice_name = processor_app.RrsRadsurvProcessor.processor_name()
scratch_path = 'Z:/scratch'
script_path = f'z:/radlib/processors/{radservice_name}/{radservice_name}_test_script.yaml'
print(radservice_name)
processor_app.RrsRadsurvProcessor.run_local(scratch_path, script_path)
