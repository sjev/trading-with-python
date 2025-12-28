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
    """Lint, format, and typecheck."""
    ctx.run("ruff check src examples", pty=True)
    ctx.run("ruff format --check src examples", pty=True)
    ctx.run("mypy src examples", pty=True)


@task
def test(ctx):
    """Run tests with coverage."""
    ctx.run("pytest --cov=src --cov-report=term-missing", pty=True)
