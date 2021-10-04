import requests
import os
import codecs
import sys
import asyncio
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup
# from dbc import new_recaptcha_coordinates as dbc
from twocaptcha import TwoCaptcha

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
}
solver = TwoCaptcha('6176e0a620e1900dbc847591d9e79fd2')
baseUrl = 'www.tuenvio.cu'
stateIn = None
timeoutValue = 120
fatResponse = 300000
session = requests.Session()
shopIndex, shopIndexCaptcha = None, None
shopList = ['pinar', 'artemisa', 'lahabana', 'carlos3',  'tvpedregal', 'caribehabana', 'almacencaribe', 'mayabeque-tv', 'matanzas', 'cienfuegos', 'villaclara',\
'sancti', 'ciego', 'camaguey', 'tunas', 'holguin', 'granma', 'santiago', 'caribesantiago', 'guantanamo', 'isla']

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
        if response.status_code == 301: saveLogs('location: ' + response.headers['location'])
        
        if not (response.status_code == 200 and isAntiScraping(str(response.content))):
            return response

        url = antiScraping(str(response.content));

    return response

def postAntiScraping(url, data):
    global session
    for i in range(6):
        saveLogs('postAntiScraping URL: ' + url)
        if url.endswith('attempt=2') or url.endswith('attempt=3'):
            url = url.split('attempt=')[0];
            url = url.substring(0, url.length - 1);
            
        while True:
            try:
                response = session.post(url, data=data, headers=headers, timeout=timeoutValue, allow_redirects=False)
                break
            except requests.exceptions.SSLError as ex:
                saveLogs('$$$$$$$$$$$$$$ SSLError postAntiScraping $$$$$$$$$$$$$')
                sleep(1)
        
        # saveLogs('STATUS: ' + str(response.status_code))
        # saveLogs('response.history: ' + str(response.history))
        # saveLogs('response.url: ' + response.url)
        if response.status_code == 302: saveLogs('location: ' + response.headers['location'])
        if response.status_code == 301: saveLogs('location: ' + response.headers['location'])
        
        if not (response.status_code == 200 and isAntiScraping(str(response.content))):
            return response

        url = antiScraping(str(response.content));

    return response

def getCaptcha():
    global session
    try:
        if stateIn is None and not getLogInStates(): return False
        print(stateIn['captchaLink'])
        url = 'https://' + baseUrl + '/' + shopList[shopIndexCaptcha] + '/' + stateIn['captchaLink']
        r = session.get(url, headers=headers, timeout=timeoutValue)
    except Exception as ex:
        saveLogs('$$$$$$$$$$$$$$ Exception getCaptcha 1 $$$$$$$$$$$$$')
        saveLogs(str(ex))
        sleep(2)
        return False
    if r.status_code == 200:
        # solvedCaptcha = dbc.getCaptcha(r.content)
        saveLogs('solving catpcha...')
        with open("captcha_" + username + ".jpg", 'wb') as f:
            f.write(r.content)
        while True:
            try:
                response = solver.normal("captcha_" + username + ".jpg")
                break
            except Exception as ex:
                saveLogs('$$$$$$$$$$$$$$ Exception getCaptcha 2 $$$$$$$$$$$$$')
                saveLogs(str(ex))
                sleep(2)
        saveLogs('Captcha: ' + response['code'])
        return response['code']

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
        url = 'https://' + baseUrl + '/' + shopList[shopIndexCaptcha] + '/' + 'SignIn.aspx?ReturnUrl=%2F' + shopList[shopIndexCaptcha] + '%2FShoppingCart.aspx'
        response = session.get(url, headers=headers, timeout=timeoutValue)
        saveLogs('LogInStates STATUS: ' + str(response.status_code))
        saveLogs('Response URL: ' + str(response.url))
        # saveContent(str(response.content), 'getLogInStates') # delete
        if response.status_code == 200 and response.url == url:
            stateIn = {
                'viewState': getValue(str(response.content), '__VIEWSTATE', False),
                'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
                'captchaLink': getCaptchaLink(str(response.content)),
            }
            return True
        if response.url == 'https://www.tuenvio.cu/caribehabana/StoreClosed.aspx': sleep(2)
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
        if isItRedirect(response.status_code): print(response.headers['location'])
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

def getItems(deptUri):
    global session, deptStates, showMode
    showMode = 'gridTemplate'
    url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/' + deptUri
    saveLogs(url)
    try:
        response = session.get(url, headers=headers, timeout=timeoutValue)
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
    deptStates = {
        'viewState': getValue(str(response.content), '__VIEWSTATE', False),
        'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', False),
    }
    
    saveContent(str(response.content), 'getItems') # delete
    
    # del session.cookies['ASP.NET_SessionId']
    getCart(response.content)
    
    #file = codecs.open('logs/' + username + '/content' + datetime.now().strftime('_%Y%m%d_%H%M%S_') + tail + '.html', 'w', encoding='utf-8', errors='ignore')
    #file.write(codecs.escape_decode(bytes(content, "utf-8"))[0].decode("utf-8"))
    #file.close()
    #file = open('logs/georkings/content_20201119_090127_getItems.html', 'r')
    #soupContent = str.encode(file.read())
    #file.close()
            
    soup = BeautifulSoup(response.content, 'html.parser')
    hProductItems = soup.find(class_ = 'hProductItems')
    saveContent(str(response.content), 'getItems1') # delete
    if hProductItems is None:
        saveLogs('--- no hay productos ---')
        return False
    itemTags = hProductItems.find_all('li', recursive=False)
    saveLogs('Total de productos: ' + str(len(itemTags)))
    productList = []
    # saveContent(str(response.content), 'getItems') # delete
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

# def addToCart(itemUri, itemId, timeoutAddToCart):
    # global session, deptStates
    # depPid = itemUri.split('depPid=')[-1].split('&')[0]
    # try:
        # if addMethod == 'p':
            # # print('POST method')
            # url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Products?depPid=' + depPid
            # response = session.post(url, data=getAddToCartData(itemId), headers=headers, timeout=timeoutAddToCart)
        # else:
            # print('GET method')
            # url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/ShoppingCart.aspx?Department=' + depPid + '&addItem=' + itemId
            # response = session.get(url, headers=headers, timeout=timeoutAddToCart)
    # except Exception as ex:
        # saveLogs('$$$$$$$$$$$$$$ Exception addToCart $$$$$$$$$$$$$')
        # saveLogs(str(ex))
        # sleep(0.5)
        # return
    # # if 'WebResource.axd' in str(response.content):
        # # saveLogs('WebResource.axd')
        # # deptStates = {
            # # 'viewState': getValue(str(response.content), '__VIEWSTATE', True),
            # # 'eventValidation': getValue(str(response.content), '__EVENTVALIDATION', True),
        # # }
        # # try:
            # # response = session.post(url, data=getAddToCartData(itemId), headers=headers, timeout=timeoutValue)
        # # except Exception as ex:
            # # saveLogs('$$$$$$$$$$$$$$ Exception $$$$$$$$$$$$$')
            # # saveLogs(str(ex))
            # # sleep(0.5)
            # # return
    # if response.status_code != 200:
        # saveLogs('Error del servidor al realizar la operación.')
        # return
    # if 'Error.aspx' in str(response.content):
        # saveLogs('Error al añadir!!!')
        # return
    # # saveContent(str(response.content), 'addToCart')
    # getCart(response.content, addMethod == 'p')
    # if not 'ctl00_cphPage_productsControl_UpdatePanel1' in str(response.content):
        # saveLogs('Producto agotado!!!')
        # return
    # saveLogs('Error desconocido al realizar la operación.')

def addToCart(itemUri, itemId, timeoutAddToCart = 90, id = '1'):
    global session, deptStates
    depPid = itemUri.split('depPid=')[-1].split('&')[0]
    saveLogs(id + '_addToCart')
    try:
        if addMethod == 'p':
            saveLogs('POST method')
            saveLogs(str(getAddToCartData()))
            url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/Products?depPid=' + depPid
            response = session.post(url, data=getAddToCartData(), headers=headers, timeout=timeoutAddToCart)
        else:
            url = 'https://' + baseUrl + '/' + shopList[shopIndex] + '/ShoppingCart.aspx?Department=' + depPid + '&addItem=' + itemId
            response = session.get(url, headers=headers, timeout=timeoutAddToCart, allow_redirects=False)
    except Exception as ex:
        saveLogs(id + '_' + '$$$$$$$$$$$$$$ Exception addToCart $$$$$$$$$$$$$')
        saveLogs(id + '_' + str(ex))
        sleep(0.5)
        return
    
    # saveLogs(id + '_' + str(response.history))
    # saveLogs(id + '_' + response.url)
    saveLogs(id + '_STATUS: ' + str(response.status_code))
    
    if response.status_code == 302 and response.headers['location'] == '/' + shopList[shopIndex] + '/Products?depPid=' + depPid:
        saveLogs(id + '_location: ' + response.headers['location'])
        try:
            response = session.get('https://' + baseUrl + response.headers['location'], headers=headers, timeout=timeoutAddToCart, allow_redirects=False)
        except Exception as ex:
            saveLogs(id + '_' + '$$$$$$$$$$$$$$ Exception addToCart $$$$$$$$$$$$$')
            saveLogs(id + '_' + str(ex))
            sleep(0.5)
            return
              
        saveLogs(id + '_STATUS: ' + str(response.status_code))
        if response.status_code == 302:
            saveLogs(id + '_location: ' + response.headers['location'])
    if response.status_code != 200:
        saveLogs(id + '_' + 'Error del servidor: ' + str(response.status_code))
        return
    if 'Error.aspx' in str(response.content):
        saveLogs(id + '_' + 'Error al añadir!!!')
        return
    # saveContent(str(response.content), 'addToCart')
    getCart(response.content, addMethod == 'p')
    if not 'ctl00_cphPage_productsControl_UpdatePanel1' in str(response.content):
        saveLogs(id + '_' + 'Producto agotado!!!')
        return
    saveLogs(id + '_' + 'Error desconocido al realizar la operación.')

def getAddToCartData(itemId = 'ctl00'):
    return {
        # 'ctl00$ScriptManager1': 'ctl00$ScriptManager1|ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        # 'ctl00$ScriptManager1': 'ctl00$cphPage$productsControl$UpdatePanel1|ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        '__EVENTTARGET': 'ctl00$cphPage$productsControl$rptListProducts$' + itemId + '$' + showMode + '$btnCart',
        '__VIEWSTATE': deptStates['viewState'],
        # '__VIEWSTATE': '',
        # '__EVENTVALIDATION': deptStates['eventValidation'],
        'ctl00$cphPage$productsControl$TopTools$cbxPageSize': '-1',
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
            os._exit(0)
        user = userTag.get_text().split('Bienvenido ')[-1]
        # print('user: ' + user)
    tableCart = soup.find(class_ = 'table-cart')
    if tableCart is None:
        saveLogs('Error leyendo el carrito')
        return
    itemsHtml = tableCart.find('tbody').find('tr')
    if not itemsHtml:
        saveLogs('shop: ' + shopList[shopIndex] + ', cart: Cart(' + user + ', carrito vacío)')
        if toExit: os._exit(0)
        return
    aTitle = itemsHtml.find(class_ = 'cart-product-desc').find('a')
    title = aTitle.get_text().strip()
    saveLogs('shop: ' + shopList[shopIndex] + ', cart: Cart(' + user + ', ' + title + ')')
    saveLogs('Tiene un producto en el carrito!!!')
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
    