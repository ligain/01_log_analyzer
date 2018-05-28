
# Log analyzer for custom nginx logs
Custom log parse which helps to find 'slow' URLs.

## Simple run
Python *3.5* should be installed in your system.
```
$ git clone https://github.com/ligain/01_log_analyzer.git
$ cd 01_log_analyzer
```
Before running script ensure you have installed correct `REPORT_DIR`, `LOG_DIR`  pathes in `config.json`
```
$ python3 log_analyzer.py --config path/to/config.json
```
or if `config.json` in the same folder as `log_analyzer.py`
```
$ python3 log_analyzer.py
```
Outcome report will be in `REPORT_DIR` with a name like `report-2018.05.28.html`


## How it works:
1) It parses a log file with a name like in `LOG_FILE_TMP` variable
which can be found in path `LOG_DIR`

The log shoud has following data format:
```$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time```

Like:
```
1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390
1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 0.133
```

2) Calculates variables:
`count` ‐ how much time an URL occurs
`count_perc` ‐ how much time an URL occurs by total occurencies in %
`time_sum` ‐ total `$request_time` for an URL
`time_perc` ‐ total `$request_time` for an URL devided by a sum of all `$request_time` values
`time_avg` ‐ avarage `$request_time` for an URL
`time_max` ‐ maximum `$request_time` for an URL
`time_max` ‐ median `$request_time` for an URL

3) Generates HTML report with rows number specified in `REPORT_SIZE`
based on template `REPORT_TMP_NAME` and then puts it in dir `REPORT_DIR`

## Tests
```
$ cd 01_log_analyzer
$ python3 -m unittest tests.py
```

### Project Goals

The code is written for educational purposes.
