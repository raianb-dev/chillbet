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

bet = 0.02
stake = bet
last_result = []
currency = 'BRL'
color = ''
loss = 1
bet_placed = False
color_to_bet = 'black'
async def send_messages():
    global color_to_bet
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
                            
                            bet_message = f'42["gameService",{{"action":"make-bet","messageId":"1","payload":{{"betAmount":"{stake}","currency":"{currency}","color":"{color_to_bet}"}}}}]'
                            await websocket.send(bet_message)
                            print(f'Sending message: {bet_message}')



                        if status == 'IN_GAME':
                            cellResult =message_dict.get('cellResult')
                            print('aqui:::', message_dict.get('cellResult'))   
                            color = cellResult['color']
                            if color != color_to_bet:
                                stake = stake*2
                            if color == color_to_bet:
                                stake = 0.02
                            


                                


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
                """if 'gameService-game-status-changed' in message_received:
                                        message_list = message_received.split('["gameService-game-status-changed",')[1:]
                                        message_dict = json.loads(message_list[0][:-1])
                                        status = message_dict.get('status')
                                        if status == "IN_GAME":
                                            if color_to_bet == 'black':
                                                color_to_bet = 'red'
                                            else:
                                                color_to_bet = 'black'
                """
                # Verifica se ocorreu um novo jogo
                

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


