#!/usr/bin/python
# -*- coding: utf-8 -*-


import requests
import json
import os
import base64
from Crypto.Cipher import AES


def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext


def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = int(text.encode('hex'), 16)**int(pubKey, 16) % int(modulus, 16)
    return format(rs, 'x').zfill(256)


def createSecretKey(size):
    return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]

#start down here.


def getinfofromnem(url,params):
    headers = {
        'Cookie': 'appver=1.5.0.75771;',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'music.163.com',
        'Referer': 'http://music.163.com/search/',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'
    }
    modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    nonce = '0CoJUm6Qyw8W8jud'
    pubKey = '010001'
    params = json.dumps(params)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(params, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {
        'params': encText,
        'encSecKey': encSecKey
    }
    req = requests.post(url, headers=headers, data=data)
    return req.json()

def getplaylist(uid):
    url = 'http://music.163.com/weapi/user/playlist?csrf_token='
    params = {
        'offset': '0',
        'limit': '9999',
        'uid': uid
    }
    return getinfofromnem(url,params)
    
def getplaylistinfo(listid):
    url = 'http://music.163.com/weapi/playlist/detail?csrf_token='
    params = {'id': listid}
    return getinfofromnem(url,params)
    
def getmusicurl(musicid):
    url = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='
    if type([]) != type(musicid):
        musicid = [musicid]
    params = {
        "ids": musicid,
        "br": '320000'
    }
    return getinfofromnem(url,params)

if __name__=="__main__":
    print "oops,126887679"






