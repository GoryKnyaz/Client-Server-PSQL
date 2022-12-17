import keyboard
import PySimpleGUI as pyGUI
import socket


class MySocket(socket.socket):
    def __init__(self):
        super().__init__()
        super().settimeout(5)

    def __del__(self):
        super().close()

    def send_text(self, text):
        size_str = "0" * (8 - len(str(len(text)))) + str(len(text))
        super().send(size_str.encode('utf-8'))
        super().send(text.encode('utf-8'))

    def get_text(self):
        size = int(super().recv(8).decode('utf-8'))
        answer = ""
        while len(answer) != size:
            answer += super().recv(size - len(answer)).decode('utf-8')
        return answer

    def my_connect(self, IP):
        try:
            super().connect((IP, 9090))
            return True
        except socket.error:
            return False

    def my_authorization(self, Login_Password):
        try:
            self.send_text(Login_Password)
            answer = self.get_text().split('>')
        except socket.error:
            return False, False
        return True, answer[0] == "0"

    def my_communication(self, Command):
        self.send_text(Command)
        Output = self.get_text().split('>')
        return Output


class MyConnectionApp(pyGUI.Window):
    def __init__(self, Font):
        Layout = \
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
        self.is_connect = False
        self.is_confirm = False
        self.my_socket = MySocket()
        self.auto_filling = []
        super().__init__('Connect to Server PSQL', Layout, font=Font, finalize=True)

    def __del__(self):
        super().close()

    @staticmethod
    def __get_connection_mass():
        lineMass = []
        try:
            with open("last_connect.txt", 'r') as file:
                for line in file:
                    lineMass += [line.split(' ')]
        finally:
            return lineMass

    @staticmethod
    def __set_connection_mass(Ip, Login_Password):
        with open("last_connect.txt", 'w') as file:
            file.write('%s %s %s' % (Ip, Login_Password[0], Login_Password[1]))

    def auto_fill(self):
        self.auto_filling = self.__get_connection_mass()
        if len(self.auto_filling) > 0:
            self['ip_text'].Update(value=self.auto_filling[-1][0])
            self['user_text'].Update(value=self.auto_filling[-1][1])
            self['password_text'].Update(value=self.auto_filling[-1][2])

    def reset_con(self):
        self['status'].Update(value='Status: none')
        self['password_text'].Update(visible=False, value='', disabled=False)
        self['user_text'].Update(visible=False, value='', disabled=False)
        self['ip_text'].Update(value='', disabled=False)
        self['password'].Update(visible=False)
        self['user'].Update(visible=False)
        self['OK'].Update(text='Connect')
        if self.is_connect:
            self.my_socket.close()
            self.my_socket = MySocket()
            self.is_connect = False
            self.is_confirm = False

    def connection(self, IP):
        self.is_connect = self.my_socket.my_connect(IP)
        if self.is_connect:
            self.my_socket.my_connect(IP)
            self['ip_text'].Update(disabled=True)
            self['user'].Update(visible=True)
            self['user_text'].Update(visible=True)
            self['password'].Update(visible=True)
            self['password_text'].Update(visible=True)
            self['status'].Update(value="Status: successful")
            self['OK'].Update(text='Confirm')
        else:
            self['status'].Update(value="Status: denied")

    def authorization(self, IP, Login_Password):
        self.is_connect, self.is_confirm = self.my_socket.my_authorization(Login_Password)
        if self.is_connect:
            if self.is_confirm:
                self.__set_connection_mass(IP, Login_Password.split('\n'))
                return True
            else:
                self['status'].Update(value="Status: denied")
        else:
            self.reset_con()
            self['status'].Update(value="Status: disconnect")
        return False


class MyTable(pyGUI.Table):
    def __init__(self):
        self.index_line = 0
        self.starting_row = 0
        self.prev_click = (-1, -1)
        self.this_table = ''
        self.row_count = 0
        self.head_count = 10
        self.max_rows = 20
        self.min_width_table = 660
        self.headings = [f'h{i}' for i in range(self.head_count)]
        super().__init__(values=[["      "] * self.head_count], headings=self.headings, vertical_scroll_only=False,
                         num_rows=20, def_col_width=100, display_row_numbers=True, justification='center',
                         key='table', enable_click_events=True)

    def insert(self, Window, Datas):
        col_widths = [min([max(map(len, columns)) + 2]) * 8 for columns in
                      zip(*Datas)]
        Window['table'].StartingRowNumber = self.starting_row
        Window['table'].Update(values=Datas[1:])
        for cid in self.headings:
            Window['table'].widget.heading(cid, text='')
            Window['table'].widget.column(cid, width=0)
        new_width_table, min_width_column = sum(col_widths), self.min_width_table // len(col_widths)
        for cid, text, width in zip(self.headings, Datas[0], col_widths):
            Window['table'].widget.heading(cid, text=text)
            Window['table'].widget.column(cid, width=(
                width if new_width_table >= self.min_width_table else min_width_column))
        Window['prevLines'].Update(disabled=True)
        Window['nextLines'].Update(disabled=True)

    def click_to_table(self, Window, Row_Column):
        row, column = Row_Column
        if row is not None and self.prev_click == Row_Column:
            Window.my_socket.send_text("select count(*) from " + Window['table'].Values[row][column] + ';')
            Code, Database, Result = Window.my_socket.get_text().split('>')
            if Code != '0':
                return
            self.starting_row = 0
            self.this_table = Window['table'].Values[row][column]
            self.prev_click = (-1, -1)
            self.index_line = 0
            self.row_count = int(Result.split('\n')[-1])
            Window.communication("select * from " + self.this_table + f' limit {self.max_rows};')
            Window['prevLines'].Update(disabled=True)
            Window['nextLines'].Update(disabled=self.row_count <= self.max_rows)
        else:
            self.prev_click = Row_Column

    def prev_datas(self, Window):
        self.index_line -= 1
        self.starting_row = self.index_line * self.max_rows
        Window.communication(
            "select * from " + self.this_table + f' offset {self.index_line * self.max_rows} limit {self.max_rows};')
        Window['prevLines'].Update(disabled=self.index_line == 0)
        Window['nextLines'].Update(disabled=False)

    def next_datas(self, Window):
        self.index_line += 1
        self.starting_row = self.index_line * self.max_rows
        Window.communication(
            "select * from " + self.this_table +
            f' offset {self.index_line * 20} limit '
            f'{min(self.max_rows, self.row_count - self.index_line * self.max_rows)};',
        )
        Window['prevLines'].Update(disabled=False)
        Window['nextLines'].Update(disabled=self.row_count - (self.index_line + 1) * self.max_rows <= 0)


class MyCommandString(pyGUI.InputText):
    def __init__(self):
        self.this_command = ""
        self.index_command = 0
        self.commands = []
        super().__init__(size=(77, 10), key='command_text', enable_events=True)

    def up_arrow(self, Window, Command):
        if Command != '':
            if self.index_command == len(self.commands):
                self.commands.append(Command)
            else:
                self.commands[self.index_command] = Command
        if self.index_command != 0:
            self.index_command -= 1
            Window['command_text'].Update(value=self.commands[self.index_command])

    def down_arrow(self, Window, Command):
        if self.index_command < len(self.commands) - 1:
            self.commands[self.index_command] = Command
            self.index_command += 1
            Window['command_text'].Update(value=self.commands[self.index_command])
        else:
            self.index_command = len(self.commands)
            Window['command_text'].Update(value='')

    def insert(self, Command):
        if Command != "" and (Command != self.commands[-1] if len(self.commands) != 0 else True):
            if self.index_command == len(self.commands):
                self.commands.append(Command)
            else:
                self.commands[self.index_command] = Command
            self.index_command = len(self.commands)

    def analise(self, Window, Command):
        if Command.find(';') == -1:
            self.this_command += Command + (' ' if Command[-1] != ' ' else '')
            print('->', Command)
            Window['command_text'].Update(value='')
        else:
            text_command = Command.split(';')
            print(f'-> {Command}' if len(text_command) != 2 or text_command[1] != '' else '')
            for command in text_command:
                if self.this_command == '' and command == '':
                    continue
                self.this_command += command + ';'
                Window.communication(self.this_command)
                self.this_command = ""

    def key_pressed(self, Window, Command):
        if self.this_command == '':
            if keyboard.is_pressed('up'):
                self.up_arrow(Window, Command)
            elif keyboard.is_pressed('down'):
                self.down_arrow(Window, Command)
            elif keyboard.is_pressed('esc'):
                Window.get_public_tables()
                Window.my_table.prev_click = (-1, -1)
        else:
            if keyboard.is_pressed('esc'):
                print('--command is cleaning--')
                Window['command_text'].Update(value='')
                self.this_command = ""


class MyApp(pyGUI.Window):
    def __init__(self, Sock, Font):
        self.my_socket = Sock
        self.my_table = MyTable()
        self.my_command_string = MyCommandString()
        Layout = \
            [
                [self.my_table,
                 pyGUI.Button(button_text="↑", key='prevLines', disabled=True),
                 pyGUI.Button(button_text="↓", key='nextLines', disabled=True)],
                [pyGUI.Output(size=(85, 10), key='output')],
                [pyGUI.Text('Command', key='command'), self.my_command_string],
                [pyGUI.OK(button_text="Enter", key="OK"),
                 pyGUI.Button(button_text="Reset"),
                 pyGUI.Exit(pad=((10, 0), (0, 0)), button_color="Red"),
                 pyGUI.Button(button_text="Execute Commands From File", pad=((388, 0), (0, 0)), key='EXEC')]
            ]
        super().__init__('Client PSQL', Layout, font=Font, finalize=True)

    def __del__(self):
        super().close()

    @staticmethod
    def delete_spaces(string):
        while string.find('  ') != -1:
            string = string.replace('  ', ' ')
        return string

    @staticmethod
    def quotes(stringMass):
        new_stringMass = []
        was_quotes = False
        new_string = ""
        for string in stringMass:
            quotes_index = string.find('$$')
            if quotes_index != -1:
                if was_quotes:
                    new_stringMass.append(new_string + string)
                    new_string = ""
                else:
                    new_string += string + '; '
                was_quotes = not was_quotes
            else:
                if was_quotes:
                    new_string += string + '; '
                else:
                    new_stringMass.append(string)
        new_stringMass.append(new_string)
        return new_stringMass

    def communication(self, Command):
        try:
            self.my_command_string.insert(Command)
            self['command_text'].Update(value='')
            Code, DataBase, Result = self.my_socket.my_communication(Command)
            print(DataBase, '=>', Command)
            if Result == "\nno results to fetch\n":
                print(Command.split(' ')[0] + ' ' + Command.split(' ')[1])
            elif Code != '0' or Result.split(' ')[0] == 'Connect':
                print(Result)
            else:
                self.my_table.insert(self, [out.split('\t') for out in Result.split('\n')])
            return True
        except socket.error as Error:
            print(Error)
            return False

    def get_public_tables(self):
        self.my_table.starting_row = 0
        return self.communication("select table_name from information_schema.tables where table_schema='public';")

    def execute_commands_from_file(self, File):
        outputMass = []
        try:
            with open(File, 'r') as commandFile:
                lineFileMass = [str(line).replace('\t', '').replace('\n', '') for line in commandFile]
            commandsMass = self.quotes([self.delete_spaces(command) for command in
                                        ("".join(
                                            line + (' ' if line.find(';') == -1 else '') for line in
                                            lineFileMass)).split(';')])
            for command in commandsMass:
                if command != '':
                    self.my_socket.send_text(command)
                    outputMass.append(self.my_socket.get_text())
                else:
                    commandsMass.remove('')
            outputFile = File.split('.')[:1]
            with open("".join(s + ('.' if s is not outputFile[-1] else '') for s in outputFile) + '_output.txt',
                      'w') as outputFile:
                for command, output in zip(commandsMass, outputMass):
                    outputFile.write(command + ';\n' + output.split('>')[-1] + '\n\n')

            return True
        finally:
            return False


def my_application(Sock, Font):
    is_closed, row_count, index_line = False, 0, 0
    window = MyApp(Sock, Font)
    window.get_public_tables()
    while not is_closed:
        event, values = window.read()
        match event:
            case pyGUI.WIN_CLOSED | 'Exit':
                window.my_socket.send_text(Sock, "EXIT")
                return True
            case "Reset":
                return False
            case "OK":
                if values['command_text'] == '':
                    continue
                elif values['command_text'].upper() in ["EXIT", "EXIT;", "QUIT", "QUIT;"]:
                    return False
                elif values['command_text'].upper() in ["CLEAR", "CLEAR;"]:
                    window['output'].Update(value='')
                else:
                    window.my_command_string.analise(window, values['command_text'])
                pass
            case "EXEC":
                window.execute_commands_from_file(pyGUI.popup_get_file('', no_window=True))
                pass
            case ("table", "+CLICKED+", (row, col)):
                window.my_table.click_to_table(window, (row, col))
                pass
            case "prevLines":
                window.my_table.prev_datas(window)
                pass
            case "nextLines":
                window.my_table.next_datas(window)
                pass
        window.my_command_string.key_pressed(window, values['command_text'])
    return not window.my_socket.is_connected


def my_connect_application():
    pyGUI.theme("DarkAmber")
    font = ("Arial", 13)
    is_closed = False
    window = MyConnectionApp(font)
    window.auto_fill()
    while not is_closed:
        event, values = window.read()
        match event:
            case pyGUI.WIN_CLOSED | 'Exit':
                is_closed = True
            case "OK":
                if not window.is_connect:
                    window.connection(values['ip_text'])
                else:
                    window.authorization(values['ip_text'], values['user_text'] + '\n' + values['password_text'])
        if window.is_confirm:
            window.hide()
            is_closed = my_application(window.my_socket, font)
            if not is_closed:
                window.un_hide()
                window.reset_con()
                window.auto_fill()


my_connect_application()
