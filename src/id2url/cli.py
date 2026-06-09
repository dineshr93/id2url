"""Command-line interface for id2url."""

import json
import sys
from typing import Optional

import click

from . import SUPPORTED_REGISTRIES, __version__, get_download_url


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version and exit.")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """Convert package registry coordinates (origin IDs) to source download URLs.

    All registries automatically verify that packages exist before returning URLs.

    Supports: npm, dart, pypi, maven, crates, nuget, rubygems, go, packagist, cocoapods, hex

    Examples:

        id2url convert npm lodash/4.17.21

        id2url convert maven "com.google.guava:guava:31.1-jre"

        id2url convert maven "androidx.glance.wear:wear:1.0.0-alpha10"

        id2url batch input.txt --format json
    """
    if version:
        click.echo(f"id2url version {__version__}")
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("registry", type=click.Choice(SUPPORTED_REGISTRIES, case_sensitive=False))
@click.argument("origin_id")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["url", "json", "tsv"]),
    default="url",
    help="Output format (default: url)",
)
@click.option("--quiet", "-q", is_flag=True, help="Only output the URL (implies --format url)")
def convert(registry: str, origin_id: str, output_format: str, quiet: bool) -> None:
    """Convert a single package coordinate to download URL.

    REGISTRY: Package registry (npm, pypi, maven, etc.)
    ORIGIN_ID: Package coordinate (e.g., "lodash/4.17.21")

    Automatically verifies the package exists. For Maven, checks both
    Maven Central and Google Maven repositories.

    Examples:

        id2url convert npm lodash/4.17.21

        id2url convert pypi requests/2.31.0 --format json

        id2url convert maven "com.google.guava:guava:31.1-jre"

        id2url convert maven "androidx.glance.wear:wear:1.0.0-alpha10"
    """
    if quiet:
        output_format = "url"

    try:
        package_name, version, download_url = get_download_url(registry, origin_id)

        if output_format == "url":
            click.echo(download_url)
        elif output_format == "json":
            result = {
                "registry": registry.lower(),
                "origin_id": origin_id,
                "package_name": package_name,
                "version": version,
                "download_url": download_url,
            }
            click.echo(json.dumps(result, indent=2))
        elif output_format == "tsv":
            click.echo(f"{registry}\t{origin_id}\t{package_name}\t{version}\t{download_url}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "tsv", "urls"]),
    default="tsv",
    help="Output format (default: tsv)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    default=None,
    help="Output file (default: stdout)",
)
@click.option("--continue-on-error", "-c", is_flag=True, help="Continue processing on errors")
def batch(
    input_file: str,
    output_format: str,
    output_file: Optional[str],
    continue_on_error: bool,
) -> None:
    """Process multiple package coordinates from a file.

    INPUT_FILE: File with lines in format "registry<TAB>origin_id" or "registry origin_id"

    Automatically verifies each package exists in its registry.

    Example input file:

        npm    lodash/4.17.21

        pypi   requests/2.31.0

        maven  com.google.guava:guava:31.1-jre

    Examples:

        id2url batch packages.txt --format json -o results.json

        id2url batch packages.txt --format urls

        id2url batch packages.txt --continue-on-error
    """
    results = []
    errors = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse line: "registry<TAB>origin_id" or "registry origin_id"
            parts = line.split("\t") if "\t" in line else line.split(None, 1)
            if len(parts) != 2:
                error_msg = f"Line {line_num}: Invalid format - expected 'registry origin_id'"
                if continue_on_error:
                    errors.append({"line": line_num, "error": error_msg, "input": line})
                    continue
                else:
                    click.echo(f"Error: {error_msg}", err=True)
                    sys.exit(1)

            registry, origin_id = parts[0], parts[1]

            try:
                package_name, version, download_url = get_download_url(registry, origin_id)
                results.append({
                    "registry": registry.lower(),
                    "origin_id": origin_id,
                    "package_name": package_name,
                    "version": version,
                    "download_url": download_url,
                })
            except Exception as e:
                error_msg = f"Line {line_num}: {e}"
                if continue_on_error:
                    errors.append({"line": line_num, "error": str(e), "input": line})
                else:
                    click.echo(f"Error: {error_msg}", err=True)
                    sys.exit(1)

    # Format output
    if output_format == "json":
        output_data = {"results": results}
        if errors:
            output_data["errors"] = errors
        output_text = json.dumps(output_data, indent=2)
    elif output_format == "urls":
        output_text = "\n".join(r["download_url"] for r in results)
    else:  # tsv
        lines = ["registry\torigin_id\tpackage_name\tversion\tdownload_url"]
        for r in results:
            lines.append(
                f"{r['registry']}\t{r['origin_id']}\t{r['package_name']}\t"
                f"{r['version']}\t{r['download_url']}"
            )
        output_text = "\n".join(lines)

    # Write output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        click.echo(f"Processed {len(results)} packages, wrote to {output_file}")
        if errors:
            click.echo(f"Encountered {len(errors)} errors", err=True)
    else:
        click.echo(output_text)

    if errors and not continue_on_error:
        sys.exit(1)


@main.command("list")
def list_registries() -> None:
    """List all supported package registries."""
    click.echo("Supported package registries:\n")

    registry_info = [
        ("npm", "JavaScript/Node.js", "package/version or @scope/package/version"),
        ("dart", "Dart/Flutter (pub.dev)", "package/version"),
        ("pypi", "Python", "package/version"),
        ("maven", "Java/JVM + Android", "groupId:artifactId:version"),
        ("crates", "Rust (crates.io)", "crate/version"),
        ("nuget", ".NET/C#", "package/version"),
        ("rubygems", "Ruby", "gem/version"),
        ("go", "Go Modules", "module/path/vX.Y.Z"),
        ("packagist", "PHP/Composer", "vendor/package/version"),
        ("cocoapods", "iOS/macOS", "pod/version"),
        ("hex", "Erlang/Elixir", "package/version"),
    ]

    for name, platform, format_example in registry_info:
        click.echo(f"  {name:<12} {platform:<25} Format: {format_example}")


if __name__ == "__main__":
    main()
