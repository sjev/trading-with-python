# type: ignore
from invoke import task


@task
def clean(ctx):
    """Dry-run git clean (prompts before deleting)."""
    ctx.run("git clean -nfdx")

    response = (
        input("Are you sure you want to remove all untracked files? (y/n) [n]: ")
        .strip()
        .lower()
    )
    if response == "y":
        ctx.run("git clean -fdx")


@task
def lint(ctx):
    """Lint/format/typecheck the modernized code path (twp package)."""
    ctx.run("ruff check src/twp", pty=True)
    ctx.run("ruff format --check src/twp", pty=True)
    ctx.run("mypy src/twp", pty=True)


@task
def test(ctx):
    """Run tests with coverage."""
    ctx.run("pytest --cov=src --cov-report=term-missing", pty=True)
