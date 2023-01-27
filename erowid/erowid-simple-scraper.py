from time import sleep
import requests
import fileinput
import pathlib
from datetime import datetime

counter = 0
base_url = "http://localhost:8000"

for line in fileinput.input("erowid-links.csv"):
    if counter < 5000:
        result = requests.request("GET", f"{base_url}/exp.php?ID={line.rstrip()}")
        counter += 1
        if result.status_code != 200:
            print(result.status_code)
    else:
        break
