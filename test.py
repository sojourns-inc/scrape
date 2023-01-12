from time import sleep
import requests
import fileinput
import pathlib
from datetime import datetime

counter = 0
for line in fileinput.input("erowid-links-2.csv"):
    if counter < 50000:
        result = requests.request("GET", line.rstrip())
        counter += 1
        if result.status_code != 200:
            print(result.status_code)
    else:
        break
