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
  --list-cfg LIST_CFG, --cfg LIST_CFG, -c LIST_CFG
                        yaml config file for list indices
```

### Example Output

```sh
poetry run odiff aux/eg1.json aux/eg2.json -c aux/eg-list-cfg.yaml
```

```txt
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

## List Index Configuration

You may have spotted in the [Example Output](#example-output) that we pass the `-c` option (`--list-config`) and that the output made use of this key in the children of `.delta` to "align" the list elements together - this allows us to diff matching objects despite them not necessarily being the correct order.

The format of this is a simple string-string, key-value pairing in YAML, e.g.:

```yaml
.delta: _id
```

You can see it takes a [JQ](https://jqlang.github.io/jq/)-ish form for the object pathing. So, if your input is a list of object, you should provide an index for the `.` key.

## Contributing

This repo uses [Pre-commit](https://pre-commit.com/) for some sanity checks, so:

```sh
pre-commit install
```

There are literally zero tests aside the examples...
