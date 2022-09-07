# resumy

[![PyPI version](https://badge.fury.io/py/resumy.svg)](https://badge.fury.io/py/resumy)
![build status](https://github.com/alexlren/estel_secp256k1/actions/workflows/ci.yaml/badge.svg)

<img src="/docs/demo.png" width="300"/>

## Install

```
pip install resumy
```

If you are on Windows (10 or 11), you will also need to install the GTK for Windows Runtime Environment installer. You can install this [here](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)

## Commands

### Usage

```
resumy --help
```

### Init a config file

```
resumy init -o myconfig.yaml
```

It makes it easier to support multiple languages (i.e. multiple config files)

### Build a resume

```
resumy build -o myresume.pdf myconfig.yaml
```

### Create and use your own theme

```
resumy theme mytheme -o /tmp/mytheme
```

Now you can simply edit /tmp/mytheme/theme.html and /tmp/mytheme/theme.css, and use your custom theme with `--theme` option.

```
resumy build -o myresume.pdf --theme /tmp/mytheme myconfig.yaml
```

## Development

1. Create a virtual env

```
python -m venv venv
source venv/bin/activate
```

2. Install dependencies

```
pip install -e .
```

2. Create a config file

```
cp config.example.yaml my_config.yaml
```

or

```
python src/resumy/resumy.py init
```

3. Run

```
python resumy/resumy.py build -o my_resume.pdf my_config.yaml
```

## Tests

### Linting with flake8

```
tox -e flake8
```

### Type checking with mypy

```
tox -e mypy
```
