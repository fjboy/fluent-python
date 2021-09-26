from six.moves import urllib_parse

from fp_lib.http import httpclient


class InfluxDBClient(httpclient.RestClient):
    WRITE_URL = '/write'

    def __init__(self, host, database, port=8086,
                 user='', password='', **kwargs):
        super(InfluxDBClient, self).__init__(host, port, **kwargs)
        self.user = user
        self.password = password
        self.database = database

    def query(self, meansurement, fields, filters):
        sql = 'select {0} from {1} where {2}'.format(
            ','.join(fields), meansurement, filters
        )

        url = '/query?{0}'.format(
            urllib_parse.urlencode({'db': self.database, 'q': sql})
        )
        resp = self.get(url)
        return resp

    def write(self, measurement, tags, fields):
        """InfluxDB sql:
           insert into <policy> measurement,tags fields <timestamp>
           tags: tagsKey1=tagValue1,...
           fields: fieldKey1=fieldValue1,...
        """
        tags_list = ','.join(
            ['{0}={1}'.format(k, v) for k, v in tags.items()])
        fields_list = ','.join(
            ['{0}={1}'.format(k, v) for k, v in fields.items()])
        data_body = '{0},{1} {2}'.format(measurement, tags_list, fields_list)
        url = '{0}?{1}'.format(
            self.WRITE_URL,
            urllib_parse.urlencode(self.get_write_url_params()))
        resp = self.post(url, data_body, headers=self.headers)
        return resp

    def create_database(self):
        sql = 'CREATE DATABASE {0}'.format(self.database)
        url = '/query?{0}'.format(urllib_parse.urlencode({'q': sql}))
        resp = self.get(url)
        return resp

    def get_write_url_params(self):
        return {'db': self.database}


class InfluxDBClientV2(InfluxDBClient):
    """Influxdb v2 Client
    E.g.

    >>> token = 'xtiFkVpkMSQmF6YtL6CjTOPDJ4BqIpDN2TSJrfROGwM0kbYT0aQt1m7xJ9bW'
    >>> client = InfluxDBClientV2('host1', 'test_bucket', 'test_bucket', token)
    >>> client.write('mem', {'host': 'host1'},
                     {'used_percent': 100})
    """
    BASE_URL = '/api/v2'
    WRITE_URL = '{0}/write'.format(BASE_URL)

    def __init__(self, host, bucket, org, token, **kwargs):
        super(InfluxDBClientV2, self).__init__(host, bucket,
                                               **kwargs)
        self.org = org
        self.token = token

    @property
    def bucket(self):
        return self.database

    @property
    def headers(self):
        return {"Content-Type": "application/json",
                'Authorization': 'Token {0}'.format(self.token)}

    def get_write_url_params(self):
        return {'org': self.org, 'bucket': self.bucket}
