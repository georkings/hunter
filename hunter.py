import tuenvioApi
import os
from threading import Thread
from time import sleep

# tuenvioApi.addMethod = input("POST(p) o GET(g): ")
tuenvioApi.addMethod = 'p'
tuenvioApi.shopIndex = int(input("1. Pinar del Río\n2. Artemisa\n3. La Habana\n4. Carlos III\n5. El Pedregal\n6. Villa Diana\n7. Almacén Caribe\n8. Mayabeque\n9. Matanzas\
      \n10. Cienfuegos\n11. Villa Clara\n12. Sancti Spíritus\n13. Ciego de Avila\n14. Camaguey\n15. Las Tunas\n16. Holguín\n17. Granma\n18. Santiago de Cuba\
      \n19. Santiago de Cuba (Caribe)\n20. Guantánamo\n21. Isla de la Juventud\nInserte número de tienda: ")) - 1
# prodPid = input("Inserte prodId (deje en blanco si no aplica): ")
# if prodPid == '': keyWord = input("Inserte palabra clave (deje en blanco si no aplica): ")
# Products?depPid=46087
deptUri = input("dept URL: ")
tuenvioApi.username = input("Usuario: ")

if os.path.isdir('users') and os.path.isfile('users/' + tuenvioApi.username):
    file = open('users/' + tuenvioApi.username, 'r')
    password = file.read()
    file.close()
else: password = "Lionel*2017"

# getCaptcha
while True:
    while True:
        captcha = tuenvioApi.getCaptcha()
        if captcha: break
        sleep(1)
    if tuenvioApi.logIn(password, captcha): break
    sleep(1)

# getSections
sleep(1)
while True:
    if deptUri: break
    deptUri = tuenvioApi.getSections()
    print(deptUri)
    sleep(1)

# getItems
def main(timeout):
    while True:
        # if prodPid == '':
        if True:
            items = tuenvioApi.getItems(deptUri)
            if not items: continue
            itemUri = items[0]['itemUri']
            if keyWord != '':
                for p in items:
                    if keyWord.lower() in p['itemTitle'].lower():
                        itemUri = p['itemUri']
                        break
            while True:
                tuenvioApi.addToCart(items[0]['itemUri'], itemUri.split('ProdPid=')[-1].split('&')[0])
        # else:
            # item = [i for i in items if i['itemUri'].split('ProdPid=')[-1].split('&')[0] == prodPid]
            # if not item:
                # tuenvioApi.saveLogs('El producto deseado no está en la lista de disponibles.')
                # continue
        
        else:
            tuenvioApi.addToCart('Products?depPid=46095', prodPid, timeout)

# Thread(target = main, args=[60 if prodPid == '' else 0.5]).start()
Thread(target = main, args=[60]).start()
while True:
    sleep(30)
    tuenvioApi.getSections()