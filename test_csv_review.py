import csv
import io
import json
import unittest
from csv_review import review


class ReviewTests(unittest.TestCase):
    def parse(self, text):
        return list(csv.reader(io.StringIO(text, newline='')))

    def test_values_and_quoted_newlines_round_trip(self):
        source = 'id,note\r\n1,"한글, quoted\nnext"\r\n2, leading \r\n'
        result = review(source)
        self.assertEqual(self.parse(result['cleaned.csv']), self.parse(source))

    def test_cells_crossing_default_character_limit_round_trip(self):
        for value in ['x' * 131_072, 'x' * 131_073, '한😀' * 70_000 + ', quoted\nnext']:
            with self.subTest(characters=len(value)):
                output = io.StringIO(newline='')
                csv.writer(output).writerows([['value'], [value]])
                result = review(output.getvalue())
                self.assertEqual(self.parse(result['cleaned.csv']), [['value'], [value]])
                self.assertEqual(json.loads(result['validation.json'])['counts']['output_records'], 1)

    def test_exact_file_byte_limit_allows_ascii_and_multibyte_cells(self):
        budget = 5_000_000 - len('value\n\n'.encode('utf-8'))
        for unit in ['x', '한😀']:
            with self.subTest(unit=unit):
                count, remainder = divmod(budget, len(unit.encode('utf-8')))
                value = unit * count + 'x' * remainder
                source = 'value\n' + value + '\n'
                self.assertEqual(len(source.encode('utf-8')), 5_000_000)
                result = review(source)
                self.assertEqual(self.parse(result['cleaned.csv']), [['value'], [value]])

    def test_multibyte_file_one_byte_over_scope_is_rejected(self):
        budget = 5_000_000 - len('value\n\n'.encode('utf-8'))
        count, remainder = divmod(budget, len('한'.encode('utf-8')))
        source = 'value\n' + '한' * count + 'x' * (remainder + 1) + '\n'
        self.assertEqual(len(source.encode('utf-8')), 5_000_001)
        self.assertLess(len(source), 5_000_000)
        with self.assertRaisesRegex(ValueError, 'File exceeds the 5 MB scope'):
            review(source)

    def test_transformations_are_opt_in(self):
        source = 'id,name\n1, A \n1,A\n'
        self.assertEqual(len(self.parse(review(source)['cleaned.csv'])), 3)
        result = review(source, trim_columns=['name'], drop_exact_duplicates=True)
        self.assertEqual(self.parse(result['cleaned.csv']), [['id', 'name'], ['1', 'A']])
        counts = json.loads(result['validation.json'])['counts']
        self.assertEqual(counts['cells_trimmed'], 1)
        self.assertEqual(counts['exact_duplicates_removed'], 1)

    def test_ragged_rows_are_reported_and_accounted(self):
        result = review('id,name\n1,A\n2\n3,B,extra\n4,D\n')
        counts = json.loads(result['validation.json'])['counts']
        self.assertEqual((counts['input_records'], counts['output_records'], counts['ragged_records']), (4, 2, 2))
        exceptions = self.parse(result['exceptions.csv'])
        self.assertEqual([row[0] for row in exceptions[1:]], ['3', '4'])

    def test_formula_like_values_are_preserved_and_flagged(self):
        result = review('id,value\n1,=1+2\n2,@name\n3,\n')
        self.assertEqual(self.parse(result['cleaned.csv'])[1][1], '=1+2')
        counts = json.loads(result['validation.json'])['counts']
        self.assertEqual(counts['formula_like_cells'], 2)
        self.assertEqual(counts['empty_cells'], 1)

    def test_ambiguous_headers_and_bad_syntax_fail(self):
        for text in ['a,a\n1,2\n', 'a,\n1,2\n', 'id,note\n1,"unfinished\n']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                review(text)

    def test_scope_limits_and_unknown_columns_fail(self):
        with self.assertRaises(ValueError):
            review('id\n1\n2\n', max_rows=1)
        with self.assertRaises(ValueError):
            review('id,name\n1,A\n', max_columns=1)
        with self.assertRaises(ValueError):
            review('id\n1\n', trim_columns=['missing'])

    def test_row_boundary_stops_before_parsing_the_remaining_file(self):
        for limit in [0, 1, 2000]:
            for record in ['1\n', '\n']:
                with self.subTest(limit=limit, blank_record=record == '\n'):
                    source = 'id\n' + record * limit
                    result = review(source, max_rows=limit)
                    self.assertEqual(json.loads(result['validation.json'])['counts']['input_records'], limit)
                    # Reading past the first excess record would raise a syntax
                    # error on this suffix instead of rejecting the row count.
                    overflow = source + record + '"unterminated\n'
                    with self.assertRaisesRegex(ValueError, 'File exceeds the row or column scope'):
                        review(overflow, max_rows=limit)

    def test_header_only_and_bom(self):
        result = review('\ufeffid,name\n')
        self.assertEqual(self.parse(result['cleaned.csv']), [['id', 'name']])
        self.assertEqual(json.loads(result['validation.json'])['counts']['input_records'], 0)


if __name__ == '__main__':
    unittest.main()
