import datetime
import dateutil.parser
import json
import pprint
import requests
import sys

LOKI_ENDPOINT = sys.argv[1]
LOKI_USERNAME = sys.argv[2]
LOKI_PASSWORD = sys.argv[3]
WORKFLOW_RUN_URL = sys.argv[4]
GITHUB_TOKEN = sys.argv[5]


def workflow_run_to_stream(workflow_run_, branch_):
    run_started_at = dateutil.parser.isoparse(workflow_run_["run_started_at"])
    updated_at = dateutil.parser.isoparse(workflow_run_["updated_at"])
    return {
        "stream": {
            "branch": branch_,
            "conclusion": workflow_run_["conclusion"],
            "duration_seconds": int(
                datetime.timedelta.total_seconds(updated_at - run_started_at)
            ),
            "event": workflow_run_["event"],
            "head_branch": workflow_run_["head_branch"],
            "path": workflow_run_["path"],
            "repo": workflow_run_["repository"]["full_name"],
            "stream": "github",
            "url": workflow_run_["html_url"],
        },
        "values": [
            [
                "{:d}000000000".format(int(updated_at.timestamp())),
                json.dumps(workflow_run_),
            ]
        ],
    }


def job_to_stream(workflow_run_, job_, branch_):
    started_at = dateutil.parser.isoparse(job_["started_at"])
    completed_at = dateutil.parser.isoparse(job_["completed_at"])
    return {
        "stream": {
            "branch": branch_,
            "conclusion": job_["conclusion"],
            "duration_seconds": int(
                datetime.timedelta.total_seconds(completed_at - started_at)
            ),
            "event": workflow_run_["event"],
            "head_branch": workflow_run_["head_branch"],
            "url": job_["html_url"],
            "name": job_["name"],
            "status": job_["status"],
            "stream": "github_jobs",
            "path": workflow_run_["path"],
            "repo": workflow_run_["repository"]["full_name"],
        },
        "values": [
            ["{:d}000000000".format(int(completed_at.timestamp())), json.dumps(job_)]
        ],
    }


def step_to_stream(workflow_run_, job_, step_, branch_):
    started_at = dateutil.parser.isoparse(step_["started_at"])
    completed_at = dateutil.parser.isoparse(step_["completed_at"])
    return {
        "stream": {
            "branch": branch_,
            "conclusion": step_["conclusion"],
            "duration_seconds": int(
                datetime.timedelta.total_seconds(completed_at - started_at)
            ),
            "event": workflow_run_["event"],
            "head_branch": workflow_run_["head_branch"],
            "job_name": job_["name"],
            "name": step_["name"],
            "status": step_["status"],
            "stream": "github_steps",
            "path": workflow_run_["path"],
            "repo": workflow_run_["repository"]["full_name"],
        },
        "values": [
            ["{:d}000000000".format(int(completed_at.timestamp())), json.dumps(step_)]
        ],
    }


# Get workflow run.
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": "token " + GITHUB_TOKEN,
}
r = requests.get(WORKFLOW_RUN_URL, headers=headers)
workflow_run = r.json()
pprint.pprint(workflow_run)

# Get jobs.
r = requests.get(workflow_run["jobs_url"], headers=headers)
jobs = r.json()

# If all the jobs were skipped, don't bother sending to Loki.
if all([job["conclusion"] == "skipped" for job in jobs["jobs"]]):
    print("All jobs got skipped. Not reporting to Loki")
    pprint.pprint(jobs)
    sys.exit(0)

# For pull request events, use the first base ref as branch label.
# For other events use head_branch as branch label.
branch = workflow_run["head_branch"]
if "pull_requests" in workflow_run and workflow_run["pull_requests"]:
    branch = workflow_run["pull_requests"][0]["base"]["ref"]

streams = []
for job in jobs["jobs"]:
    streams.append(job_to_stream(workflow_run, job, branch))
    for step in job["steps"]:
        streams.append(step_to_stream(workflow_run, job, step, branch))

streams.append(workflow_run_to_stream(workflow_run, branch))

body = {"streams": streams}
r = requests.post(LOKI_ENDPOINT, json=body, auth=(LOKI_USERNAME, LOKI_PASSWORD))
pprint.pprint(body)
pprint.pprint(r.status_code)
