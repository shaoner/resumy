import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, cast

import jinja2
import yaml
from weasyprint import HTML  # type: ignore
from weasyprint.document import DocumentMetadata  # type: ignore

DATE_FORMAT = '%Y-%m-%d'
DEFAULT_OUTPUT_FILENAME = 'out.pdf'
DEFAULT_CONFIG_FILENAME = 'myconfig.yaml'
DEFAULT_MYTHEME_NAME = 'mytheme'
DEFAULT_THEMES_DIR = 'themes'
DEFAULT_THEME = 'prairie'

# Type aliases
Config = Dict[str, Any]

# Setup logger
logger = logging.getLogger('resumy')
logger.setLevel(logging.INFO)


def get_config(config_path: str) -> Config:
    config = {}
    with open(config_path, 'r') as stream:
        config = yaml.safe_load(stream)
    return config


def create_resume(config: Config,
                  output_file: str,
                  theme_path: str,
                  metadata: DocumentMetadata) -> None:
    # 1. Retrieve theme
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('/'),
    )
    try:
        template = env.get_template(f'{theme_path}/theme.html')
    except jinja2.exceptions.TemplateNotFound as err:
        raise IOError(f"No such file or directory: '{err}'")

    # 2. Create a html from both the theme and the config file
    html_resume = template.render(config)

    # 3. Add css automatically
    css_list = []
    theme_lsdir = os.listdir(theme_path)
    for theme_file in theme_lsdir:
        [_, ext] = os.path.splitext(theme_file)
        if ext != '.css':
            continue
        css_list.append(os.path.join(theme_path, theme_file))

    # 4. Export a pdf
    html = HTML(string=html_resume, media_type='print')
    doc = html.render(
        stylesheets=css_list,
        optimize_size=('fonts'),
    )
    doc.metadata = metadata
    logger.info(f'export to {output_file}')
    doc.write_pdf(output_file)


def normalize_args(args: argparse.Namespace, config: Config) -> argparse.Namespace:
    now = datetime.now().strftime(DATE_FORMAT)

    if args.auto_metadata:
        if not args.title:
            args.title = args.output
        if not args.created_date:
            try:
                stat = os.stat(args.output)
                args.created_date = datetime.fromtimestamp(stat.st_ctime).strftime(DATE_FORMAT)
            except FileNotFoundError:
                args.created_date = now
        if not args.modified_date:
            args.modified_date = now
        if not args.author:
            args.author = f"{config['profile']['firstname']} {config['profile']['lastname']}"
        if len(args.keyword) == 0:
            args.keyword = ['resume']

    return args


def cmd_build(args: argparse.Namespace) -> int:
    try:
        config = get_config(args.config_path)
    except IOError as err:
        logger.error(err)
        return err.errno
    args = normalize_args(args, config)
    theme_path = args.theme
    if args.theme[0] != '/':
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        theme_path = os.path.abspath(os.path.join(cur_dir, DEFAULT_THEMES_DIR, args.theme))

    metadata = DocumentMetadata(
        title=args.title,
        authors=args.author,
        keywords=args.keyword,
        created=args.created_date,
        modified=args.modified_date,
    )

    try:
        create_resume(config, args.output, theme_path, metadata)
    except IOError as err:
        logger.error(err)
        return err.errno
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, 'config.example.yaml')
    shutil.copyfile(config_file, args.output)
    return 0


def cmd_theme(args: argparse.Namespace) -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    theme_dir = os.path.join(script_dir, DEFAULT_THEMES_DIR, DEFAULT_THEME)
    shutil.copytree(theme_dir, args.output)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    cmdparsers = parser.add_subparsers(dest='command')

    buildparser = cmdparsers.add_parser('build', help='build a resume')
    buildparser.add_argument(
        '--title', type=str,
        help='metadata: title (default to None)',
    )
    buildparser.add_argument(
        '--author', type=str,
        help='metadata: author (default to None)',
    )
    buildparser.add_argument(
        '--keyword', nargs='+', default=[],
        help='metadata: keywords (default to empty list)',
    )
    buildparser.add_argument(
        '--created-date', type=str,
        help='metadata: date of creation YYYY-MM-DD (default to None)',
    )
    buildparser.add_argument(
        '--modified-date', type=str,
        help='metadata: date of modification YYYY-MM-DD (default to None)',
    )
    buildparser.add_argument(
        '--auto-metadata', action='store_true',
        help='auto fill metadata with proper dates, title and keywords',
    )
    buildparser.add_argument(
        '-o', '--output', type=str, default=DEFAULT_OUTPUT_FILENAME,
        help='output file name',
    )
    buildparser.add_argument(
        '-t', '--theme', type=str, default=DEFAULT_THEME,
        help='either the theme name (in themes/) or an absolute path to a theme directory',
    )
    buildparser.add_argument(
        'config_path', type=str,
        help='path to a config yaml file, see config.example.yaml',
    )
    buildparser.set_defaults(cmd=cmd_build)

    initparser = cmdparsers.add_parser('init', help='create a config file')
    initparser.add_argument(
        '-o', '--output', type=str, default=DEFAULT_CONFIG_FILENAME,
        help='output config filename',
    )
    initparser.set_defaults(cmd=cmd_init)

    themeparser = cmdparsers.add_parser('theme', help='create a new theme')
    themeparser.add_argument(
        '-o', '--output', type=str, default=DEFAULT_MYTHEME_NAME,
        help='output theme name',
    )
    themeparser.set_defaults(cmd=cmd_theme)

    args = parser.parse_args()

    # force a cast to int to make mypy happy
    return cast(int, args.cmd(args))


if __name__ == '__main__':
    sys.exit(main())
