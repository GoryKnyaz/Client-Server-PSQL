import keyboard
import PySimpleGUI as pyGUI
import socket


def set_command_to_array(Commands, Command, Index_command):
    if Index_command == len(Commands):
        Commands.append(Command)
    else:
        Commands[Index_command] = Command


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
        Sock.send(size_str.encode('utf-8'))
        Sock.send(text.encode('utf-8'))
    except socket.error:
        pass


def get_text(Sock):
    try:
        size = int(Sock.recv(8).decode('utf-8'))
        answer = ""
        while len(answer) != size:
            answer += Sock.recv(size - len(answer)).decode('utf-8')
        return answer
    except socket.error:
        return None


def get_public_tables(Window, Sock, Commands, Index_command, Headings):
    return communication(Window, Sock, "select table_name from information_schema.tables where table_schema='public'",
                         Commands, Index_command, Headings)


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
        Sock.settimeout(5)
    return Sock, False, False


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
        return True
    except socket.error:
        Window['status'].Update(value="Status: denied")
        return False


def authorization(Window, Sock, login_password):
    try:
        send_text(Sock, login_password)
        answer = get_text(Sock).split('>')
        if answer[0] == "0":
            return True, True
    except socket.error:
        Window['status'].Update(value="Status: denied")
        return False, False
    Window['status'].Update(value="Status: denied")
    return True, False


def set_table_text(Window, Output_data, headings):
    min_width_table = 660
    col_widths = [min([max(map(len, columns)) + 2]) * 8 for columns in
                  zip(*Output_data)]
    Window['table'].Update(values=Output_data[1:])
    for cid in headings:
        Window['table'].widget.heading(cid, text='')
        Window['table'].widget.column(cid, width=0)
    new_width_table, min_width_column = sum(col_widths), min_width_table // len(col_widths)
    for cid, text, width in zip(headings, Output_data[0], col_widths):
        Window['table'].widget.heading(cid, text=text)
        Window['table'].widget.column(cid, width=(width if new_width_table >= min_width_table else min_width_column))


def up_arrow(Window, Command, Commands, Index_command):
    if Command != '':
        set_command_to_array(Commands, Command, Index_command)
    if Index_command != 0:
        Index_command -= 1
        Window['command_text'].Update(value=Commands[Index_command])
    return Index_command


def down_arrow(Window, Command, Commands, Index_command):
    if Index_command < len(Commands) - 1:
        Commands[Index_command] = Command
        Index_command += 1
        Window['command_text'].Update(value=Commands[Index_command])
    else:
        Index_command = len(Commands)
        Window['command_text'].Update(value='')
    return Index_command


def communication(Window, Sock, Command, Commands, Index_command, Headings):
    if Command.upper() == "CLEAR":
        Window['list'].Update(value='')
        return Index_command, True
    try:
        if Command != "" and (Command != Commands[-1] if len(Commands) != 0 else True):
            if Index_command == len(Commands):
                Commands.append(Command)
            else:
                Commands[Index_command] = Command
            Index_command = len(Commands)
        Window['command_text'].Update(value='')
        send_text(Sock, Command)
        Output = get_text(Sock).split('>')
        print(Output[1], '=>', Command)
        if Output[-1] == "\nno results to fetch\n":
            print(Command.split(' ')[0] + ' ' + Command.split(' ')[1])
        elif Output[0] != '0' or Output[-1].split(' ')[0] == 'Connect':
            print(Output[-1])
        else:
            set_table_text(Window, [out.split('\t') for out in Output[-1].split('\n')], Headings)
        return Index_command, True
    except socket.error as Error:
        print(Error)
        return Index_command, False


def application(Sock, Font):
    is_connected, is_closed, index_command, head_count, commands, prev_click = True, False, 0, 10, [], (-1, -1)
    headings = [f'h{i}' for i in range(head_count)]
    layout = \
        [

            [pyGUI.Table(values=[["      "] * head_count], headings=headings, vertical_scroll_only=False,
                         num_rows=20, def_col_width=100, display_row_numbers=True, justification='center',
                         key='table', enable_click_events=True)],
            [pyGUI.Output(size=(78, 10), key='list')],
            [pyGUI.Text('Command', key='command'),
             pyGUI.InputText(size=(70, 10), key='command_text', enable_events=True)],
            [pyGUI.OK(key="OK", button_text="Enter"),
             pyGUI.Button(button_text="Reset"),
             pyGUI.Exit(pad=((10, 0), (0, 0)), button_color="Red")]
        ]
    window = pyGUI.Window('Client PSQL', layout, font=Font, finalize=True)
    index_command, is_connected = get_public_tables(window, Sock, commands, index_command, headings)
    while not is_closed:
        event, values = window.read()
        match event:
            case pyGUI.WIN_CLOSED | 'Exit':
                send_text(Sock, "EXIT")
                Sock.close()
                is_connected, is_closed = False, True
                pass
            case "Reset":
                is_closed = True
                pass
            case "OK":
                if values['command_text'].upper() in ["EXIT", "EXIT;", "QUIT", "QUIT;"]:
                    is_closed = True
                else:
                    index_command, is_connected = communication(window, Sock, values['command_text'], commands,
                                                                index_command, headings)
                pass
            case ("table", "+CLICKED+", (row, col)):
                if prev_click == event[-1]:
                    index_command, is_connected = communication(window, Sock,
                                                                "select * from " +
                                                                window['table'].Values[row][col],
                                                                commands, index_command, headings)
                prev_click = event[-1]
                pass
        if keyboard.is_pressed('up'):
            index_command = up_arrow(window, values['command_text'], commands, index_command)
        elif keyboard.is_pressed('down'):
            index_command = down_arrow(window, values['command_text'], commands, index_command)
        elif keyboard.is_pressed('esc'):
            index_command, is_connected = get_public_tables(window, Sock, commands, index_command, headings)

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
            [pyGUI.Text('User', key='user', visible=False),
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
                    is_connected = connection(window, values, sock)
                else:
                    is_connected, is_confirmed = authorization(window, sock,
                                                               values['user_text'] + '\n' + values['password_text'])
        if is_confirmed:
            window.hide()
            is_closed = application(sock, font)
            set_connection_mass(values['ip_text'], values['user_text'], values['password_text'])
            if not is_closed:
                window.un_hide()
                sock, is_connected, is_confirmed = reset_con(window, sock, is_connected)
                auto_fill(window)

    window.close()
    sock.close()


connect_application()
