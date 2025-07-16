import subprocess
import sys
sys.path.append('/home/aa-cxk023/share/radlib')
from radlib.processor.processor import Processor


class TotalSegmentatorProcessor(Processor):


    def processor_script(self):
        # total segmentator preprocessing
        try:

            print('------------script------------')
            print(self.script_info)
            print('------------------------------')
            # assume each input_file is paired with an output_file
            for input_file, output_file in zip(self.get_fileset('input_files').get_local_paths(),
                                                self.get_fileset('output_files').get_local_paths()):

                # run process
                try:
                    command_text = ['TotalSegmentator', '-i', input_file, '-o', output_file,
                                    '-ta', 'total_mr', '-ml', '-v']

                    self.logger.info(f"run unique process {command_text}")
                    print(command_text)
                    p = subprocess.Popen(command_text, text=True, close_fds=True)
                    exit_code = p.wait()
                    self.logger.info(f"run unique process {command_text} finished with code {exit_code}")
                    p.terminate()

                except Exception as e:
                    print(f"Error: {e}")

        except Exception as e:
            print(f"{self.processor_name()} exception {e}")


if __name__ == "__main__":
    TotalSegmentatorProcessor.run_processor()
