import PySimpleGUI as pyGUI
import socket

is_connected, is_confirmed, is_closed = False, False, False
pyGUI.theme("DarkAmber")
font = ("Arial", 13)
layout = \
    [
        [pyGUI.Text('IP', font=font, key='ip'),
         pyGUI.InputText(pad=((63, 0), (0, 0)), font=font, disabled_readonly_background_color='#2c2825',
                         use_readonly_for_disable=True, key='ip_text')],
        [pyGUI.Text('User', font=font, key='user', visible=False),
         pyGUI.InputText(pad=((45, 0), (0, 0)), font=font, use_readonly_for_disable=True, key='user_text',
                         disabled_readonly_background_color='#2c2825', visible=False)],
        [pyGUI.Text('Password', font=font, key='password', visible=False),
         pyGUI.InputText(pad=((8, 0), (0, 0)), font=font, use_readonly_for_disable=True, key='password_text',
                         disabled_readonly_background_color='#2c2825', password_char='*', visible=False)],
        [pyGUI.Text('Command', font=font, key='command', visible=False),
         pyGUI.InputText(font=font, key='command_text', visible=False)],
        [pyGUI.Output(font=font, size=(53, 25), key='list', visible=True)],
        [pyGUI.OK(font=font, key="OK", button_text="Connect"),
         pyGUI.Button(font=font, button_text="Reset"), pyGUI.Exit(font=font, pad=((10, 0), (0, 0)), button_color="Red")]
    ]
window = pyGUI.Window('Client PSQL', layout)
sock = socket.socket()
sock.settimeout(5)


def reset():
    global window, sock, is_connected, is_confirmed
    window['ip_text'].Update(disabled=False, value='')
    window['password_text'].Update(disabled=False, visible=False, value='')
    window['command_text'].Update(visible=False, value='')
    window['user_text'].Update(disabled=False, visible=False, value='')
    window['password'].Update(visible=False)
    window['command'].Update(visible=False)
    window['user'].Update(visible=False)
    window['list'].Update(value='')
    window['OK'].Update(text='Connect')
    is_connected, is_confirmed = False, False
    sock.send("EXIT".encode())
    sock.close()
    sock = socket.socket()


while not is_closed:
    event, values = window.read()
    match event:
        case pyGUI.WIN_CLOSED | 'Exit':
            if is_confirmed:
                sock.send("EXIT".encode())
            is_closed = True
            break
        case "Reset":
            reset()
        case "OK":
            if is_connected:
                if is_confirmed:
                    if values['command_text'].upper() in ["EXIT", "EXIT;", "QUIT", "QUIT;"]:
                        reset()
                    else:
                        try:
                            sock.send((values['command_text']).encode())
                            output = sock.recv(1024).decode()
                            print(output.split('>')[0], '=>', values['command_text'])
                            print("\n" + (values['command_text'].split(" ")[0] + ' ' +
                                          values['command_text'].split(" ")[1]
                                  if output.split('>')[1] == "\nno results to fetch\n"
                                          else output.split('>')[1]) + "\n")
                        except socket.error as Error:
                            reset()
                            print("Connection denied!")
                else:
                    try:
                        sock.send((values['user_text'] + '\n' + values['password_text']).encode())
                        answer = sock.recv(1024).decode()
                        print(answer)
                        if answer.split(' ')[2] != "denied!":
                            window['user_text'].Update(disabled=True)
                            window['password_text'].Update(disabled=True)
                            window['command'].Update(visible=True)
                            window['command_text'].Update(visible=True)
                            window['list'].Update(visible=True)
                            window['OK'].Update(text='Enter')
                            is_confirmed = True
                    except socket.error as Error:
                        reset()
                        print("Connection denied!")
            else:
                try:
                    sock.connect((values['ip_text'], 9090))
                    window['ip_text'].Update(disabled=True)
                    window['user'].Update(visible=True)
                    window['user_text'].Update(visible=True)
                    window['password'].Update(visible=True)
                    window['password_text'].Update(visible=True)
                    window['OK'].Update(text='Confirm')
                    print("Connection was successful! Enter a user and his password!")
                    is_connected = True
                except Exception as error:
                    print("Connection was denied! ", error)
window.close()
sock.close()
