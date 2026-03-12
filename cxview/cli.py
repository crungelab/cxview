import click

from .app import CxView
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        app = CxView().create()
        app.use_all()
        app.show_channel("main")
        app.run()


@cli.command()
@click.pass_context
@click.argument("name")
def show(ctx, name):
    app = CxView().create()
    app.show_channel(name)
    app.run()

"""
from crunge.demo.cli import cli
from crunge.demo.demo import set_demo_factory
from .app import CxView

__all__ = ["cli"]


def factory():
    app = CxView().create()
    app.use_all()
    app.show_channel("main")

    return app


set_demo_factory(factory)
"""