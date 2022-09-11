import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, cast

import jinja2
import yaml
from jsonschema import ValidationError, validate
from weasyprint import HTML  # type: ignore
from weasyprint.document import DocumentMetadata  # type: ignore

DATE_FORMAT = '%Y-%m-%d'
DEFAULT_OUTPUT_FILENAME = 'out.pdf'
DEFAULT_CONFIG_FILENAME = 'myconfig.yaml'
DEFAULT_MYTHEME_NAME = 'mytheme'
DEFAULT_SCHEMAS_DIR = 'schemas'
DEFAULT_SCHEMA = 'jsonresume.yaml'
DEFAULT_THEMES_DIR = 'themes'
DEFAULT_THEME = 'prairie'

# Type aliases
Yaml = Dict[str, Any]

# Setup logger
logger = logging.getLogger('resumy')
logger.setLevel(logging.INFO)


def load_yaml(config_path: str) -> Yaml:
    config = {}
    with open(config_path, 'r') as stream:
        config = yaml.safe_load(stream)
    return config


def validate_config(config: Yaml, schema_file: str) -> None:
    if schema_file[0] != '/':
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.abspath(os.path.join(cur_dir, DEFAULT_SCHEMAS_DIR, schema_file))
    else:
        schema_path = schema_file
    schema = load_yaml(schema_path)
    validate(instance=config, schema=schema)


def create_resume(config: Yaml,
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


def normalize_args(args: argparse.Namespace, config: Yaml) -> argparse.Namespace:
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


def get_month_from(date: Yaml) -> str:
    if 'month' in date:
        return datetime.strptime(date['month'], '%b').strftime('%m')
    return '01'


def from_resumy_to_jsonschema(config: Yaml) -> Yaml:  # noqa: C901
    profile = config['profile']
    new_config: Yaml = {
        'meta': {
            'breaks_before': {},
        },
        'basics': {
            'name': f"{profile['firstname']} {profile['lastname']}",
            'email': profile['email'],
            'phone': profile['phone'],
            'url': profile['portfolio_url'],
            'profiles': [],
        },
    }
    if profile['city'] or profile['country']:
        new_config['basics']['location'] = {
            'city': profile['city'],
            'countryCode': profile['country'],
        }
    if profile['github_username']:
        new_config['basics']['profiles'].append({
            'network': 'Github',
            'username': profile['github_username'],
            'url': f"https://github.com/{profile['github_username']}",
        })
    if profile['linkedin_username']:
        new_config['basics']['profiles'].append({
            'network': 'Linkedin',
            'username': profile['linkedin_username'],
            'url': f"https://www.linkedin.com/{profile['linkedin_username']}",
        })
    if config['skills']:
        if 'include_page_break' in config['skills']:
            new_config['meta']['breaks_before']['skills'] = True
        new_config['skills'] = []
        for skillcat in config['skills']['content']:
            new_config['skills'].append({
                'name': skillcat['title'],
                'keywords': [skill['name'] for skill in skillcat['content']],
            })
    if config['job_experience']:
        if 'include_page_break' in config['job_experience']:
            new_config['meta']['breaks_before']['work'] = True
        new_config['work'] = []
        for work in config['job_experience']['content']:
            from_month = get_month_from(work['from'])
            new_work = {
                'name': work['company_name'],
                'position': work['title'],
                'startDate': f"{work['from']['year']}-{from_month}-01",
                'highlights': work['description'],
            }
            if 'present' not in work and 'to' in work:
                to_month = get_month_from(work['to'])
                new_work['endDate'] = f"{work['to']['year']}-{to_month}-01"
            new_config['work'].append(new_work)
    if config['education']:
        if 'include_page_break' in config['education']:
            new_config['meta']['breaks_before']['education'] = True
        new_config['education'] = []
        for edu in config['education']['content']:
            from_month = get_month_from(edu['from'])
            new_edu = {
                'institution': edu['company_name'],
                'area': edu['title'],
                'startDate': f"{edu['from']['year']}-{from_month}-01",
            }
            if 'present' not in work:
                to_month = get_month_from(edu['to'])
                new_work['endDate'] = f"{edu['to']['year']}-{to_month}-01"
            new_config['education'].append(new_edu)
    if config['projects']:
        if 'include_page_break' in config['projects']:
            new_config['meta']['breaks_before']['projects'] = True
        new_config['projects'] = []
        for project in config['projects']['content']:
            new_project = {
                'name': project['name'],
                'description': project.get('description', ''),
                'keywords': [skill['name'] for skill in project['skills']],
            }
            if 'url' in project:
                new_project['url'] = project['url']

            new_config['projects'].append(new_project)
    return new_config


def cmd_build(args: argparse.Namespace) -> int:
    try:
        config = load_yaml(args.config_path)
        if not args.disable_validation:
            validate_config(config, args.schema)
    except ValidationError as err:
        logger.error('Validation error')
        logger.error(err)
        return 2
    except IOError as err:
        logger.error(err)
        return err.errno

    args = normalize_args(args, config)
    # Not perfect but try to detect if the config is resumy or jsonresume friendly
    if 'version' in config and config['version'] == '0.0.1':
        config = from_resumy_to_jsonschema(config)
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


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        config = load_yaml(args.config_path)
        validate_config(config, args.schema)
    except ValidationError as err:
        logger.error('Validation error')
        logger.error(err)
        return 2
    else:
        print('Your config file is valid ✔')  # noqa: T201
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


def cmd_normalize(args: argparse.Namespace) -> int:
    try:
        config = load_yaml(args.config_path)
        validate_config(config, 'resumy.yaml')
    except ValidationError as err:
        logger.error('Validation error')
        logger.error(err)
        return 2

    new_config = from_resumy_to_jsonschema(config)
    with open(args.output, 'w') as yfile:
        yaml.dump(new_config, yfile)

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
        '-s', '--schema', type=str, default=DEFAULT_SCHEMA,
        help='either the schema name (in schemas/) or an absolute path to a schema file',
    )
    buildparser.add_argument(
        '--disable-validation', action='store_true',
        help='Disable schema validation, in case you want your own customization',
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

    validateparser = cmdparsers.add_parser('validate', help='check that a config file is valid')
    validateparser.add_argument(
        '-s', '--schema', type=str, default=DEFAULT_SCHEMA,
        help='either the schema name (in schemas/) or an absolute path to a schema file',
    )
    validateparser.add_argument(
        'config_path', type=str,
        help='path to a config yaml file, see config.example.yaml',
    )
    validateparser.set_defaults(cmd=cmd_validate)

    normparser = cmdparsers.add_parser('normalize',
                                       help='transform a config to the jsonresume format')
    normparser.add_argument(
        'config_path', type=str,
        help='path to a config yaml file, see config.example.yaml',
    )
    normparser.add_argument(
        '-o', '--output', type=str, default=DEFAULT_CONFIG_FILENAME,
        help='output config filename',
    )
    normparser.set_defaults(cmd=cmd_normalize)

    args = parser.parse_args()

    # force a cast to int to make mypy happy
    return cast(int, args.cmd(args))


if __name__ == '__main__':
    sys.exit(main())
