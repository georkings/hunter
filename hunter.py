import tuenvioApi
import os
import sys
from threading import Thread
from time import sleep

# tuenvioApi.addMethod = input("POST(p) o GET(g): ")
tuenvioApi.addMethod = 'p'
if len(sys.argv) != 3:
    print('Debe usar el sgte formato: "python hunter.py <tienda> <usuario>"')
    sys.exit(0)
tuenvioApi.shopIndex = tuenvioApi.shopList.index(sys.argv[1])
tuenvioApi.username = sys.argv[2]
sleepTime = int(input('Tiempo entre cada intento de montar(ms): '))

if os.path.isdir('users') and os.path.isfile('users/' + tuenvioApi.username):
    file = open('users/' + tuenvioApi.username, 'r')
    password = file.read()
    file.close()
else: password = "Lionel*2017"

tuenvioApi.saveLogs('*** Welcome! ***')
tuenvioApi.saveLogs('sleep Time: ' + str(sleepTime) + 'ms')

# logIn
while True:
    while True:
        captcha = tuenvioApi.getCaptcha()
        if captcha: break
        sleep(1)
    if captcha == 'loggedIn': break
    if tuenvioApi.logIn(password, captcha): break
    sleep(1)

c = 0
while True:
    Thread(target = tuenvioApi.helper).start()
    if tuenvioApi.deptStates is None: sleep(1)
    else: sleep(sleepTime / 1000)
    c += 1
    # if c % 30 == 0: tuenvioApi.getSections()
    if c % 60 == 0: Thread(target = tuenvioApi.getSections).start()