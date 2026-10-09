"""Create deterministic dependency-only NuGet packages for the PDF's synthetic tests."""
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from xml.sax.saxutils import escape


def create_feed(directory, specification):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, children in specification.items():
        dependencies = ''.join(f'<dependency id="{escape(child)}" version="1.0.0" />' for child in children)
        nuspec = (f'<?xml version="1.0"?><package><metadata><id>{escape(name)}</id>'
                  '<version>1.0.0</version><authors>IR QA</authors><description>Dependency graph fixture</description>'
                  f'<dependencies><group targetFramework="net8.0">{dependencies}</group></dependencies></metadata></package>')
        with ZipFile(directory / f'{name.lower()}.1.0.0.nupkg', 'w', ZIP_DEFLATED) as archive:
            info = ZipInfo(f'{name}.nuspec', date_time=(2020, 1, 1, 0, 0, 0))
            archive.writestr(info, nuspec)


def prepare(scenario_dir):
    specification = json.loads((scenario_dir / 'feed.json').read_text(encoding='utf-8'))
    create_feed(scenario_dir / 'feed', specification)
    if (scenario_dir / 'duplicate-feed').exists():
        create_feed(scenario_dir / 'duplicate-feed', specification)
