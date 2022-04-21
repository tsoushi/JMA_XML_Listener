import requests
import json

from lineNotifyTokens import tokens

url = 'https://notify-api.line.me/api/notify'

def lineNotify(message, file=None, tokenName='テスト'):
    headers = {'Authorization': 'Bearer '+tokens[tokenName]}
    params = {'message': message}
    if file == None:
        r = requests.post(url, headers=headers, params=params)
    else:
        r = requests.post(url, headers=headers, params=params, files={'imageFile': file})
    if r.status_code != 200:
        err_message = json.loads(r.content)['message']
        raise Exception('Lineの送信に失敗({})'.format(err_message))

    return r

if __name__ == '__main__':
    res = lineNotify(input('message:'))
    print(res.text)
