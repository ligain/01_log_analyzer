import unittest
import os
import shutil
import inspect

import log_analyzer

TEST_CONFIG = {
    'TEMP_DIR': 'temp',
    'EMPTY_CONF_NAME': 'empty_config.json',
    'BAD_CONF_NAME': 'bad_config.json',
    'LOG_SAMPLE': '''1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
    1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 0.133
    1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 0.199
    1.199.4.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/slot/4705/groups HTTP/1.1" 200 2613 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-3800516057-4708-9752745" "2a828197ae235b0b3cb" 0.704
    1.168.65.96 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/internal/banner/24294027/info HTTP/1.1" 200 407 "-" "-" "-" "1498697422-2539198130-4709-9928846" "89f7f1be37d" 0.146
    1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/1769230/banners HTTP/1.1" 200 1020 "-" "Configovod" "-" "1498697422-2118016444-4708-9752747" "712e90144abee9" 0.628
    1.194.135.240 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28 HTTP/1.1" 200 22 "-" "python-requests/2.13.0" "-" "1498697422-3979856266-4708-9752772" "8a7741a54297568b" 0.067
    1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/1717161 HTTP/1.1" 200 2116 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752771" "712e90144abee9" 0.138
    1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/1717161 HTTP/1.1" 200 2116 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752771" "712e90144abee9" 0.138
    ''',
    'LOG_SAMPLE_FILENAME': 'sample.log'
}


class TestAnalyzer(unittest.TestCase):

    def setUp(self):
        self.config = TEST_CONFIG
        self.analyzer_def_config = log_analyzer.DEFAULT_CONFIG

        os.mkdir(self.config['TEMP_DIR'])
        self.empty_conf_path = os.path.join(
            os.path.abspath(os.getcwd()),
            self.config['TEMP_DIR'],
            self.config['EMPTY_CONF_NAME']
        )
        self.bad_conf_path = os.path.join(
            os.path.abspath(os.getcwd()),
            self.config['TEMP_DIR'],
            self.config['BAD_CONF_NAME']
        )
        self.sample_log_path = os.path.join(
            os.path.abspath(os.getcwd()),
            self.config['TEMP_DIR'],
            self.config['LOG_SAMPLE_FILENAME']
        )

        with open(self.empty_conf_path, 'w') as file:
            file.write('{}')

        with open(self.bad_conf_path, 'w') as file:
            file.write('bad')

        with open(self.sample_log_path, 'w') as file:
            file.write(self.config['LOG_SAMPLE'])

    def test_getting_log_filepath(self):
        path = log_analyzer.get_log_filepath('wrong/path', 'bad.log')
        self.assertIsNone(path)

    def test_empty_config(self):
        empty_conf = log_analyzer.get_config(
            self.empty_conf_path,
            self.analyzer_def_config
        )
        self.assertEqual(self.analyzer_def_config, empty_conf)

    def test_bad_json_config(self):
        empty_conf = log_analyzer.get_config(self.bad_conf_path)
        self.assertIsNone(empty_conf)

    def test_parse_errors(self):
        zero_case = log_analyzer.check_parse_errors(0, 0, 0.1)
        self.assertTrue(zero_case)

        ok_case = log_analyzer.check_parse_errors(100, 1, 0.1)
        self.assertTrue(ok_case)

        bad_case = log_analyzer.check_parse_errors(100, 13, 0.1)
        self.assertFalse(bad_case)

    def test_log_parser(self):
        log_fileobj = log_analyzer.read_log(self.sample_log_path)
        self.assertTrue(inspect.isgenerator(log_fileobj))

        processed_lines = log_analyzer.process_log_lines(
            log_fileobj,
            self.analyzer_def_config['LOG_LINE_PATTERN']
        )
        self.assertTrue(inspect.isgenerator(processed_lines))

        statistics = log_analyzer.count_statistics(list(processed_lines))
        self.assertIsInstance(statistics, list)
        print('statistics', statistics)

    def tearDown(self):
        shutil.rmtree(self.config['TEMP_DIR'])


if __name__ == '__main__':
    unittest.main()
