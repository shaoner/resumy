# resumy

[![PyPI version](https://badge.fury.io/py/resumy.svg)](https://badge.fury.io/py/resumy)
![build status](https://github.com/alexlren/estel_secp256k1/actions/workflows/ci.yaml/badge.svg)

<img src="/docs/demo.png" width="300"/>

### Features

- Now supports the [jsonresume](https://jsonresume.org/schema/) format
- A default theme already supported
- Easy to create a theme or a config file
- Configs and schemas are both in yaml format
- Exports a pdf

## Install

```
pip install resumy
```

**It may not work out of the box as some external dynamic libraries are necessary depending on your platform, please take a look at the weasyprint documentation page: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html**

## Commands

### Usage

```
resumy --help
```

### Init a config file

```
resumy init -o myconfig.yaml
```

This creates a file that you can easily edit:

```
basics:
  email: anakin@skywalker.com
  location:
    city: Mos Eisley
    countryCode: Tatooine
  name: Anakin Skywalker
  phone: 123-456-7890
  profiles:
  - network: Github
    url: https://github.com/alexlren
    username: alexlren
  - network: Linkedin
    url: https://www.linkedin.com/anakin
    username: anakin
  url: https://shaoner.com
education:
- area: Jedi / General
  institution: Jedi Academy
  startDate: '2011-01-01'
projects:
- description: a multiplatform gameboy engine
  keywords:
  - Rust
  - React.js
  name: padme
  url: https://padme.cc
skills:
- keywords:
  - Rust
  - Python
  name: Languages
work:
- highlights:
  - Killed a few rebels here and there
  - Tracked Jedi all around the galaxy
  - Practiced the force with my master Darth Sidious
  - Killed some younglings
  name: Empire
  position: Darth Vader
  startDate: '2016-08-01'
```

And it makes it easier to support multiple languages (i.e. multiple config files)

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

## Migrating from v0.0.2

It's now possible to transform the previous resumy format into the jsonresume standard:

```
resumy normalize my_config.yaml -s jsonresume.yaml -o my_new_config.yaml
```

You can still use the original format, it is internally transformed into the new format

```
resumy build -o myresume.pdf --schema resumy.yaml myconfig.yaml
```

The old theme is not supported anymore, but it's not that hard to migrate it yourself.

## Tests

### Linting with flake8

```
tox -e flake8
```

### Type checking with mypy

```
tox -e mypy
```
