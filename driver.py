import asyncio, time
import json
import websockets
from reqoperator import operator
from sessionID import TOKEN
from auth_inout import auth_wss

op, auth = operator(TOKEN)
token = auth_wss(TOKEN)

# Configuração das apostas
bet = 1
stake = bet
last_result = []
currency = 'BRL'
loss = 1
placed = False
win = False
count_win = 0
count_false = 0

async def send_messages():
    global bet, last_result, placed, win, count_false, count_win

    uri = f"wss://api.inout.games/games/diver/?Authorization={token}&operatorId={op}&EIO=4&transport=websocket"

    message_queue = asyncio.Queue()

    async with websockets.connect(uri, timeout=60) as websocket:
        await websocket.send("40")

        async def receive_messages():
            global bet, last_result, placed, win, count_false, count_win

            while True:
                try:
                    message = await websocket.recv()
                    await message_queue.put(message)

                    if 'onChangeStateGame' in message:
                        message_list = message.split('["onChangeStateGame",')[1:]
                        message_dict = json.loads(message_list[0][:-1])
                        coefficient = message_dict.get('coeffCrash')
                        status = message_dict.get('status')
                        if coefficient is not None:
                            last_result.insert(0, coefficient)

                            if win:
                                bet = stake # Redefine a aposta para 1 em caso de vitória

                            if not win and last_result[0] > 1.5 and placed and bet < 8:
                                bet *= 2

                            if last_result[0] > 1.8 and placed:
                                win = True
                                count_win += 1
                                print(f'Ganhou a aposta! Ganhou {count_win}x')
                                bet = 1  # Redefine a aposta para 1 após uma vitória
                            elif last_result[0] < 1.8 and placed:
                                win = False
                                count_false += 1
                                print(f'Perdeu a aposta. Perdeu {count_false}x')
                                bet = bet * 2  # Dobra a aposta apenas após uma perda

                            placed = False

                            if len(last_result) > 1 and last_result[0] == last_result[1]:
                                print('Excluindo linha repetida')
                                last_result.pop(0)

                    if 'onChangeStateGame' in message:
                        message_list = message.split('["onChangeStateGame",')[1:]
                        message_dict = json.loads(message_list[0][:-1])
                        status = message_dict.get('status')
                        if status == 'WAIT_GAME' and last_result[0] > 1.5 and not placed:
                            print('Passou da validação')
                            bet_message = f'42["addBet",{{"betAmount":{bet},"coeffAuto":1.8,"currency":"DEMO","betNumber":0}}]'
                            await websocket.send(bet_message)
                            print('Apostou')
                            placed = True

                except websockets.exceptions.ConnectionClosed:
                    break

        receive_task = asyncio.create_task(receive_messages())
        INACTIVITY_TIMEOUT = 60
        last_activity_time = time.time()

        while True:
            try:
                message_received = await asyncio.wait_for(message_queue.get(), timeout=7)
                await websocket.send("3")

            except asyncio.TimeoutError:
                await websocket.send("3")


        receive_task.cancel()

asyncio.get_event_loop().run_until_complete(send_messages())
