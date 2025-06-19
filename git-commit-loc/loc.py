# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "typer",
#   "GitPython",
# ]
# ///
import csv
from typing import cast

from git import Commit, Repo, Tree
from typer import Typer


def count_lines_in_commit(commit: Commit, ext: str) -> int:
    total_lines = 0

    def traverse_tree(tree: Tree) -> None:
        nonlocal total_lines
        for blob in tree.blobs:
            if blob.name.endswith(ext):
                data = cast(bytes, blob.data_stream.read())
                content = data.decode("utf-8")
                total_lines += len(content.splitlines())
        for subtree in tree.trees:
            traverse_tree(subtree)

    traverse_tree(commit.tree)
    return total_lines


def analyze_repo(path: str, branch: str, ext: str, output: str) -> None:
    repo = Repo(path)
    assert not repo.bare

    commits = list(repo.iter_commits(branch))[::-1]

    with open(output, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "commit_sha",
                "commit_datetime_iso",
                "line_count",
                "commit_message",
            ]
        )

        for n, commit in enumerate(commits, start=1):
            line_count = count_lines_in_commit(commit, ext)
            assert isinstance(commit.message, str), f"{type(commit.message)=}"
            writer.writerow(
                [
                    commit.hexsha,
                    commit.committed_datetime.isoformat(),
                    line_count,
                    commit.message.strip().replace("\n", " "),
                ]
            )
            if n == 1 or n == len(commits):
                print(
                    f"{n}/{len(commits)}: "
                    f"{commit.hexsha} - {line_count} lines"
                )
                if n == 1:
                    print("...")

    print(f"written to {output}")


cli = Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@cli.command()
def analyze(
    repo: str = ".",
    branch: str = "main",
    ext: str = ".py",
    output: str = "output.csv",
) -> None:
    print("repo", repo, "| branch", branch, "| ext", ext)
    analyze_repo(repo, branch, ext, output)


if __name__ == "__main__":
    cli()
