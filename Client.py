import PySimpleGUI as pyGUI
import keyboard
import socket


def set_connection_mass(ip, login, password):
    with open("last_connect.txt", 'w') as file:
        file.write(ip + ' ' + login + ' ' + password)


def get_connection_mass():
    lineMass = []
    try:
        with open("last_connect.txt", 'r') as file:
            for line in file:
                lineMass += [line.split(' ')]
    finally:
        return lineMass


def send_text(Sock, text):
    try:
        size_str = "0" * (8 - len(str(len(text)))) + str(len(text))
        Sock.send(size_str.encode())
        Sock.send(text.encode())
    except socket.error:
        pass


def get_text(Sock):
    try:
        size = int(Sock.recv(8).decode())
        answer = ""
        while len(answer) != size:
            answer += Sock.recv(size - len(answer)).decode()
        return answer
    except socket.error:
        return None


def reset_con(Window, Sock, Is_connected):
    Window['status'].Update(value='Status: none')
    Window['password_text'].Update(visible=False, value='', disabled=False)
    Window['user_text'].Update(visible=False, value='', disabled=False)
    Window['ip_text'].Update(value='', disabled=False)
    Window['password'].Update(visible=False)
    Window['user'].Update(visible=False)
    Window['OK'].Update(text='Connect')
    if Is_connected:
        Sock.close()
        Sock = socket.socket()
        socket.timeout(5)
    return Window, Sock, False, False


def auto_fill(Window):
    connection_mass = get_connection_mass()
    if len(connection_mass) > 0:
        Window['ip_text'].Update(value=connection_mass[-1][0])
        Window['user_text'].Update(value=connection_mass[-1][1])
        Window['password_text'].Update(value=connection_mass[-1][2])
    return Window


def connection(Window, Values, Sock):
    try:
        Sock.connect((Values['ip_text'], 9090))
        Window['ip_text'].Update(disabled=True)
        Window['user'].Update(visible=True)
        Window['user_text'].Update(visible=True)
        Window['password'].Update(visible=True)
        Window['password_text'].Update(visible=True)
        Window['status'].Update(value="Status: successful")
        Window['OK'].Update(text='Confirm')
        return Window, Sock, True
    except socket.error:
        Window['status'].Update(value="Status: denied")
        return Window, Sock, False


def authorization(Window, Sock, Values):
    try:
        send_text(Sock, Values['user_text'] + '\n' + Values['password_text'])
        answer = get_text(Sock).split('>')
        if answer[0] == "0":
            return Window, Sock, True, True
    except socket.error:
        Window['status'].Update(value="Status: denied")
        return Window, Sock, False, False
    Window['status'].Update(value="Status: denied")
    return Window, Sock, True, False


def set_table_text(Window, Output_data, headings):
    col_widths = [min([max(map(len, columns)) + 2]) * 8 for columns in
                  zip(*Output_data)]
    Window['table'].Update(values=Output_data[1:])
    for cid in headings:
        Window['table'].widget.heading(cid, text='')
        Window['table'].widget.column(cid, width=0)
    for cid, text, width in zip(headings, Output_data[0], col_widths):
        Window['table'].widget.heading(cid, text=text)
        Window['table'].widget.column(cid, width=width)
    return Window


def up_arrow(Window, Values, Commands, Index_command):
    Commands[Index_command] = Values['command_text']
    if Index_command != 0:
        Index_command -= 1
        Window['command_text'].Update(value=Commands[Index_command])
    return Window, Commands, Index_command


def down_arrow(Window, Values, Commands, Index_command):
    Commands[Index_command] = Values['command_text']
    if Index_command != len(Commands) - 1:
        Index_command += 1
        Window['command_text'].Update(value=Commands[Index_command])
    return Window, Commands, Index_command


def communication(Window, Sock, Values, Commands, Index_command, headings):
    if Values['command_text'].upper() == "CLEAR":
        Window['list'].Update(value='')
        return Window, Sock, True
    try:
        Commands[Index_command] = Values['command_text']
        if Commands[-1] != "":
            Commands.append("")
            Window['command_text'].Update(value='')
        send_text(Sock, Values['command_text'])
        Output = get_text(Sock).split('>')
        print(Output[1], '=>', Values['command_text'])
        if Output[-1] == "\nno results to fetch\n":
            print(Values['command_text'].split(' ')[0] + ' ' + Values['command_text'].split(' ')[1])
        elif Output[0] != '0' or Output[-1].split(' ')[0] == 'Connect':
            print(Output[-1])
        else:
            Window = set_table_text(Window, [out.split('\t') for out in Output[-1].split('\n')], headings)
        return Window, Sock, True
    except socket.error as Error:
        print(Error)
        return Window, Sock, False


def application(Sock, Font):
    is_connected, is_closed, index_command, head_count, commands = True, False, 0, 10, [""]
    headings = [f'h{i}' for i in range(head_count)]
    layout = \
        [

            [pyGUI.Table(values=[["      "] * head_count], headings=headings, vertical_scroll_only=False,
                         num_rows=20, def_col_width=100, display_row_numbers=True, justification='center',
                         key='table')],
            [pyGUI.Output(size=(78, 10), key='list')],
            [pyGUI.Text('Command', key='command'),
             pyGUI.InputText(size=(70, 10), key='command_text', enable_events=True)],
            [pyGUI.OK(key="OK", button_text="Enter"),
             pyGUI.Button(button_text="Reset"),
             pyGUI.Exit(pad=((10, 0), (0, 0)), button_color="Red")]
        ]
    window = pyGUI.Window('Client PSQL', layout, font=Font, finalize=True)
    while not is_closed:
        event, values = window.read()
        match event:
            case pyGUI.WIN_CLOSED | 'Exit':
                send_text(Sock, "EXIT")
                Sock.close()
                is_connected, is_closed = False, True
            case "Reset":
                is_closed = True
            case "OK":
                if values['command_text'].upper() in ["EXIT", "EXIT;", "QUIT", "QUIT;"]:
                    is_closed = True
                else:
                    window, Sock, is_connected = communication(window, Sock, values, commands, index_command, headings)
                    index_command = len(commands) - 1
        if keyboard.is_pressed('up'):
            window, commands, index_command = up_arrow(window, values, commands, index_command)
        elif keyboard.is_pressed('down'):
            window, commands, index_command = down_arrow(window, values, commands, index_command)

    window.close()
    return not is_connected


def connect_application():
    is_connected, is_confirmed, is_closed = False, False, False
    pyGUI.theme("DarkAmber")
    font = ("Arial", 13)
    layout = \
        [
            [pyGUI.Text('Status: none', key='status')],
            [pyGUI.Text('IP', key='ip'),
             pyGUI.InputText(pad=((63, 0), (0, 0)), disabled_readonly_background_color='#2c2825',
                             use_readonly_for_disable=True, key='ip_text')],
            [pyGUI.Text('User', font=font, key='user', visible=False),
             pyGUI.InputText(pad=((45, 0), (0, 0)), use_readonly_for_disable=True, key='user_text',
                             disabled_readonly_background_color='#2c2825', visible=False)],
            [pyGUI.Text('Password', key='password', visible=False),
             pyGUI.InputText(pad=((8, 0), (0, 0)), use_readonly_for_disable=True, key='password_text',
                             disabled_readonly_background_color='#2c2825', password_char='*', visible=False)],
            [pyGUI.OK(key="OK", button_text="Connect"),
             pyGUI.Exit(pad=((10, 0), (0, 0)), button_color="Red")]
        ]
    window = pyGUI.Window('Connect to Server PSQL', layout, font=font, finalize=True)
    window = auto_fill(window)
    sock = socket.socket()
    sock.settimeout(5)
    while not is_closed:
        event, values = window.read()
        match event:
            case pyGUI.WIN_CLOSED | 'Exit':
                is_closed = True
            case "OK":
                if not is_connected:
                    window, sock, is_connected = connection(window, values, sock)
                else:
                    window, sock, is_connected, is_confirmed = authorization(window, sock, values)
        if is_confirmed:
            window.hide()
            is_closed = application(sock, font)
            set_connection_mass(values['ip_text'], values['user_text'], values['password_text'])
            window.un_hide()
            window, sock, is_connected, is_confirmed = reset_con(window, sock, is_connected)
            window = auto_fill(window)

    window.close()
    sock.close()


connect_application()
