import requests

import jparser
import jmaGetter
from jmaGetter import JMAQuakeXML
from send import send
from config import HOME_NAME

import logging
logger = logging.getLogger(__name__)


#
# 指定回数リトライするリクエスト関数
#
def autoRetryRequest(url, retry=3, timeout=10, sleep=10):
    errCount = 0
    while 1:
        if errCount >= retry:
            raise Exception('exceed the retry count')

        logger.debug('requesting : {}'.format(url))
        try:
            res = requests.get(url)
        except Exception as e:
            errCount += 1
            logger.debug('requesting -> fail : {} : error count {} / {}'.format(e, errCount, retry))
            continue

        if res.status_code != 200:
            errCount += 1
            logger.debug('requesting -> fail : status code {} : error count {} / {}'.format(res.status_code, errCount, retry))
            continue
        else:
            logger.debug('requesting -> complete')
            return res


class MyApp(JMAQuakeXML):
    #
    # 震源情報
    #
    def update_eqCenter(self, data):
        self._logger.info('execute : {}'.format(data['title']))

        res = autoRetryRequest(data['link'])

        ps = jparser.EqHypocenter(res.content)
        text = '\n' + ps.tostring()

        print(text)
        
        send(text)

        self._logger.info('execute : {} -> complete'.format(data['title']))
        

    #
    # 震度速報
    #
    def update_eqIntensity(self, data):
        self._logger.info('execute : {}'.format(data['title']))

        res = autoRetryRequest(data['link'])

        ps = jparser.EqIntensity(res.content)
        text = '\n' + ps.tostring()

        print(text)
        
        if HOME_NAME in [i['name'] for i in ps.intensityVerbose]:
            send(text, emergency=True)

        send(text)

        self._logger.info('execute : {} -> complete'.format(data['title']))

    #
    # 震源・震度情報
    #
    def update_eqVerbose(self, data):
        self._logger.info('execute : {}'.format(data['title']))

        res = autoRetryRequest(data['link'])

        ps = jparser.EqVerbose(res.content)
        text = '\n' + ps.tostring()

        print(text)
        
        if HOME_NAME in [i['name'] for i in ps.intensityVerbose]:
            send(text, emergency=True)

        send(text)

        self._logger.info('execute : {} -> complete'.format(data['title']))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sleep', '-s', default=30, type=int, help='取得頻度')
    parser.add_argument('--loglevel', '-l', default='info', choices=['debug', 'info'], type=str, help='ログ出力レベル')
    parser.add_argument('--notskipfirst', action='store_true', help='すでに発表されている報告をスキップしない')
    #parser.add_argument('--out', '-o', type=str, help='チャットの出力先')

    args = parser.parse_args()

    if args.loglevel == 'debug':
        LOGLEVEL = logging.DEBUG
    elif args.loglevel == 'info':
        LOGLEVEL = logging.INFO
    logger = logging.getLogger(__name__)
    logger_g = logging.getLogger(jmaGetter.__name__)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(LOGLEVEL)
    streamHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(streamHandler)
    logger_g.addHandler(streamHandler)
    logger.setLevel(LOGLEVEL)
    logger_g.setLevel(LOGLEVEL)

    jma = MyApp()
    jma.mainloop(sleep=args.sleep, skipFirst=not args.notskipfirst)
