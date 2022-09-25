import json
from unittest import TestCase
from push import jobs_to_stream


class Test(TestCase):
    def test_jobs_to_stream(self):
        with open("testdata/run.json") as run_json, open(
            "testdata/jobs.json"
        ) as jobs_json:
            run = json.load(run_json)
            jobs = json.load(jobs_json)
            # Make sure it can handle null timestamps
            jobs_to_stream(run, jobs, "main")
