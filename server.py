import falcon
import falcon.asgi
import json
import urllib.parse
import traceback

from dotenv import dotenv_values
from pymongo import MongoClient

from main import fetch_report, fetch_shroomery_report, fetch_shroomery_reports, fetch_pihkal, wordle_latest

config = dotenv_values(".env")

# Load DB
mongodb_client = MongoClient(config["ATLAS_URI"])
db = mongodb_client[config["DB_NAME"]]
print("Connected to the MongoDB database!")


# Falcon follows the REST architectural style, meaning (among
# other reports) that you think in terms of resources and state
# transitions, which map to HTTP verbs.

class ShroomeryReportsResource:
    async def on_get(self, req, resp):
        if "page" in req.params:
            links = fetch_shroomery_reports(page=req.params["page"])
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(links)
        elif "url" in req.params:
            report_id_url = urllib.parse.unquote(req.params["url"])
            report_id = report_id_url.split("/")[-1:][0]
            report = fetch_shroomery_report(id=report_id)
            
            existing = db["shroomery-1"].find_one(
                {"post.id": str(report_id)}
            )
            if existing is None:
                db["shroomery-1"].insert_one(report)
                existing = db["shroomery-1"].find_one(
                    {"post.id": str(report_id)}
                )
                del existing['_id']
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(existing)
                return
            del existing['_id']
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(existing)
        else:
            report_id = req.params["id"]
            report = fetch_shroomery_report(id=report_id)
            
            existing = db["shroomery-1"].find_one(
                {"post.id": str(report_id)}
            )
            if existing is None:
                db["shroomery-1"].insert_one(report)
                existing = db["shroomery-1"].find_one(
                    {"post.id": str(report_id)}
                )
                del existing['_id']
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(existing)
                return
            del existing['_id']
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(existing)


class ErowidReportsResource:
    async def on_get(self, req, resp):
        """Handles GET requests"""
        if 'ID' not in req.params:
            resp.status = falcon.HTTP_400
            resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
            resp.text = (
                'Report id not provided'
            )
            return

        report_id = req.params["ID"]
        existing = db["erowid-1"].find_one(
            {"extra.exp_id": str(report_id)}
        )

        if existing is not None:
            del existing['_id']
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(existing)
        else:
            report = fetch_report(id=report_id)
            if "faulty" in report:
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(report)
            else:
                db["erowid-1"].insert_one(report)
                existing = db["erowid-1"].find_one(
                    {"extra.exp_id": (report_id)}
                )
                del existing['_id']

                resp.status = falcon.HTTP_200
                resp.body = json.dumps(existing)


class WorbleResource:
    async def on_get(self, req, resp):
        """Handles GET requests"""
        wordle_data = wordle_latest(tz=req.params["tz"] if "tz" in req.params else "America/New_York")
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(wordle_data)


class PihkalResource:
    async def on_get(self, req, resp):
        """Handles GET requests"""
        if 'drug' not in req.params:
            resp.status = falcon.HTTP_400
            resp.content_type = falcon.MEDIA_TEXT  # Default is JSON, so override
            resp.text = (
                'Drug id not provided'
            )
            return
        try:
            drug = req.params["drug"]
            drug_data = fetch_pihkal(drug=drug)
            existing = db["dbank"].find_one(
                {"name": drug_data["name"]}
            )
            if existing is not None:
                del existing['_id']
                resp.status = falcon.HTTP_200
                resp.body = json.dumps(existing)
            else:
                # print(drug_data)
                db["dbank"].insert_one(drug_data)
                resp.status = falcon.HTTP_200
                resp.body = json.dumps({"message": "success"})
        except:
            traceback.print_exc()


# falcon.asgi.App instances are callable ASGI apps...
# in larger applications the app is created in a separate file
app = falcon.asgi.App()

# Resources are represented by long-lived class instances
reports = ErowidReportsResource()
shroomery_reports = ShroomeryReportsResource()
worble = WorbleResource()
pihkal = PihkalResource()

# reports will handle all requests to the '/reports' URL path
app.add_route('/exp.php', reports)
app.add_route('/shroomery', shroomery_reports)
app.add_route('/worble', worble)
app.add_route('/pihkal', pihkal)