import pytest
from urllib.parse import urljoin
from parsel import Selector
import avm

PRODUCT_PAGE = u'''<html lang="en">
                       <head>
                           <meta charset="UTF-8">
                           <title>Index of /fritzbox/</title>
                       </head>
                       <body>
                           <pre>
                               <a href="../">../</a>
                               <a href="beta/">beta/</a>
                               01-Jan-2019 02:45 -
                               <a href="fritzbox-1234/">fritzbox-1234/</a>
                               12-Aug-2019 12:13 -
                               <a href="tools/">tools/</a>
                               13-Sep-2017 21:18 -
                               <a href="license.txt">license.txt</a>
                               21-Jun-2018 01:10 28193
                           </pre>
                       </body>
                   </html>'''

LOCATION_PAGE = u'''<html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <title>Index of /fritzbox/fritzbox-1234/</title>
                        </head>
                        <body>
                            <pre>
                                <a href="../">../</a>
                                <a href="deutschland/">deutschland/</a>
                                12-Aug-2019 12:13 -
                                <a href="other/">other/</a>
                                13-Sep-2017 21:18 -
                            </pre>
                        </body>
                    </html>'''

OS_PAGE = u'''<html lang="en">
                  <head>
                      <meta charset="UTF-8">
                      <title>Index of /fritzbox/fritzbox-1234/deutschland/</title>
                  </head>
                  <body>
                      <pre>
                          <a href="../">../</a>
                          <a href="fritz.os/">fritz.os/</a>
                          12-Aug-2019 12:13 -
                          <a href="recover/">recover/</a>
                          13-Sep-2017 21:18 -
                      </pre>
                  </body>
              </html>'''

FIRWMARE_PAGE = u'''<html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <title>Index of /fritzbox/fritzbox-1234/deutschland/fritz.os/</title>
                        </head>
                        <body>
                            <pre>
                                <a href="../">../</a>
                                <a href="FRITZ.Box_1234.image">FRITZ.Box_1234.image</a>
                                12-Aug-2019 12:13 22241280
                                <a href="info_de.txt">info_de.txt</a>
                                13-Sep-2017 21:18 47418
                            </pre>
                        </body>
                    </html>'''


class MockResponse:
    def __init__(self, url, body):
        self.url = url
        self.body = body
        self.request = MockRequest(url, None)

    def urljoin(self, url):
        return urljoin(self.url, url)

    def xpath(self, xpath):
        selector = Selector(text=self.body)
        return selector.xpath(xpath)


class MockRequest:
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback


@pytest.fixture(scope='session', autouse=True)
def spider_instance():
    return avm.AvmSpider()


@pytest.fixture(scope='function', autouse=True)
def mocked_request(mocker):
    return mocker.patch(target='avm.Request', new=MockRequest)


@pytest.fixture(scope='function', autouse=True)
def mocked_download(mocker):

    def item_download(spider_instance, response, path):
        return [MockResponse('/'.join(path) + '/FRITZ.Box_1234.image', None)]

    return mocker.patch.object(avm.AvmSpider, 'prepare_item_download', item_download)


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/', body=PRODUCT_PAGE), ['/fritzbox/fritzbox-1234/'])])
def test_parse(spider_instance, mocked_request, response, expected):
    for index, request in enumerate(spider_instance.parse(response=response)):
        assert request.url == expected[index]


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/fritzbox-1234/', body=LOCATION_PAGE), ['/fritzbox/fritzbox-1234/deutschland/', '/fritzbox/fritzbox-1234/other/']),
                                                (MockResponse(url='/fritzbox/fritzbox-1234/other/', body=OS_PAGE), ['/fritzbox/fritzbox-1234/other/fritz.os/']),
                                                (MockResponse(url='/fritzbox/fritzbox-1234/other/fritz.os/', body=FIRWMARE_PAGE), ['/fritzbox/fritzbox-1234/other/fritz.os/FRITZ.Box_1234.image'])])
def test_parse_product(spider_instance, mocked_request, mocked_download, response, expected):
    for index, request in enumerate(spider_instance.parse_product(response=response)):
        assert request.url == expected[index]


def test_prepare_item_download():
    pass


@pytest.mark.parametrize('response, prefix, expected', [(MockResponse(url='/fritzbox/', body=PRODUCT_PAGE), ('beta', 'tools', 'license', '..'), ['/fritzbox/fritzbox-1234/'])])
def test_link_extractor(spider_instance, response, prefix, expected):
    assert spider_instance.link_extractor(response=response, prefix=prefix) == expected


@pytest.mark.parametrize('response, expected', [(MockResponse(url='/fritzbox/fritzbox-1234/other/fritz.os/', body=FIRWMARE_PAGE), ['12-Aug-2019 12:13', '13-Sep-2017 21:18'])])
def test_date_extractor(spider_instance, response, expected):
    assert spider_instance.date_extractor(response=response) == expected
