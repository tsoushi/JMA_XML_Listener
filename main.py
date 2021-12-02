from xml.etree import ElementTree
import requests
import time
import datetime
import threading

import logging
logger = logging.getLogger(__name__)


class JMAQuakeXML:
    URL = 'http://www.data.jma.go.jp/developer/xml/feed/eqvol.xml'
    XML_NAMESPACE = {'def': 'http://www.w3.org/2005/Atom'}
    #
    # init
    #
    def __init__(self):
        self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
        
        self.feed_lastModified = None # 最後に取得したフィードの更新時間を記録する
        self.feed_idList = []

    #
    # メインループ
    #
    def mainloop(self, skipFirst=True, sleep=30):
        if skipFirst:
            self.initIdList()
        else:
            self.checkFeed()

        while 1:
            self._logger.info('wait {} seconds'.format(sleep))
            time.sleep(sleep)
            self.checkFeed()
    
    #
    # lastModifiedの値をもとに、更新されていた場合のみ、フィードを取得する
    #
    def getFeed(self):
        self._logger.info('getting feed')

        headers = {}
        headers['If-Modified-Since'] = self.feed_lastModified

        try:
            res = requests.get(self.URL, headers=headers)
        except requests.exceptions.ConnectionError:
            self._logger.warning('connection error')
            return None
        except requests.exceptions.ReadTimeout:
            self._logger.warning('connection timeout error')
            return None

        if res.status_code == 304:
            self._logger.info('feed is not modified')
            return None

        if res.status_code != 200:
            self._logger.warning('request error : status code {}'.format(res.status_code))
            return None

        self.feed_lastModified = res.headers['Last-Modified']

        self._logger.info('getting feed -> complete')
        return res

    #
    # self.feed_idList を現在のfeedで初期化する
    #
    def initIdList(self):
        self._logger.info('initializing id list')

        res = self.getFeed()
        if res == None:
            self._logger.error('initializing id list -> error')
            raise Exception('connection error')


        # XMLからidをのリストを取得する
        self._logger.info('parsing xml')

        xml = res.content.decode('utf-8')
        root = ElementTree.fromstring(xml)
        ids = root.findall('def:entry/def:id', self.XML_NAMESPACE)
        ids = [i.text for i in ids]

        self.feed_idList = ids

        self._logger.info('initializing id list -> complete')


    #
    # 新しいentry以外を除外し、情報をパースする
    #
    def filterAndParseEntries(self, entries):
        out_entries = []
        for entry in entries:
            entryId = entry.find('def:id', self.XML_NAMESPACE).text
            if entryId not in self.feed_idList:
                entryData = {}
                entryData['title'] = entry.find('def:title', self.XML_NAMESPACE).text
                entryData['author'] = entry.find('def:author/def:name', self.XML_NAMESPACE).text
                entryData['id'] = entryId
                entryData['content'] = entry.find('def:content', self.XML_NAMESPACE).text
                entryData['link'] = entry.find('def:link', self.XML_NAMESPACE).get('href')
                out_entries.append(entryData)
                
                self.feed_idList.append(entryId)

        return out_entries

    #
    # feedの更新確認をし、更新されていた場合、処理を行う
    #
    def checkFeed(self):
        self._logger.info('checking feed')

        res = self.getFeed()
        if res == None:
            return

        # parse xml
        self._logger.info('parsing xml')

        xml = res.content.decode('utf-8')
        root = ElementTree.fromstring(xml)
        entries = root.findall('def:entry', self.XML_NAMESPACE)

        entryDatas = self.filterAndParseEntries(entries)

        self._logger.info('{} entries was found'.format(len(entries)))

        # entry処理
        for data in entryDatas:
            func = None
            args = (data,)
            if data['title'] == '震源に関する情報':
                func = self.update_eqCenter
            elif data['title'] == '震度速報':
                func = self.update_eqIntensity
            elif data['title'] == '震源・震度に関する情報':
                func = self.update_eqVerbose

            if func:
                threading.Thread(target=func, args=args).start()
        
        self._logger.info('checking feed -> complete')
        return

    def update_eqCenter(self, data):
        self._logger.info(data['title'])
        pass

    def update_eqIntensity(self, data):
        self._logger.info(data['title'])
        pass

    def update_eqVerbose(self, data):
        self._logger.info(data['title'])
        pass

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
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(LOGLEVEL)
    streamHandler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(streamHandler)
    logger.setLevel(LOGLEVEL)

    jma = JMAQuakeXML()
    jma.mainloop(sleep=args.sleep, skipFirst=not args.notskipfirst)
