import os
import openai
import re
from pymongo import MongoClient
import pandas as pd
import json

def ceil(ceil=None, num=0):
    if ceil is None:
        return num
    else:
        return num if num <= ceil else ceil

openai.api_key = os.getenv("OPENAI_API_KEY")
cert_path = os.path.abspath("analysis/X509-cert-6010376682297659033.pem")
uri = "mongodb+srv://curated0.a1vgt.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile=cert_path)
db = client['tripindex']
collection = db['erowid-1']
result_collection = db['erowid-effects']
doc_count = collection.count_documents({})
print(doc_count)

texts = [item for item in collection.find().limit(1000).skip(39574)]

for text in texts:
    result = {}
    t = text["text"]
    joined_full = "\n".join(t)
    joined = joined_full[:ceil(ceil=3000, num=len(joined_full))]
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"A table summarizing the subjective effects from a trip report:\n\n{joined}\n\n| Subjective Effect |",
        temperature=0.1,
        max_tokens=1250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    result["link"] = f"https://erowid.org/experiences/exp.php?ID={text['extra']['exp_id']}"
    result["drug"] = re.split(', | & ', text["drug"])
    result_raw = "| Subjective Effect |" + response["choices"][0]["text"]

    df: pd.DataFrame = pd.DataFrame([x.split('|') for x in result_raw.split('\n')])
    data_drop_first = df.iloc[:, 1:]
    data_drop_last = data_drop_first.iloc[:, :-1]
    df = data_drop_last.T.set_index(0).T.tail(-1)
    df = df.rename(columns={" Subjective Effect ": "effect", " Description ": "detail"})
    effects = json.loads(json.dumps(list(df.applymap(lambda x: x.strip() if isinstance(x, str) else x).T.to_dict().values())))

    result["effects"] = effects

    print("************************************")
    print(result["drug"])
    print(effects)
    print("************************************")

    result_collection.insert_one(result)

    # with open("result.txt", "a") as f:
    #     f.write(result["link"])
    #     f.write(";".join(result["drug"]))
    #     f.write(result["result"])