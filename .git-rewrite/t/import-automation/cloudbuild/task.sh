curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
python3 -m pip install -r import-automation/cloudbuild/requirements.txt
python3 import-automation/cloudbuild/create_task.py
