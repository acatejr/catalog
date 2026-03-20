import click
import datetime

@click.group()
def cli():
    """Catalog CLI group."""
    pass


@cli.command()
def health() -> None:
    """Helper command to check the application's status."""
    click.echo(f"status: ok - {datetime.datetime.now()}")

def _download_all_fs_metadata():
    print("Downloading all filesystem metadata...")


if __name__ == "__main__":
    cli()