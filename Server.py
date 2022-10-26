import sys
import socket
import psycopg2
import subprocess


def connect(ClientConnected):
    conn = None
    dbname = ""
    try:
        while True:
            data_from_client = clientConnected.recv(1024)
            try:
                str_list = data_from_client.decode().split("\n")
                conn = psycopg2.connect(
                    "user='%s' password='%s' host='127.0.0.1' port='5432' dbname='postgres'" % (
                        str_list[0], str_list[1]))
                dbname = "postgres"
                break
            except Exception as Error:
                ClientConnected.send(("Authorization was denied! " + str(Error)).encode())
                if conn is not None:
                    conn.close()
        print("Authorization was successfully! Hello %s!" % str_list[0])
        conn.autocommit = True
        ClientConnected.send(("Authorization was successfully! Hello %s!" % str_list[0]).encode())
        with conn.cursor() as cur:
            command_from_client = ClientConnected.recv(1024).decode()
            while command_from_client.upper().split(';')[0] not in ["EXIT", "QUIT"]:
                try:
                    command_list = command_from_client.split(' ')
                    if command_list[0].upper() == "CONNECT":
                        new_dbname = command_list[1].split(';')[0]
                        new_conn = psycopg2.connect(
                            "user='%s' password='%s' host='127.0.0.1' port='5432' dbname='%s'" % (
                                str_list[0], str_list[1], new_dbname))
                        conn.close()
                        conn = new_conn
                        conn.autocommit = True
                        cur = conn.cursor()
                        ClientConnected.send((dbname + ">\nConnect to %s completed\n" % new_dbname).encode())
                        dbname = new_dbname
                        command_from_client = ClientConnected.recv(1024).decode()
                        continue
                    cur.execute(command_from_client)
                    output = cur.fetchall()
                    ClientConnected.send(
                        (dbname + ">" + "".join(
                            [('\n' if column is row[0] else ' ') + str(column)
                             for row in output for column in row]) + '\n').encode())
                except Exception as Error:
                    conn.rollback()
                    ClientConnected.send((dbname + ">\n" + str(Error) + "\n").encode())
                command_from_client = ClientConnected.recv(1024).decode()
    except (Exception, psycopg2.DatabaseError) as Error:
        print('\tError: ', Error)
        ClientConnected.send((dbname + ">\n" + str(Error) + "\n").encode())
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
        print("Ip address command:", subprocess.run(["ip", "-f", "inet", "address"], capture_output=True, text=True).stdout)
    (clientConnected, clientAddress) = serverSocket.accept()
    print("Accepted a connection request from %s:%s" % (clientAddress[0], clientAddress[1]))
    connect(clientConnected)
    print("Disconnect a connection request from %s:%s" % (clientAddress[0], clientAddress[1]))
except Exception as error:
    print(error)
finally:
    serverSocket.close()
