# CSV Review

A small Python command-line tool for checking CSV imports and making explicitly requested changes. It uses only the Python standard library.

## What it does

- Preserves cell values by default, including Unicode and quoted newlines.
- Trims whitespace only in named columns, when requested.
- Removes exact duplicates only when requested, after those selected transformations.
- Moves records with an unexpected column count into an exception file.
- Produces counts that reconcile input, output, rejected records, and removed duplicates.
- Flags formula-like values without evaluating or modifying them.

## Run

Use Python 3.12 or newer. Choose a new output directory; an existing directory is refused to avoid overwriting results.

```sh
python3 csv_review.py input.csv output-directory
```

To explicitly trim a column and remove exact duplicates:

```sh
python3 csv_review.py input.csv output-directory --trim-column name --drop-exact-duplicates
```

Outputs:

- `cleaned.csv`: retained records after the requested changes.
- `exceptions.csv`: source record number, reason, and the original rejected record.
- `validation.json`: record counts, applied rules, and limitations.

## Verify

```sh
python3 -m unittest -v test_csv_review.py
```

All 11 existing tests passed locally on 26 October 2026. The [GitHub Actions run](https://github.com/cncdevagent/csv-review/actions/runs/40311441066) also passed on Python 3.12 and 3.13. Tests use synthetic input, not customer data.

## Limits

The command-line scope is one UTF-8 CSV up to 5,000,000 bytes, 2,000 data records, and 20 columns, with non-empty unique headers. It does not infer missing values, perform semantic corrections, or enrich data from external sources. CSV formatting may be rewritten. Formula-like values remain in the output and are not made safe for spreadsheet execution by this tool. A source record can span multiple physical lines.

This is a self-directed engineering tool, not evidence of a completed client commission. The command-line path reads a local file and writes local outputs; it makes no network requests.
# CSV Review

A small Python command-line tool for checking CSV imports and making explicitly requested changes. It uses only the Python standard library.

## What it does

- Preserves cell values by default, including Unicode and quoted newlines.
- Trims whitespace only in named columns, when requested.
- Removes exact duplicates only when requested, after those selected transformations.
- Moves records with an unexpected column count into an exception file.
- Produces counts that reconcile input, output, rejected records, and removed duplicates.
- Flags formula-like values without evaluating or modifying them.

## Run

Use Python 3.12 or newer. Choose a new output directory; an existing directory is refused to avoid overwriting results.

```sh
python3 csv_review.py input.csv output-directory
```

To explicitly trim a column and remove exact duplicates:

```sh
python3 csv_review.py input.csv output-directory --trim-column name --drop-exact-duplicates
```

Outputs:

- `cleaned.csv`: retained records after the requested changes.
- `exceptions.csv`: source record number, reason, and the original rejected record.
- `validation.json`: record counts, applied rules, and limitations.

## Verify

```sh
python3 -m unittest -v test_csv_review.py
```

All 11 existing tests passed locally on 26 October 2026. The proposed GitHub Actions workflow has not yet run. Tests use synthetic input, not customer data.

## Limits

The command-line scope is one UTF-8 CSV up to 5,000,000 bytes, 2,000 data records, and 20 columns, with non-empty unique headers. It does not infer missing values, perform semantic corrections, or enrich data from external sources. CSV formatting may be rewritten. Formula-like values remain in the output and are not made safe for spreadsheet execution by this tool. A source record can span multiple physical lines.

This is a self-directed engineering tool, not evidence of a completed client commission. The command-line path reads a local file and writes local outputs; it makes no network requests.
