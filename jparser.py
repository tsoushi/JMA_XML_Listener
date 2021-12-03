from xml.etree import ElementTree
import datetime
import re

import logging

class EqBase:
    XMLNS = {
            'def': 'http://xml.kishou.go.jp/jmaxml1/',
            'jmx': 'http://xml.kishou.go.jp/jmaxml1/'
    }

    XMLNS_HEAD = {
            'def': 'http://xml.kishou.go.jp/jmaxml1/informationBasis1/'
    }

    XMLNS_BODY = {
            'def': 'http://xml.kishou.go.jp/jmaxml1/body/seismology1/',
            'jmx_eb': 'http://xml.kishou.go.jp/jmaxml1/elementBasis1/'
    }

    def __init__(self, xml):
        self._logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
        
        self._xml = ElementTree.fromstring(xml)

    @property
    def title(self):
        return self._xml.find('def:Head/def:Title', self.XMLNS_HEAD).text

    @property
    def reportDatetime(self):
        return datetime.datetime.fromisoformat(self.reportDatetime_raw)

    @property
    def reportDatetime_raw(self):
        return self._xml.find('def:Head/def:ReportDateTime', self.XMLNS_HEAD).text

    @property
    def eventID(self):
        return self._xml.find('def:Head/def:EventID', self.XMLNS_HEAD).text

    @property
    def infoKind(self):
        return self._xml.find('def:Head/def:InfoKind', self.XMLNS_HEAD).text

    @property
    def headText(self):
        return self._xml.find('def:Head/def:Headline/def:Text', self.XMLNS_HEAD).text

    # headとコメントの情報の概要を文字列にして返す
    def tostring_head(self, indent=0):
        text = ' ' * indent + '{} ({})\n'.format(self.title, self.infoKind)
        text += ' ' * indent + '更新時刻: {}\n'.format(self.reportDatetime)
        text += '\n'
        text += ' ' * indent + self.headText + '\n'
        text += '\n'
        text += ' ' * indent + self.forecastComment
        freeFormComment = self.freeFormComment
        if freeFormComment:
            text += '\n'
            text += '\n'
            text += ' ' * indent + freeFormComment
        return text

    #
    # Comments配下
    #

    @property
    def forecastComment(self):
        return self._xml.find('def:Body/def:Comments/def:ForecastComment/def:Text', self.XMLNS_BODY).text

    @property
    def forecastCommentCode(self):
        return self._xml.find('def:Body/def:Comments/def:ForecastComment/def:Code', self.XMLNS_BODY).text

    # その他の付加的な情報
    @property
    def freeFormComment(self):
        element = self._xml.find('def:Body/def:Comments/def:FreeFormComment/def:Text', self.XMLNS_BODY)
        if element:
            return element.text
        else:
            return ''
    
        
#
# 震源速報
#
class EqHypocenter(EqBase):

    #
    # Earthquake配下
    # (地震の諸要素)
    #

    # 地震の発生時刻
    @property
    def originTime_raw(self):
        return self._xml.find('def:Body/def:Earthquake/def:OriginTime', self.XMLNS_BODY).text
    
    # 地震の発生時刻 (datetime型に変換)
    @property
    def originTime(self):
        return datetime.datetime.fromisoformat(self.originTime_raw)
    
    # 震央地名
    @property
    def hypocenterName(self):
        return self._xml.find('def:Body/def:Earthquake/def:Hypocenter/def:Area/def:Name', self.XMLNS_BODY).text
    
    # 震央地名コード
    @property
    def hypocenterCode(self):
        return self._xml.find('def:Body/def:Earthquake/def:Hypocenter/def:Area/def:Code', self.XMLNS_BODY).text

    # 震源座標、深さ。ISO6709。深さの単位はメートル。
    @property
    def coordinate_raw(self):
        return self._xml.find('def:Body/def:Earthquake/def:Hypocenter/def:Area/jmx_eb:Coordinate', self.XMLNS_BODY).text

    #　震源座標、深さの数値変換。深さの単位をキロメートルに変換。
    @property
    def coordinate(self):
        res = re.search('\+(.*)\+(.*)-(.*)/', self.coordinate_raw)
        lat = float(res[1])
        lon = float(res[2])
        depth = int(res[3])/1000
        return (lat, lon, depth)

    # 震源座標、深さのテキスト表記。
    @property
    def coordinate_text(self):
        return self._xml.find('def:Body/def:Earthquake/def:Hypocenter/def:Area/jmx_eb:Coordinate', self.XMLNS_BODY).get('description')
    
    @property
    def magnitude_raw(self):
        return self._xml.find('def:Body/def:Earthquake/jmx_eb:Magnitude', self.XMLNS_BODY).text

    @property
    def magnitude(self):
        return float(self.magnitude_raw)

    @property
    def magnitude_text(self):
        return self._xml.find('def:Body/def:Earthquake/jmx_eb:Magnitude', self.XMLNS_BODY).get('description')

    # 震源の情報をすべて文字列にして返す
    def tostring_hypocenter(self, indent=0):
        text = ' ' * indent + '発生時刻: {}\n'.format(self.originTime)
        text += ' ' * indent + '震源: {}\n'.format(self.hypocenterName)
        text += ' ' * indent + '　　  {}\n'.format(self.coordinate_text)
        text += ' ' * indent + '規模: {}'.format(self.magnitude_text)
        return text

    def tostring(self):
        text = self.tostring_head() + '\n'
        text += '\n'
        text += self.tostring_hypocenter()
        return text

#
# 震度速報
#
class EqIntensity(EqBase):

    #
    # Intensity/
    # (震度情報. ヘッダ部の「情報形態」(Head/InfoType)が"取消"の場合、出現しない。)
    #

    #
    # Observation/
    # (震度の観測に関する諸要素)
    #

    # 最大震度
    @property
    def maxIntensity_raw(self):
        return self._xml.find('def:Body/def:Intensity/def:Observation/def:MaxInt', self.XMLNS_BODY).text

    @property
    def maxIntensity(self):
        return self.maxIntensity_raw.replace('-', '弱').replace('+', '強')

    # 詳細な震度情報を辞書形式で返す
    #[
    #   {
    #       name: 都道府県名
    #       code: 都道府県コード
    #       areas: [{
    #                   name: 地名
    #                   code: 地名コード
    #                   maxInt: 最大震度
    #       }...]
    #   }...
    #]
    @property
    def intensityVerbose(self):
        prefs = self._xml.findall('def:Body/def:Intensity/def:Observation/def:Pref', self.XMLNS_BODY)

        out = []
        for pref in prefs:
            dic = {}
            dic['name'] = pref.find('def:Name', self.XMLNS_BODY).text
            dic['code'] = pref.find('def:Code', self.XMLNS_BODY).text
            dic['maxInt'] = pref.find('def:MaxInt', self.XMLNS_BODY).text.replace('-', '弱').replace('+', '強')
            dic['areas'] = []

            areas = pref.findall('def:Area', self.XMLNS_BODY)
            for area in areas:
                ddic = {}
                ddic['name'] = area.find('def:Name', self.XMLNS_BODY).text
                ddic['code'] = area.find('def:Code', self.XMLNS_BODY).text
                ddic['maxInt'] = area.find('def:MaxInt', self.XMLNS_BODY).text.replace('-', '弱').replace('+', '強')
                dic['areas'].append(ddic)
            
            out.append(dic)
        return out

    # 詳細な震度情報を文字列にして返す
    def tostring_intensityVerbose(self, indent=0):
        prefs = self.intensityVerbose

        text = ''
        for pref in prefs:
            text += ' ' * indent + '{} Max: {}\n'.format(pref['name'], pref['maxInt'])
            for area in pref['areas']:
                text += ' ' * indent + '    {}: {}\n'.format(area['name'], area['maxInt'])
        return text[:-1]

    def tostring_intensity(self, indent=0):
        text = ' ' * indent + '最大震度: {}\n'.format(self.maxIntensity)
        text += '\n'
        text += ' ' * indent + self.tostring_intensityVerbose()
        return text

    # すべての情報を文字列にして返す
    def tostring(self):
        text = self.tostring_head() + '\n'
        text += '\n'
        text += self.tostring_intensity()
        return text

class EqVerbose(EqHypocenter, EqIntensity):
    def tostring(self):
        text = self.tostring_head() + '\n'
        text += '\n'
        text += self.tostring_hypocenter() + '\n'
        text += '\n'
        text += '\n'
        text += self.tostring_intensity()
        return text
