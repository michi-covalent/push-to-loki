import datetime
import dateutil.parser
import json
import pprint
import requests
import os
import sys


def workflow_run_to_stream(workflow_run, branch):
    run_started_at = dateutil.parser.isoparse(workflow_run["run_started_at"])
    updated_at = dateutil.parser.isoparse(workflow_run["updated_at"])
    return {
        "stream": {
            "branch": branch,
            "conclusion": workflow_run["conclusion"],
            "duration_seconds": int(
                datetime.timedelta.total_seconds(updated_at - run_started_at)
            ),
            "event": workflow_run["event"],
            "filename": os.path.basename(workflow_run["path"]),
            "head_branch": workflow_run["head_branch"],
            "repo": workflow_run["repository"]["full_name"],
            "stream": "github_workflow_runs",
            "url": workflow_run["html_url"],
        },
        "values": [
            [
                "{:d}000000000".format(int(updated_at.timestamp())),
                json.dumps(workflow_run),
            ]
        ],
    }


def job_to_stream(workflow_run, job, branch):
    duration = 0
    completed_at = datetime.datetime.now(datetime.timezone.utc)
    if (
        "started_at" in job
        and job["started_at"] is not None
        and "completed_at" in job
        and job["completed_at"] is not None
    ):
        started_at = dateutil.parser.isoparse(job["started_at"])
        completed_at = dateutil.parser.isoparse(job["completed_at"])
        duration = int(datetime.timedelta.total_seconds(completed_at - started_at))
    return {
        "stream": {
            "branch": branch,
            "conclusion": job["conclusion"],
            "duration_seconds": duration,
            "event": workflow_run["event"],
            "filename": os.path.basename(workflow_run["path"]),
            "head_branch": workflow_run["head_branch"],
            "url": job["html_url"],
            "name": job["name"],
            "status": job["status"],
            "stream": "github_jobs",
            "repo": workflow_run["repository"]["full_name"],
        },
        "values": [
            ["{:d}000000000".format(int(completed_at.timestamp())), json.dumps(job)]
        ],
    }


def step_to_stream(workflow_run, job, step, branch):
    duration = 0
    completed_at = datetime.datetime.now(datetime.timezone.utc)
    if (
        "started_at" in step
        and step["started_at"] is not None
        and "completed_at" in step
        and step["completed_at"] is not None
    ):
        started_at = dateutil.parser.isoparse(step["started_at"])
        completed_at = dateutil.parser.isoparse(step["completed_at"])
        duration = int(datetime.timedelta.total_seconds(completed_at - started_at))
    return {
        "stream": {
            "branch": branch,
            "conclusion": step["conclusion"],
            "duration_seconds": duration,
            "event": workflow_run["event"],
            "filename": os.path.basename(workflow_run["path"]),
            "head_branch": workflow_run["head_branch"],
            "job_name": job["name"],
            "name": step["name"],
            "status": step["status"],
            "stream": "github_steps",
            "repo": workflow_run["repository"]["full_name"],
        },
        "values": [
            ["{:d}000000000".format(int(completed_at.timestamp())), json.dumps(step)]
        ],
    }


def jobs_to_stream(workflow_run, jobs, branch):
    streams = []
    for job in jobs["jobs"]:
        streams.append(job_to_stream(workflow_run, job, branch))
        for step in job["steps"]:
            streams.append(step_to_stream(workflow_run, job, step, branch))
    return streams


def main(loki_endpoint, loki_username, loki_password, workflow_run_url, github_token):
    # Get workflow run.
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "token " + github_token,
    }
    r = requests.get(workflow_run_url, headers=headers)
    workflow_run = r.json()
    pprint.pprint(workflow_run)

    # Get jobs.
    r = requests.get(workflow_run["jobs_url"], headers=headers)
    jobs = r.json()

    # If all the jobs were skipped, don't bother sending to Loki.
    if all([job["conclusion"] == "skipped" for job in jobs["jobs"]]):
        print("All jobs got skipped. Not reporting to Loki")
        pprint.pprint(jobs)
        return 0

    # For pull request events, use the first base ref as branch label.
    # For other events use head_branch as branch label.
    branch = workflow_run["head_branch"]
    if "pull_requests" in workflow_run and workflow_run["pull_requests"]:
        branch = workflow_run["pull_requests"][0]["base"]["ref"]

    streams = jobs_to_stream(workflow_run, jobs, branch)
    streams.append(workflow_run_to_stream(workflow_run, branch))

    body = {"streams": streams}
    r = requests.post(loki_endpoint, json=body, auth=(loki_username, loki_password))
    pprint.pprint(body)
    pprint.pprint(r.status_code)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
