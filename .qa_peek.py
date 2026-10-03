"""Throwaway QA helper: print the dashboard score breakdown for the browser QA user."""

import json
import sys

import httpx
from dotenv import dotenv_values
from supabase import create_client

env = {**dotenv_values(".env"), **dotenv_values(".env.test")}
client = create_client(env["SUPABASE_URL"], env["SUPABASE_ANON_KEY"])
session = client.auth.sign_in_with_password({"email": "qa-c@arwa.dev", "password": env["ARWA_TEST_PASSWORD"]}).session
path = sys.argv[1] if len(sys.argv) > 1 else "/dashboard"
response = httpx.get(f"http://localhost:8000{path}", headers={"Authorization": f"Bearer {session.access_token}"}, timeout=60)
data = response.json()
if path == "/dashboard":
    data = {
        "score": data["score"]["score"],
        "factors": [(f["key"], f.get("score"), f.get("weight")) for f in data["score"]["factors"]],
        "metrics": [(m["key"], m.get("value"), m.get("detail")) for m in data["metrics"]],
        "insight": data.get("insight"),
    }
print(response.status_code, json.dumps(data, indent=1, default=str)[:4000])
