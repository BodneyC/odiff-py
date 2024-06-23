<!-- markdownlint-disable MD013 -->

# Object Diff

Object diff (`odiff`) is a little tool/library for diffing objects - it's a little specific in a couple of places to a thing I'm doing at work but it might be useful elsewhere.

Essentially, you feed it two files, JSON or YAML, to compare and discrepancies are listed in the console.

## Usage

```txt
usage: odiff [-h] [--log-level LOG_LEVEL] [--output-type OUTPUT_TYPE]
             [--list-cfg LIST_CFG]
             [files ...]

positional arguments:
  files                 two files to diff

options:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        log level name
  --output-type OUTPUT_TYPE, --output OUTPUT_TYPE, -o OUTPUT_TYPE
                        report output flavour
  --config CONFIG, -c CONFIG
                        yaml config file
```

### Example Output

```sh
odiff -c aux/eg-cfg.yaml aux/eg1.json aux/eg2.json
```

```txt
[WARN:odiff] Discrepancy found for path '.alpha' but was excluded
╭──────────────┬────────────┬────────────────┬───────────────────────╮
│ Variant      │ Path       │ Lvalue         │ Rvalue                │
├──────────────┼────────────┼────────────────┼───────────────────────┤
│ modification │ .beta      │ world          │ , world               │
├──────────────┼────────────┼────────────────┼───────────────────────┤
│ subtraction  │ .gamma[]   │ None           │ [                     │
│              │            │                │   "isn't",            │
│              │            │                │   "not-in-eg1"        │
│              │            │                │ ]                     │
├──────────────┼────────────┼────────────────┼───────────────────────┤
│ addition     │ .gamma[]   │ [              │ None                  │
│              │            │   "is",        │                       │
│              │            │   "not-in-eg2" │                       │
│              │            │ ]              │                       │
├──────────────┼────────────┼────────────────┼───────────────────────┤
│ subtraction  │ .delta[    │ None           │ {                     │
│              │   Ct2fhriU │                │   "_id": "Ct2fhriU",  │
│              │ ]          │                │   "key1": "i'm added" │
│              │            │                │ }                     │
├──────────────┼────────────┼────────────────┼───────────────────────┤
│ modification │ .delta[    │ value0         │ i've been modified    │
│              │   vCjpIL2A │                │                       │
│              │ ].key0     │                │                       │
╰──────────────┴────────────┴────────────────┴───────────────────────╯
```

Instead of using a configuration file (see [Configuration](#configuration)) you can also provide the same configuration directly in the command:

```sh
odiff aux/eg1.json aux/eg2.json --li '.delta: _id' --exc '.alpha'
```

## Configuration

### List Index Configuration

You may have spotted in the [Example Output](#example-output) that we pass the `-c` option (`--list-config`) and that the output made use of this key in the children of `.delta` to "align" the list elements together - this allows us to diff matching objects despite them not necessarily being the correct order.

The format of this is a simple string-string, key-value pairing in YAML, e.g.:

```yaml
.delta: _id
```

You can see it takes a [JQ](https://jqlang.github.io/jq/)-ish form for the object pathing. So, if your input is a list of object, you should provide an index for the `.` key.

### Exclusions

Another thing you may have spotted in the output is the log line at the top about the excluded discrepancy on `.alpha`.

This is what the `.exclusions` list is for, anything you wish to ignore in either the left or right file can be listed here.

## Contributing

This repo uses [Pre-commit](https://pre-commit.com/) for some sanity checks, so:

```sh
pre-commit install
```

There are literally zero tests aside the examples...
