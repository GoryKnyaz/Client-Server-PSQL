import socket
import psycopg2
import subprocess
import sys


def send_text(ClientConnected, text):
    size_str = "0" * (8 - len(str(len(text)))) + str(len(text))
    ClientConnected.send(size_str.encode())
    ClientConnected.send(text.encode())


def get_text():
    size = int(clientConnected.recv(8).decode())
    answer = ""
    while len(answer) != size:
        answer += clientConnected.recv(size - len(answer)).decode()
    return answer


def authorization(ClientConnected):
    while True:
        data_from_client = get_text()
        if data_from_client == "EXIT":
            return False, None, None
        try:
            login_password = data_from_client.split("\n")
            conn = psycopg2.connect(
                f"user='{login_password[0]}' password='{login_password[1]}' "
                f"host='127.0.0.1' port='5432' dbname='postgres'")
            break
        except psycopg2.DatabaseError as Error:
            send_text(ClientConnected, f"1>Authorization was denied!{str(Error)}")
    print(f"Authorization was successfully!\nHello {login_password[0]}!")
    send_text(ClientConnected, f"0>Authorization was successfully!\nHello {login_password[0]}!\n")
    return True, conn, login_password


def connect(ClientConnected):
    dbname = "postgres"
    try:
        is_connected, conn, login_password = authorization(ClientConnected)
        if not is_connected:
            return
        conn.autocommit = True
        with conn.cursor() as cur:
            command_from_client = get_text()
            while command_from_client.upper().split(';')[0] != "EXIT":
                try:
                    command_list = command_from_client.split(' ')
                    if command_list[0].upper() == "CONNECT":
                        new_dbname = command_list[1].split(';')[0]
                        new_conn = psycopg2.connect(
                            f"user='{login_password[0]}' password='{login_password[1]}' host='127.0.0.1' port='5432' "
                            f"dbname='{new_dbname}'")
                        conn.close()
                        cur.close()
                        conn = new_conn
                        conn.autocommit = True
                        cur = conn.cursor()
                        dbname = new_dbname
                        send_text(ClientConnected, f"0>{dbname}>Connect to {new_dbname} completed")
                        command_from_client = get_text()
                        continue
                    cur.execute(command_from_client)
                    output = cur.fetchall()
                    send_text(ClientConnected, f"0>{dbname}>" +
                              "".join(
                                  [str(desc[0]) + ('' if desc[0] is cur.description[-1][0] else '\t') for desc in
                                   cur.description]) +
                              "".join(
                                  [('\n' if column is row[0] else '\t') + str(column) for row in output for column in
                                   row]))
                except Exception as Error:
                    conn.rollback()
                    send_text(ClientConnected, f"2>{dbname}>{str(Error)}")
                command_from_client = get_text()
    except (Exception, psycopg2.DatabaseError) as Error:
        print('\tError: ', Error)
        send_text(ClientConnected, f"3>{dbname}>{str(Error)}")
    finally:
        if conn is not None:
            conn.close()


serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    serverSocket.bind(('', 9090))
    serverSocket.listen()
    print("Server is ready.\nWaiting for connection from client.")
    if sys.platform == 'win32':
        print("Ip address command:", subprocess.run(["ipconfig"], capture_output=True, text=True).stdout)
    elif sys.platform == 'linux':
        print("ip address command:",
              subprocess.run(["ip", "-f", "inet", "address"], capture_output=True, text=True).stdout)
    (clientConnected, clientAddress) = serverSocket.accept()
    print(f"Accepted a connection request from {clientAddress[0]}:{clientAddress[1]}")
    connect(clientConnected)
    print(f"Disconnect a connection request from {clientAddress[0]}:{clientAddress[1]}")
except Exception as error:
    print(error)
finally:
    serverSocket.close()
