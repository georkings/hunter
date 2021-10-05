import requests
import os
import codecs
import sys
import asyncio
import pickle
import re
from datetime import datetime
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
}
baseUrl = 'www.tuenvio.cu'
stateIn = None
deptStates = None
getItemsContent = None
if os.path.isfile('getItems.html'):
    with open('getItems.html', 'r') as file:
        getItemsContent = str.encode(file.read())
timeoutValue = 120
fatResponse = 300000
session = requests.Session()
shopIndex, shopIndexCaptcha = None, None
shopList = ['pinar', 'artemisa', 'lahabana', 'carlos3',  'tvpedregal', 'caribehabana', 'almacencaribe', 'mayabeque-tv', 'matanzas', 'cienfuegos', 'villaclara',\
'sancti', 'ciego', 'camaguey', 'tunas', 'holguin', 'granma', 'santiago', 'caribesantiago', 'guantanamo', 'isla']
depPidMap = {
    'tvpedregal': '55',
    'caribehabana': '46087',
    'caribesantiago': '46087',
    'almacencaribe': '46087'
}

baseData = {
    '__EVENTARGUMENT': '',
    '__LASTFOCUS': '',
    'Language': 'es-MX',
    'CurrentLanguage': 'es-MX',
    'Currency': '',
    # 'ctl00$taxes$listCountries': '54'
}

def saveLogs(log):
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + log)
    if not os.path.isdir('logs'): os.mkdir('logs')
    if not os.path.isdir('logs/' + username): os.mkdir('logs/' + username)
    file = codecs.open('logs/' + username + '/tuenvio.log', 'a', encoding='utf-8', errors='ignore')
    file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + log + '\n')
    file.close()

def saveContent(content, tail):
    file = codecs.open('logs/' + username + '/content' + datetime.now().strftime('_%Y%m%d_%H%M%S_') + tail + '.html', 'w', encoding='utf-8', errors='ignore')
    file.write(codecs.escape_decode(bytes(content, "utf-8"))[0].decode("utf-8"))
    file.close()

def isItRedirect(status_code):
    return status_code == 301 or \
      status_code == 302 or \
      status_code == 303 or \
      status_code == 307 or \
      status_code == 308

def isAntiScraping(body):
    return len(body) < 10000 and 'slowAES.decrypt' in body

def toNumbers(hex_str):
    return list(binascii.unhexlify(hex_str))

def toHex(int_list):
    return binascii.hexlify(bytearray(int_list)).decode()

def antiScraping(body):
    global session
    url = body.split('location.href = "')[1].split('"')[0]
    a = body.split('a = toNumbers("')[1].split('"')[0]
    b = body.split('b = toNumbers("')[1].split('"')[0]
    c = body.split('c = toNumbers("')[1].split('"')[0]

    cookie_key = "ASP.KLR"
    cookie_value = toHex(myAES.decrypt(toNumbers(c), toNumbers(a), toNumbers(b)))
    print('cookie anti scraping: ' + cookie_value)
    session.cookies.set(cookie_key, cookie_value)
    
    return url

def getAntiScraping(url):
    global session
    for i in range(6):
        saveLogs('getAntiScraping URL: ' + url)
        if url.endswith('attempt=2') or url.endswith('attempt=3'):
            url = url.split('attempt=')[0];
            url = url.substring(0, url.length - 1);
        
        while True:
            try:
                response = session.get(url, timeout=timeoutValue, allow_redirects=False)
                break
            except requests.exceptions.SSLError as ex:
                saveLogs('$$$$$$$$$$$$$$ SSLError getAntiScraping $$$$$$$$$$$$$')
                sleep(1)
        
        # saveLogs('response.history: ' + str(response.history))
        # saveLogs('response.url: ' + response.url)
        # saveLogs('STATUS: ' + str(response.status_code))
        if isItRedirect(response.status_code): saveLogs('location: ' + response.headers['location'])
        
        if not (response.status_code == 200 and isAntiScraping(str(response.content))):
            return response

        url = antiScraping(str(response.content));

    return response

def postAntiScraping(url, data, timeout=timeoutValue):
    global session
    for i in range(6):
        saveLogs('postAntiScraping URL: ' + url)
        if url.endswith('attempt=2') or url.endswith('attempt=3'):
            url = url.split('attempt=')[0];
            url = url.substring(0, url.length - 1);
            
        while True:
            try:
                response = session.post(url, data=data, headers=headers, timeout=timeout, allow_redirects=False)
                break
            except requests.exceptions.SSLError as ex:
                saveLogs('$$$$$$$$$$$$$$ SSLError postAntiScraping $$$$$$$$$$$$$')
                sleep(1)
        
        # saveLogs('STATUS: ' + str(response.status_code))
        # saveLogs('response.history: ' + str(response.history))
        # saveLogs('response.url: ' + response.url)
        if isItRedirect(response.status_code): saveLogs('location: ' + response.headers['location'])
        
        if not (response.status_code == 200 and isAntiScraping(str(response.content))):
            return response

        url = antiScraping(str(response.content));

    return response

def getCaptcha():
    global session, pathCookies
    pathCookies = 'logs/' + username + '/cookies'
    if os.path.isfile(pathCookies):
        with open(pathCookies, 'rb') as f:
            session.cookies.update(pickle.load(f))
    try:
        if stateIn is None:
            _logInStates = getLogInStates()
            if _logInStates != True: return _logInStates
        # print(stateIn['captchaLink'])
        url = 'https://' + baseUrl + '/' + shopList[shopIndexCaptcha] + '/' + stateIn['captchaLink']
        r = getAntiScraping(url)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception getCaptcha 1 $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return False
    if r.status_code == 200:
        with open("captcha_" + username + ".jpg", 'wb') as f:
            f.write(r.content)
        return input('Enter the captcha: ')

def logIn(password, captcha):
    global session, stateIn
    login_data = {
        'PageLoadedHiddenTxtBox': 'Set',
        '__VIEWSTATE': stateIn['viewState'],
        '__EVENTVALIDATION': stateIn['eventValidation'],
        'ctl00$cphPage$Login$UserName': username,
        'ctl00$cphPage$Login$Password': password,
        'ctl00$cphPage$Login$capcha': captcha,
        'ctl00$cphPage$Login$LoginButton': 'Entrar',
        **baseData
    }
    # stateIn = None
    # print(captcha)
    # print(login_data)
    url = 'https://' + baseUrl + '/' + shopList[shopIndexCaptcha] + '/' + 'SignIn.aspx?ReturnUrl=%2f' + shopList[shopIndexCaptcha] + '%2fSignIn.aspx'
    while True:
        try:
            response = session.post(url, data=login_data, headers=headers, timeout=timeoutValue)
            saveLogs('LogIn STATUS: ' + str(response.status_code))
            saveContent(str(response.content), 'logIn')
            if response.status_code == 200: break
        except Exception as ex:
            saveLogs('$$$$$$$$$$$$$$ Exception logIn $$$$$$$$$$$$$')
            saveLogs(str(ex))
        saveLogs('Error en la autenticación.')
        sleep(1)
    # stateIn = {
        # 'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        # 'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    # }
    stateIn = None
    if 'Bienvenido ' in str(response.content) and not 'Bienvenido a ' in str(response.content):
        saveLogs('Autenticación exitosa!!!')
        with open(pathCookies, 'wb') as f:
            pickle.dump(session.cookies, f)
        return True
    if 'Nombre de Usuario Incorrecto' in str(response.content):
        saveLogs('Usuario y/o contraseña incorrect@.')
        sys.exit(0)
    else: saveLogs('Captcha incorrecto.')
    saveLogs(response.url)
    return False

def getLogInStates():
    global session, shopIndexCaptcha, stateIn
    shopIndexCaptcha = shopIndex
    # print(url)
    while True:
        try:
            url = 'https://' + baseUrl + '/' + shopList[shopIndexCaptcha] + '/' + 'SignIn.aspx?ReturnUrl=%2F' + shopList[shopIndexCaptcha] + '%2FShoppingCart.aspx'
            response = getAntiScraping(url)
            saveLogs('LogInStates STATUS: ' + str(response.status_code))
            if isItRedirect(response.status_code): saveLogs('location: ' + response.headers['location'])
            saveLogs('Response URL: ' + str(response.url))
            # saveContent(str(response.content), 'getLogInStates') # delete
            if response.status_code == 200 and response.url == url:
                if getCart(response.content):
                    saveLogs('User is loggedIn!!!')
                    return 'loggedIn'
                stateIn = {
                    'viewState': getValue(str(response.content), '__VIEWSTATE', False),
                    'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
                    'captchaLink': getCaptchaLink(str(response.content)),
                }
                return True
            elif response.url == 'https://www.tuenvio.cu/' + shopList[shopIndexCaptcha] + '/StoreClosed.aspx': sleep(2)
        except Exception as ex:
            saveLogs('$$$$$$$$$$$$$$ Exception getLogInStates $$$$$$$$$$$$$')
            saveLogs(str(ex))
        sleep(1)
        saveLogs('Intentando autenticación en otra tienda...')
        shopIndexCaptcha = (shopIndexCaptcha + 1) % len(shopList)
        if shopIndexCaptcha == shopIndex: break
    return False

def getSections(toExit = False):
    global session
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/SignIn.aspx?ReturnUrl=%2F' + shopList[shopIndex] + '%2FShoppingCart.aspx'
    try:
        response = getAntiScraping(url)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception getSections $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(1)
        return False
    saveLogs('getSections STATUS: ' + str(response.status_code))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        if isItRedirect(response.status_code): saveLogs('location: ' + response.headers['location'])
        return False
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    getCart(response.content, toExit = toExit)
    soup = BeautifulSoup(response.content, 'html.parser')
    section = list(soup.find(class_ = 'mainNav').find(class_ = 'nav').children)[1]
    output = section.find('li').find('a').attrs['href']
    saveLogs(output)
    return output

c = 0
def helper():
    global deptStates, c
    if deptStates is None:
        items = getItems()
        if items and len(items) > 0:
            for i in range(5): Thread(target = addToCart).start()
    elif c < 150 || getItemsContent !is None:
        addToCart()
        c += 1

def getItems():
    global session, deptStates, showMode
    showMode = 'listTemplate'
    if getItemsContent !is None:
        soupContent = getItemsContent
    else:
        url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Products?depPid=' + depPidMap.get(shopList[shopIndex], '46095')
        saveLogs(url)
        try:
            response = getAntiScraping(url)
        except Exception as ex:
            saveLogs('$$$$$$$$$$$$$$ Exception getItems $$$$$$$$$$$$$')
            saveLogs(str(ex))
            sleep(0.5)
            return False
        saveLogs('getItems STATUS: ' + str(response.status_code))
        if response.status_code != 200:
            if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
            return False
        if response.url != url:
            saveLogs(response.url)
            if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
            if response.url == 'https://www.tuenvio.cu/mtto_sys_producto_agotado': sleep(5)
            return False
        soupContent = response.content
        getCart(soupContent)

    soup = BeautifulSoup(soupContent, 'html.parser')
    hProductItems = soup.find(class_ = 'hProductItems')
    if hProductItems is None:
        saveLogs('--- no hay productos ---')
        return False

    deptStates = {
        'viewState': getValue(str(soupContent), '__VIEWSTATE', False),
        'eventValidation': getValue(str(soupContent), '__EVENTVALIDATION', False),
    }

    if getItemsContent is None: saveContent(str(soupContent), 'getItems')
    
    itemTags = hProductItems.find_all(class_ = 'product-details')
    if len(itemTags) > 0: return getItemsData_new(itemTags)
    return getItemsData_old(hProductItems.find_all('li', recursive=False))

def getItemsData_old(itemTags):
    saveLogs('Total de productos: ' + str(len(itemTags)))
    productList = []
    for el in itemTags:
        item = {}
        thumbSetting = el.find(class_ = 'thumbSetting')
        a = thumbSetting.find('a')
        item['itemTitle'] = a.get_text().strip()
        item['itemUri'] = a.attrs['href']
        thumbPrice = thumbSetting.find(class_ = 'thumbPrice')
        if thumbPrice is None:
            thumbPrice = thumbSetting.find(class_ = 'thumbPriceRate')
            showMode = 'listTemplate' 
        saveLogs('showMode: ' + showMode)
        if thumbPrice is None:
            saveLogs('• ' + item['itemTitle'] + ' (EXHIBICIÓN)')
            continue
        itemPriceText = thumbPrice.find('span').get_text().strip()
        item['itemId'] = el.find(class_ = 'product-inputs').find('a').get('id').split('rptListProducts_')[-1].split('_' + showMode)[0]
        saveLogs('- ' + item['itemTitle'] + ' (' + itemPriceText + ')')
        productList.append(item)
    return productList

def getItemsData_new(itemTags):
    saveLogs('Total de productos: ' + str(len(itemTags)))
    productList = []
    for el in itemTags:
        item = {}
        item['itemTitle'] = el.find(class_ = 'product-title').get_text().strip()
        item['itemPrice'] = el.find(class_ = 'product-price').get_text().strip()
        saveLogs('- ' + item['itemTitle'] + ' (' + item['itemPrice'] + ')')
        productList.append(item)
    return productList

def addToCart():
    global session, deptStates
    try:
        if addMethod == 'p':
            saveLogs('POST method')
            url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Products?depPid=' + depPidMap.get(shopList[shopIndex], '46095') + '&page=0'
            postData = getAddToCartData()
            saveLogs(re.sub("__VIEWSTATE': '[^']*", "__VIEWSTATE': '" + deptStates['viewState'][-10:], str(postData).replace(', ', '\n')))
            saveLogs(url)
            response = postAntiScraping(url, data=postData, timeout=1)
        else:
            saveLogs('GET method')
            url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/ShoppingCart.aspx?Department=' + depPidMap.get(shopList[shopIndex], '46095') + '&addItem=' + itemId
            response = getAntiScraping(url)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception addToCart $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return
    
    # saveLogs(str(response.history))
    # saveLogs(response.url)
    saveLogs('STATUS: ' + str(response.status_code))
    if isItRedirect(response.status_code): saveLogs('location: ' + response.headers['location'])

def getAddToCartData(itemId = 'ctl00'):
    return {
        'ctl00$ScriptManager1': 'ctl00$ScriptManager1|ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        # 'ctl00$ScriptManager1': 'ctl00$cphPage$productsControl$UpdatePanel1|ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        '__EVENTTARGET': 'ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        '__VIEWSTATE': deptStates['viewState'],
        # '__VIEWSTATE': '',
        # '__EVENTVALIDATION': deptStates['eventValidation'],
        'ctl00$txtSearch': '',
        'ctl00$cphPage$productsControl$TopTools$cbxPageSize': '-1',
        'ctl00$cphPage$productsControl$TopTools$cbxSortType': '',
        'ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$txbCaptcha': '',
        # 'ctl00$cphPage$productsControl$TopTools$cbxViewType': 'GridMode',
        'ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$txtCount': '1',
        '__ASYNCPOST': 'true',
        'PageLoadedHiddenTxtBox': 'Set',
        **baseData
    }
    
def getItemsData():
    return {
        'ctl00$ScriptManager1': 'ctl00$cphPage$productsControl$UpdatePanel1|ctl00$cphPage$productsControl$TopTools$cbxViewType',
        '__EVENTTARGET': 'ctl00$cphPage$productsControl$TopTools$cbxViewType',
        'PageLoadedHiddenTxtBox': 'Set',
        'ctl00$cphPage$productsControl$TopTools$cbxViewType': 'ListMode',
        **baseData
    }

def getMyOrders():
    global session, orderStates
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Orders'
    try:
        response = session.get(url, headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return False
    saveLogs('getMyOrders STATUS: ' + str(response.status_code))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    orderStates = {
        'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        'viewStateGenerator': getValue(str(response.content), '__VIEWSTATEGENERATOR', False),
        'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    }
    return _getMyOrders(response.content)

def _getMyOrders(content):
    global orders
    orders = []
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find(id = 'ctl00_cphPage_gridOrders')
    if table is None:
        saveLogs('No tiene órdenes en esa tienda.')
        return False
    rows = table.find_all('tr', class_ = isNotThead)
    for row in rows:
        columns = row.find_all('td')
        orders.append(columns[4].find('a').attrs['href'].split('orderId=')[-1])
    # print(orders)
    return True

def isNotThead(css_class):
    return css_class is None or css_class == 'AlternatingRowStyle'

def reOrder(idx):
    global session, orderStates
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Orders'
    sleep(2.8)
    try:
        response = session.post(url, data=getReOrderData(idx), headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return False
    saveLogs('reOrder STATUS: ' + str(response.status_code))
    #saveLogs('Ninguno: ' + str('Ninguno de los productos está' in str(response.content)))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    if 'Ninguno de los productos est' in str(response.content):
        saveLogs('Ninguno de los productos están disponibles hoy.')
        # orderStates = {
            # 'viewState': getValue(str(response.content), '__VIEWSTATE', True),
            # 'viewStateGenerator': getValue(str(response.content), '__VIEWSTATEGENERATOR', True),
            # 'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', True),
        # }
        return False
    saveContent(str(response.content), 'reOrder')
    getCart(response.content, True)

def getReOrderData(idx):
    data =  {
        'PageLoadedHiddenTxtBox': 'Set',
        'ctl00$ScriptManager1': 'ctl00$cphPage$mainUpdatePanel|ctl00$cphPage$gridOrders$ctl' + '{:02d}'.format(idx + 1) + '$btnAddCart',
        '__EVENTTARGET': 'ctl00$cphPage$gridOrders$ctl' + '{:02d}'.format(idx + 1) + '$btnAddCart',
        '__VIEWSTATE': orderStates['viewState'],
        '__VIEWSTATEGENERATOR': orderStates['viewStateGenerator'],
        '__EVENTVALIDATION': orderStates['eventValidation'],
        'ctl00$cphPage$hiddenOrderId': '',
        'ctl00$cphPage$shipDateControl$hiddenProductPid': '0',
        '__ASYNCPOST': 'true',
        **baseData
    }
    for i in range(len(orders)):
        data['ctl00$cphPage$gridOrders$ctl' + '{:02d}'.format(i + 2) + '$hdnOrderId'] = orders[i]
    # print(data)
    return data

def getMyContacts():
    global session, contactStates
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/MyContacts'
    try:
        response = session.get(url, headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return
    saveLogs('getMyContacts STATUS: ' + str(response.status_code))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return
    contactStates = {
        'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    }
    saveContent(str(response.content), 'getMyContacts')
    return

def newContact():
    global session, contactStates
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/MyContacts'
    try:
        response = session.post(url, data=newContactData(), headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return False
    saveLogs('newContact STATUS: ' + str(response.status_code))
    #saveLogs('Ninguno: ' + str('Ninguno de los productos está' in str(response.content)))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    contactStates = {
        'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    }
    saveContent(str(response.content), 'newContact')

def newContactData():
    return {
        'PageLoadedHiddenTxtBox': 'Set',
        '__EVENTTARGET': 'ctl00$cphPage$btnInsert',
        '__VIEWSTATE': contactStates['viewState'],
        '__EVENTVALIDATION': contactStates['eventValidation'],
        **baseData
    }

def changeProvinceContact():
    global session, contactStates
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/MyContacts'
    try:
        response = session.post(url, data=changeProvinceContactData(), headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(0.5)
        return False
    saveLogs('changeProvinceContact STATUS: ' + str(response.status_code))
    #saveLogs('Ninguno: ' + str('Ninguno de los productos está' in str(response.content)))
    if response.status_code != 200:
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    if response.url != url:
        saveLogs(response.url)
        if (len(response.content) > fatResponse): saveLogs('Alto Consumo de Megas!!!')
        return False
    contactStates = {
        'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        'viewStateGenerator': getValue(str(response.content), '__VIEWSTATEGENERATOR', False),
        'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    }
    print(response.request.headers)
    saveContent(str(response.content), 'changeProvinceContact')
    
def changeProvinceContactData():
    return {
        'ctl00$ScriptManager1': 'ctl00$cphPage$addressForm$UpdatePanel1|ctl00$cphPage$addressForm$listState',
        '__EVENTTARGET': 'ctl00$cphPage$addressForm$listState',
        '__ASYNCPOST': 'true',
        '__VIEWSTATE': contactStates['viewState'],
        '__EVENTVALIDATION': contactStates['eventValidation'],
        'ctl00$cphPage$addressForm$txtFirstName': '',
        'ctl00$cphPage$addressForm$txtLastName': '',
        'ctl00$cphPage$addressForm$txtIdNumber': '',
        'ctl00$cphPage$addressForm$txtAddress1': '',
        'ctl00$cphPage$addressForm$listCountry': '54',
        'ctl00$cphPage$addressForm$listState': '711',
        'ctl00$cphPage$addressForm$listCity': '',
        'ctl00$cphPage$addressForm$txtPhone': '',
        'ctl00$cphPage$addressForm$txtEmail': '',
        'ctl00$cphPage$addressForm$txtShippingAddressName': '',
        'ctl00$cphPage$addressForm$hiddenAlias': '',
        'ctl00$cphPage$addressForm$txtAltName': '',
        'ctl00$cphPage$addressForm$txtAltLastName': '',
        'ctl00$cphPage$addressForm$txtAltIdNumber': '',
        **baseData
    }

def getCart(content, xhr = False, toExit = False):
    soup = BeautifulSoup(content, 'html.parser')
    user = ''
    if not xhr:
        userTag = soup.find(id = 'ctl00_LoginName1')
        if userTag is None: userTag = soup.find(id = 'LoginName1')
        if userTag is None:
            saveLogs('NO ESTÁ AUTENTICADO')
            return False
            # os._exit(0)
        user = userTag.get_text().split('Bienvenido ')[-1]
        # print('user: ' + user)
    tableCart = soup.find(class_ = 'table-cart')
    if tableCart is None:
        saveLogs('Error leyendo el carrito')
        return True
    itemsHtml = tableCart.find('tbody').find('tr')
    if not itemsHtml:
        saveLogs('shop: ' + shopList[shopIndex] + ', cart: Cart(' + user + ', carrito vacío)')
        if toExit: os._exit(0)
        return True
    aTitle = itemsHtml.find(class_ = 'cart-product-desc').find('a')
    title = aTitle.get_text().strip()
    saveLogs('shop: ' + shopList[shopIndex] + ', cart: Cart(' + user + ', ' + title + ')')
    saveLogs('Tiene un producto en el carrito!!!')
    # return True
    os._exit(0)

def getValue(content, name, xhr):
    if xhr: return content.split(name + '|')[-1].split('|')[0] if (name + '|' in content) else ''
    pattern = '<input type="hidden" name="' + name + '" id="' + name + '" value="';
    return content.split(pattern)[-1].split('"')[0] if (pattern in content) else '';

def getCaptchaLink(content):
    soup = BeautifulSoup(content, 'html.parser')
    loginPanel = soup.find(id = 'ctl00_cphPage_Login_loginPanel')
    if loginPanel is None: loginPanel = soup.find(id = 'cphPage_Login_loginPanel')
    img = loginPanel.find('img')
    if not img is None and img.has_attr('src'): return img.attrs['src']
    loginCaptcha = soup.find(id = 'ctl00_cphPage_Login_captch')
    if loginCaptcha is None: loginCaptcha = soup.find(id = 'cphPage_Login_captch')
    if not loginCaptcha is None and loginCaptcha.has_attr('src'): return loginCaptcha.attr('src')
    
    #print(content)
    #if "document.getElementById(\\'cphPage_Login_captch\\').src=\\'" in content: print('TRUEEEEE')
    #else: print('FALSEEE')
    return content.split("document.getElementById(\\'cphPage_Login_captch\\').src=\\'")[1].split("\\'")[0];
    