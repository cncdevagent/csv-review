"""Small, dependency-free CSV review with explicit, limited transformations."""
import argparse
import csv
import io
import json
from itertools import islice
from pathlib import Path


MAX_FILE_BYTES = 5_000_000
# csv limits decoded characters. No UTF-8 cell can exceed the file's byte
# budget; configure the process-wide parser once without lowering a higher limit.
csv.field_size_limit(max(csv.field_size_limit(), MAX_FILE_BYTES))


def csv_text(rows):
    output = io.StringIO(newline='')
    csv.writer(output).writerows(rows)
    return output.getvalue()


def review(text, *, trim_columns=(), drop_exact_duplicates=False, max_rows=2000, max_columns=20):
    """Return cleaned CSV, exception CSV and accounting; never infer missing values.

    Ragged rows are excluded into exceptions. Exact duplicate removal happens
    only when requested, after the selected whitespace transformations.
    Values that look like spreadsheet formulas are flagged, never evaluated.
    """
    if len(text.encode('utf-8')) > MAX_FILE_BYTES:
        raise ValueError('File exceeds the 5 MB scope')
    try:
        reader = csv.reader(io.StringIO(text.lstrip('\ufeff'), newline=''), strict=True)
        # Header, allowed records, and one extra record to detect overflow.
        rows = list(islice(reader, max_rows + 2))
    except csv.Error as error:
        raise ValueError('CSV syntax needs clarification') from error
    if not rows:
        raise ValueError('A header row is required')
    header, data = rows[0], rows[1:]
    if not header or any(not value.strip() for value in header) or len(set(header)) != len(header):
        raise ValueError('Headers must be non-empty and unique')
    if len(header) > max_columns or len(data) > max_rows:
        raise ValueError('File exceeds the row or column scope')
    if isinstance(trim_columns, str) or any(column not in header for column in trim_columns):
        raise ValueError('Only named existing columns may be trimmed')
    if not isinstance(drop_exact_duplicates, bool):
        raise ValueError('Duplicate policy must be an explicit boolean')
    trimmed = {header.index(column) for column in trim_columns}
    cleaned = [header]
    exceptions = [['source_record', 'reason', 'original_row_json']]
    seen = set()
    counts = {'input_records': len(data), 'output_records': 0, 'ragged_records': 0,
              'exact_duplicates_removed': 0, 'cells_trimmed': 0,
              'empty_cells': 0, 'formula_like_cells': 0}
    for number, original in enumerate(data, 2):
        if len(original) != len(header):
            counts['ragged_records'] += 1
            exceptions.append([number, 'Column count differs from header', json.dumps(original, ensure_ascii=False)])
            continue
        row = list(original)
        for index in trimmed:
            value = row[index].strip()
            counts['cells_trimmed'] += value != row[index]
            row[index] = value
        key = tuple(row)
        if drop_exact_duplicates and key in seen:
            counts['exact_duplicates_removed'] += 1
            exceptions.append([number, 'Exact duplicate after requested transformations', json.dumps(original, ensure_ascii=False)])
            continue
        seen.add(key)
        counts['empty_cells'] += sum(value == '' for value in row)
        counts['formula_like_cells'] += sum(value.lstrip().startswith(('=', '+', '-', '@')) for value in row if value)
        cleaned.append(row)
    counts['output_records'] = len(cleaned) - 1
    assert counts['input_records'] == counts['output_records'] + counts['ragged_records'] + counts['exact_duplicates_removed']
    report = {
        'counts': counts,
        'rules': {'trim_columns': list(trim_columns), 'drop_exact_duplicates': drop_exact_duplicates},
        'limitations': ['No missing values inferred; no semantic correction or external enrichment.',
                        'CSV formatting may be rewritten while cell values are preserved by default.',
                        'Formula-like cells are flagged and preserved as text; this tool never evaluates them.',
                        'A source record is a parsed CSV record, not necessarily a physical line.'],
    }
    return {'cleaned.csv': csv_text(cleaned), 'exceptions.csv': csv_text(exceptions),
            'validation.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv', type=Path)
    parser.add_argument('output_directory', type=Path)
    parser.add_argument('--trim-column', action='append', default=[])
    parser.add_argument('--drop-exact-duplicates', action='store_true')
    args = parser.parse_args()
    if args.input_csv.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('File exceeds the 5 MB scope')
    with args.input_csv.open(encoding='utf-8-sig', newline='') as source:
        result = review(source.read(), trim_columns=args.trim_column,
                        drop_exact_duplicates=args.drop_exact_duplicates)
    # A new result directory prevents overwriting the buyer's existing files.
    args.output_directory.mkdir(parents=True, exist_ok=False)
    for filename, content in result.items():
        (args.output_directory / filename).write_text(content, encoding='utf-8', newline='')


if __name__ == '__main__':
    main()
