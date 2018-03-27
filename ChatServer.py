import socket
import sys
import threading
import Channel
import User
import Util
import datetime
import argparse


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}
    HELP_MESSAGE = """\n> The list of commands available are:

    /HELP                                                           - Show the instructions
    /JOIN [channel_name] [password]                                 - To create or switch to a channel.
    /QUIT                                                           - Exits the program.
    /LIST                                                           - Lists all available channels.

    /AWAY [messege]                                                 - mode - send everything as a privet message 
    /CONNECT [target server] [port] [remote server]                 - connect to a remote server
    /DIE                                                            - shut down server
    /INFO                                                           - Returns information about the <target> server, or the current server if <target> is omitted
    /INVITE [nickname] [channel]                                    - Invite a client to an invite-only channel
    /ISON [nicknames]                                               - Queries the server to see if the clients in the space-separated list <nicknames> are currently on the network.
    /KICK  [channel] [client]                                       - Eject a client from the channel
    /KILL [client]                                                  - forcibly remove client form server
    /KNOCK [channel]                                                - send a invite-request to a private channel
    /MODE                                                           - Change the channels mode
    /NICK  [nickname]                                               - change user nickname to [nickname] 
    /NOTICE [target user] [messege]                                 - private message, no auto reply
    /PART   [channel]                                               - user leaves specified channel
    /OPER [username] [password]                                     - authenticates user as operator
    /PASS [password]                                                - set a connection password
    /PING                                                           - test the connection with server
    /PONG                                                           - reply to the PING command
    /PRIVMSG [target] [message]                                     - private message to [target] 
    /RESTART                                                        - restart server
    /RULES                                                          - request server rules
    /SETNAME                                                        - allows to re-set a real name
    /SILENCE                                                        - FIXME - not gonna do it
    /TIME                                                           - returns server time
    /TOPIC                                                          - Change the channel topic in a mode
    /USER [username] [hostname] [realname]                          - This command is used at the beginning of a connection to specify the username, hostname, real name and initial user modes of the connecting client 
    /USERHOST [nickname]                                            - returns info on specified user
    /USERIP   [nickname]                                            - returns IP of [nickname]
    /USERS                                                          - return info on all of the users on the server
    /VERSION                                                        - returns server info    
    /WALLOPS [messege]                                              - send messege to all operators
    /WHO [name]                                                     - return a list of users who match [name]
    /WHOIS [nickname]                                               - returns info on nickname masks\n\n
    """.encode('utf8')

    WELCOME_MESSAGE = "\n> Welcome to our chat app!!!\n".encode('utf8')

    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True, timeout=3):
        self.address = (host, port)
        self.channels = {} # Channel Name -> Channel
        self.users_channels_map = {} # User Name -> Channel Name
        self.client_thread_list = [] # A list of all threads that are either running or have finished their task.
        self.users = [] # A list of all the users who are connected to the server.
        self.exit_signal = threading.Event()
        self.START_TIME = str(datetime.datetime.today())
        self.SERVER_VERSION = '0.5' # random number
        self.RULES = 'No rules'
        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - {0}".format(errorMessage))
            raise

        self.serverSocket.settimeout(timeout)

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0], self.address[1], errorMessage))
            raise

    def start_listening(self, defaultGreeting="\n> Welcome to our chat app!!! What is your full name?\n"):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])

        try:
            while not self.exit_signal.is_set():
                try:
                    print("Waiting for a client to establish a connection\n")
                    clientSocket, clientAddress = self.serverSocket.accept()
                    print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0], clientAddress[1]))
                    user = User.User(clientSocket)
                    user.status = 'Online'
                    self.users.append(user)
                    self.welcome_user(user)
                    clientThread = threading.Thread(target=self.client_thread, args=(user,))
                    clientThread.start()
                    self.client_thread_list.append(clientThread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            self.exit_signal.set()

        for client in self.client_thread_list:
            if client.is_alive():
                client.join()

    def welcome_user(self, user):
        user.socket.sendall(Server.WELCOME_MESSAGE)

    def client_thread(self, user, size=4096):
       # username = Util.generate_username(user.socket.recv(size).decode('utf8')).lower()
        username = None

        while not username:
            user.socket.sendall("\n> Press SEND\n".encode('utf8'))
            username = user.socket.recv(size).decode('utf8').lower()
            print('+' + username + '+')
            if username == "enter message.":
                user.socket.sendall("\n> Please enter the username you wish to use\n".encode('utf8'))
                username = user.socket.recv(size).decode('utf8').lower()
            if username in self.users:
                user.socket.sendall("\n> The username provided already exists, please choose a different username\n".encode('utf8'))
                username = None


        user.username = username

        welcomeMessage = '\n> Welcome {0}, type /help for a list of helpful commands.\n\n'.format(user.username).encode('utf8')
        user.socket.sendall(welcomeMessage)

        while True:
            chatMessage = user.socket.recv(size).decode('utf8').lower()

            if self.exit_signal.is_set():
                break

            if not chatMessage:
                break

            if '/quit' in chatMessage:
                self.quit(user)
                break
            elif '/list' in chatMessage:
                self.list_all_channels(user)
            elif '/help' in chatMessage:
                self.help(user)
            elif '/join' in chatMessage:
                self.join(user, chatMessage)
            # solution commands
            elif '/die' in chatMessage:  # DONE
                self.server_shutdown()
            elif '/info' in chatMessage:  # DONE
                # returns info about server
                self.serv_info(user)
            elif '/time' in chatMessage:
                # give server time
                message = ("Server time = " + str(datetime.datetime.today()) + "\n").encode('utf8')
                user.socket.sendall(message)
            elif '/kill' in chatMessage:
                # use a given method
                user.socket.sendall(self.kill_usr(chatMessage).encode('utf8'))
            elif '/ison' in chatMessage:
                # check if user is online
                user.socket.sendall(self.is_on(chatMessage).encode('utf8'))
            elif '/mode' in chatMessage:
                # will simplify and only allow /mode to change the mode of the channel
                user.socket.sendall(self.mode_ch(chatMessage).encode('utf8'))
            elif '/nick' in chatMessage:
                # change the nickname of the user
                user.socket.sendall(self.nick_change(user, chatMessage).encode('utf8'))
            elif '/pass' in chatMessage:
                user.socket.sendall(self.pass_change(user, chatMessage).encode('utf8'))
            elif '/version' in chatMessage:
                # send the server version info
                user.socket.sendall(self.SERVER_VERSION.encode('utf8'))
            elif '/topic' in chatMessage:
                user.socket.sendall(self.topic_set(chatMessage).encode('utf8'))
            elif '/rules' in chatMessage:
                user.socket.sendall(self.RULES.encode('utf8'))
            elif '/setname' in chatMessage:
                # change user's username
                user.socket.sendall(self.setname(user, chatMessage).encode('utf8'))
            elif '/users' in chatMessage:
                # show all users on the server
                user.socket.sendall(self.users_all().encode('utf8'))
            elif '/ping' in chatMessage:
                user.socket.sendall('/pong'.encode('utf8'))
            else:
                self.send_message(user, chatMessage + '\n')

        if self.exit_signal.is_set():
            user.socket.sendall('/squit'.encode('utf8'))

        user.socket.close()

    def quit(self, user):
        user.socket.sendall('/quit'.encode('utf8'))
        self.remove_user(user)

    def list_all_channels(self, user):
        if len(self.channels) == 0:
            chatMessage = "\n> No rooms available. Create your own by typing /join [channel_name]\n".encode('utf8')
            user.socket.sendall(chatMessage)
        else:
            chatMessage = '\n\n> Current channels available are: \n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ": " + str(len(self.channels[channel].users)) + " user(s)"
            chatMessage += "\n"
            user.socket.sendall(chatMessage.encode('utf8'))

    def help(self, user):
        user.socket.sendall(Server.HELP_MESSAGE)

    def join(self, user, chatMessage):
        isInSameRoom = False

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if user.username in self.users_channels_map: # Here we are switching to a new channel.
                if self.users_channels_map[user.username] == channelName:
                    user.socket.sendall("\n> You are already in channel: {0}".format(channelName).encode('utf8'))
                    isInSameRoom = True
                else: # switch to a new channel
                    oldChannelName = self.users_channels_map[user.username]
                    self.channels[oldChannelName].remove_user_from_channel(user) # remove them from the previous channel

            if not isInSameRoom:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel

                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username)
                self.users_channels_map[user.username] = channelName
        else:
            self.help(user.socket)

    def send_message(self, user, chatMessage):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].broadcast_message(chatMessage, "{0}: ".format(user.username))
        else:
            chatMessage = """\n> You are currently not in any channels:

Use /list to see a list of available channels.
Use /join [channel name] to join a channel.\n\n""".encode('utf8')

            user.socket.sendall(chatMessage)

    # my methods
    # send server infop to cient
    def serv_info(self, user):

        message = ("Server version = " + self.SERVER_VERSION + "\nServer start time = " + self.START_TIME + "\n").encode('utf8')
        # self.send_message(user, message)
        user.socket.sendall(message)

    # kill function with client name
    def kill_usr(self, text):
        if len(text.split()) <= 2:
            userName = text.split()[1]
            # print (userName + '\n')
            i = 0
            while i < len(self.users):
                # print(self.users[i].username)
                u = self.users[i].username
                if userName == u:
                    self.remove_user(self.users[i])
                    return 'User ' + u + ' has been removed\n'
                i += 1
            return 'User' + userName + ' not found\n'
        else:
            return 'Error, input is incorrect: /kill [client name]\n'

    # is_on method
    def is_on (self, text):
        if len(text.split()) == 2:
            userName = text.split()[1]
            # print (userName + '\n')
            i = 0
            while i < len(self.users):
                # print(self.users[i].username)
                if userName == self.users[i].nickname:
                    return 'User ' + userName + ' is connected\n'
                i += 1
            else:
                return userName + " not found\n"

        else:
            return 'Error, input is incorrect: /ison [client name]\n'

    # define a mode method for switching the mode of the channel
    def mode_ch (self, text):
        if len(text.split()) == 3:
            newMode = text.split()[1] # what to change the mode to
            channel = text.split()[2] # the name of the channel
            # need to fine correct channel
            i = 0
            while i < len(self.channels):
                if self.channels[channel]:
                    self.channels[channel].mode = newMode
                    return channel + ' mode has changed to ' + newMode
                i += 1
            else:
                return channel + " not found\n"

        else:
            return 'Error, input is incorrect: /mode [mode] [channel]\n'

    # define a method for changing users nickname
    def nick_change(self, user, text):
        nick = text.split()
        if len(nick) == 2:
            user.nickname = nick[1]
            return 'Nickname has been changed to ' + nick[1] + '\n'
        else:
            return 'Error, input is incorrect: /nick [new nickname]\n'

    # define a method that will change the connection password
    def pass_change (self, user, text):
        parse = text.split()
        if len(parse) == 2 and len(user.username) >= 1:
            user.password = parse[1]
            return "Password has been changed\n"
        else:
            return 'Error, user undefined or input is incorrect: /pass [new password]\n'

    # define method for changing a channels topic
    def topic_set(self, text):
        messege = text.split()
        if len(text.split()) >= 3:
            channel = messege[1]
            topic = ' '.join(messege[2:len(text.split())])
            i = 0
            while i < len(self.channels):
                if self.channels[channel]:
                    self.channels[channel].topic = topic
                    return 'Channel ' + channel + ' -> topic has been changed to ' + self.channels[channel].topic + '\n'
                else:
                    return 'Error, channel with a name ' + channel + ' was not found\n'
        else:
            return 'Error, user undefined or input is incorrect: /topic [channel] [topic]\n'

    # define method to re-set username
    def set_name (self, user, text):
        nick = text.split()
        if len(nick) == 2:
            user.username = nick[1]
            return 'Username has been changed to ' + user.username + '\n'
        else:
            return 'Error, input is incorrect: /setname [new username]\n'

    # define method for that show all users that are online
    def users_all(self):
        i = 0
        usersAll = ''
        while i < len(self.users):
            # usersAll +=  'User socket = '  + self.users[i].socket() + '\n' - soccet is an object
            usersAll +=  'User name = ' + self.users[i].username + '\n'
            usersAll +=  'User nickname = ' + self.users[i].nickname + '\n'
            usersAll +=  'Password = ' + self.users[i].password + '\n'
            usersAll +=  'User type = ' + self.users[i].usertype + '\n'
            usersAll +=  'Status = ' + self.users[i].status + '\n'
            usersAll +=  'Real name = ' + self.users[i].realname
            usersAll +=  '\n\n'
            i += 1
        print(usersAll)
        return usersAll

    #
    #
    #
    def remove_user(self, user):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].remove_user_from_channel(user)
            del self.users_channels_map[user.username]
        user.status = 'Offline'
        self.users.remove(user)
        print("Client: {0} has left\n".format(user.username))

    def server_shutdown(self):
        print("Shutting down chat server.\n")
        self.serverSocket.close()

def main():


    chatServer = Server()

    print("\nListening on port {0}".format(chatServer.address[1]))
    print("Waiting for connections...\n")

    chatServer.start_listening()
    chatServer.server_shutdown()

if __name__ == "__main__":
    main()

# how client works
# privete messeges
# switching channels