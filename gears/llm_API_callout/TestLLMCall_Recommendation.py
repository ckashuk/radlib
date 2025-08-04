import os
import json
import subprocess
import shutil
#Install the required libraries
def install_libraries():
    subprocess.check_call([os.sys.executable, "-m", "pip", "install", "openai"])


#install_libraries()

from openai import OpenAI
import pandas as pd
client = OpenAI(
    base_url = 'http://10.151.27.42:11434/v1',
    api_key='ollama', # required, but unused
)

response = client.chat.completions.create(
    model="gemma3:27b",
    messages=[
        {"role": "user", "content": "In the following radiology report impression is any recommendation made? Only answer yes or no. Report impression: 1. No cardiac mass demonstrated on this cardiac MRI. ENCOUNTER_MED^GADOTERATE MEGLUMINE 10 MMOL/20ML IV SOLN 37 mL"}    ]
)
print(response.choices[0].message.content)