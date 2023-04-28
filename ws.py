import asyncio
import json
import websockets
from reqoperator import operator
from sessionID import TOKEN
from auth_inout import auth_wss
import time


op, auth = operator(TOKEN)
token = auth_wss(TOKEN)

# Config bets
bet = 0.05
stake = bet
last_result = []
currency = 'BRL'
color = ''
loss = 1
bet_placed = False
async def send_messages():
    # Url do websocket
    uri = f"wss://api.inout.games/io/?operatorId={op}&Authorization={token}&gameMode=new-double&EIO=4&transport=websocket"
    key_api = "5328905392:AAG29HHnR1vZQpCs5wcAvtDMfhzqJXzfrMA"

    # Criando uma fila para armazenar as mensagens
    message_queue = asyncio.Queue()

    async with websockets.connect(uri, timeout=60) as websocket:
        # Enviando mensagem "40"
        await websocket.send("40")

        # Iniciando uma tarefa para receber mensagens do servidor
        async def receive_messages():
            global bet, last_result, color, loss, stake, bet_placed
            win_count = 0  # Counter for number of consecutive wins
            lost_previous_round = False  # Flag to keep track of previous loss
            while True:
                try:
                    # Recebendo mensagens do websocket
                    message = await websocket.recv()
                    await message_queue.put(message)

                    log = None
                    # Capturando mensagem desejada
                    if 'gameService-game-status-changed' in message:
                        message_list = message.split('["gameService-game-status-changed",')[1:]
                        message_dict = json.loads(message_list[0][:-1])
                        status = message_dict.get('status')
                        print(status)
                        if status == 'WAIT_GAME':
                            if len(last_result) >= 2 and last_result[-2:] == ['red', 'black'] or last_result[-2:] == ['black', 'red']:
                                print('Skipping bet because last 2 results were the same color')
                                continue

                            if len(last_result) >= 3 and last_result[-3] == last_result[-2]:
                                # Bet on the last color
                                color_to_bet = last_result[-1]
                                loss = 1
                            else:
                                color_to_bet = color
                                if lost_previous_round is True and last_result != 'green':
                                    stake = stake*3 if stake < 4.00 else bet
                                elif bet_placed is False:
                                    stake = bet
                                print(f'Resetting the bet to {stake}')

                            if color_to_bet != 'green' and color_to_bet == color:
                                bet_message = f'42["gameService",{{"action":"make-bet","messageId":"1","payload":{{"betAmount":"{stake}","currency":"{currency}","color":"{color_to_bet}"}}}}]'
                                await websocket.send(bet_message)
                                print(f'Sending message: {bet_message}')

                                bet_placed = False
                            elif color_to_bet == color and last_result[-2] != last_result[-1]:
                                stake = bet
                                print(f'Resetting the bet to {stake}')

                                                                        
                        else:
                            cell_result = message_dict.get('cellResult')
                            if cell_result:
                                color = cell_result.get('color')
                                number = cell_result.get('number')
                                print(f'Color: {color}, Number: {number}')

                                last_result.append(color)
                                if len(last_result) > 2:
                                    last_result = last_result[-2:]

                                if len(last_result) == 2:
                                    if last_result[0] == last_result[1]:
                                        print('São cores iguais:', last_result[0], last_result[1])

                                    # Check if lost previous round
                                    if last_result[-1] != color_to_bet:
                                        lost_previous_round = True
                                    else:
                                        lost_previous_round = False
                                    bet_placed = False



                except websockets.exceptions.ConnectionClosed:
                    # Fechando a conexão caso ocorra erro de conexão
                    continue


        # Iniciando a tarefa de recebimento de mensagens
        receive_task = asyncio.create_task(receive_messages())
        INACTIVITY_TIMEOUT = 120 
        last_activity_time = time.time() # inicializando a última hora de atividade

        while True:
            try:
                # Aguardando a recepção de uma mensagem do servidor antes de enviar a próxima mensagem "3"
                message_received = await asyncio.wait_for(message_queue.get(), timeout=7)
                # Enviando mensagem "3"
                await websocket.send("3")

                # definindo a hora da última atividade para a hora atual
                last_activity_time = time.time() 

            except asyncio.TimeoutError:
                # Enviando mensagem "3" caso o tempo de espera tenha expirado
                await websocket.send("3")

                if time.time() - last_activity_time > INACTIVITY_TIMEOUT:
                    await websocket.close()
                    break

            except websockets.exceptions.ConnectionClosed:
                # Fechando a conexão caso ocorra erro de conexão
                break

        # Finalizando a tarefa de recebimento de mensagens
        receive_task.cancel()

# Executando o loop de eventos do asyncio para enviar as mensagens
asyncio.get_event_loop().run_until_complete(send_messages())


