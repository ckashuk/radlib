import sys

sys.path.append('/home/aa-cxk023/share/radlib')

from radlib.processor.processor import Processor

class TestProcessor(Processor):

    def processor_script(self):
        print(f'this is {self.processor_name()} processor_script!')
        with open('/script.yaml') as f:
            print(f.readlines())

if __name__ == "__main__":
    TestProcessor.run_processor()
