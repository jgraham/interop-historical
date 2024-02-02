import argparse
import csv
import io
import pygit2
import os
import sys
from datetime import datetime

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", default="origin/gh-pages")
    parser.add_argument("--out-path", default=os.curdir)
    parser.add_argument("repo_path", help="Path to interop scoring repo")
    return parser


def load_commits(repo, branch, paths):
    branch_ref = repo.branches[branch]
    for commit in repo.walk(branch_ref.peel().oid, pygit2.GIT_SORT_REVERSE):
        tree = commit.tree
        blobs = {path: tree[path] for path in paths if path in tree}
        yield commit, blobs


class ScoreData:
    def __init__(self):
        self.field_names = None
        self.output_data = []

    def add(self, commit_time, data:str):
        reader = csv.DictReader(data)
        all_rows = list(reader)
        if self.field_names is None:
            self.field_names = reader.fieldnames
            self.field_names.insert(1, "time")
        date_str = self.output_data[-1]["date"] if self.output_data else all_rows[0]["date"]
        current_date = datetime.strptime(date_str, "%Y-%m-%d")
        for row in all_rows:
            date = datetime.strptime(row["date"], "%Y-%m-%d")
            appended = False
            last_row = self.output_data[-1].copy() if self.output_data else None
            if last_row:
                del last_row["time"]
            if date >= current_date:
                # Only add new rows if they're different from the previous row
                if appended or row != last_row:
                    row["time"] = datetime.fromtimestamp(commit_time).isoformat()
                    self.output_data.append(row)
                    appended = True

    def write(self, f):
        writer = csv.DictWriter(f, self.field_names)
        writer.writeheader()
        writer.writerows(self.output_data)


def main():
    parser = get_parser()
    args = parser.parse_args()

    repo = pygit2.Repository(args.repo_path)

    score_data = {"data/interop-2024/interop-2024-experimental-v2.csv": ScoreData(),
                  "data/interop-2024/interop-2024-stable-v2.csv": ScoreData()}

    for (commit, blobs) in load_commits(repo, args.branch, score_data.keys()):
        commit_time = commit.commit_time
        for filename, blob in blobs.items():
            data = io.StringIO(blob.data.decode("utf8"))
            score_data[filename].add(commit_time, data)

    for path, data in score_data.items():
        out_path = os.path.join(args.out_path,
                                path.rsplit("/", 1)[1].replace(".csv", "-historic.csv"))
        with open(out_path, "w") as f:
            data.write(f)

if __name__ == "__main__":
    main()
