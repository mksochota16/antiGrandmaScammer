import json
import pickle
import traceback
from typing import List, Tuple

import uvicorn
from bson import ObjectId
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from grandma_analyzer.new_data_parser import create_dataframe

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins if needed
    allow_methods=["*"],  # Adjust this to restrict HTTP methods if needed
    allow_headers=["*"],  # Adjust this to restrict headers if needed
)


class UrlScanResponse(BaseModel):
    result: bool = False


@app.get("/check-url",
         response_model=UrlScanResponse)
def place_scraper(url: str):
    df = create_dataframe(url)
    to_drop = ['url',
               'domain_age',
               'nameserver_domain',
               'mail_domain',
               'tls_age',
               'tls_issuer',
               'url_len',
               'parameters_len',
               'parameters_count',
               'numbers_percent',
               'url_entropy',
               'is_redirect',
               'subdomain_count',
               'content_img_count',
               'label']
    df = df.drop(to_drop, axis=1)
    df = df.fillna(-1)
    df = df.replace('', -1)

    with open('../../data/dict.json', 'r') as plik:
        names_dict = json.load(plik)

    df = df.replace(names_dict)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = -1

    model = pickle.load(open('../../ml_models/finalized_model.sav', 'rb'))

    prediction = model.predict(df.values.tolist())
    return UrlScanResponse(result=(prediction[0] == 1))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
