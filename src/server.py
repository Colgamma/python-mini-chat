#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


class ServerProtocol(LineOnlyReceiver):
    factory: "Server"
    login: str = None

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason=connectionDone):
        self.factory.clients.remove(self)

    def lineReceived(self, line: bytes):
        content = line.decode(errors='ignore')

        if self.login is not None:
            content = f"Message from {self.login}: {content}"
            self.factory.save_history(content)

            for user in self.factory.clients:
                if user is not self and user.login is not None:
                    user.sendLine(content.encode())
        else:
            # login:admin -> admin
            if content.startswith("login:"):
                login = content.replace("login:", "")
                unique = True

                for user in self.factory.clients:
                    if login == user.login:
                        unique = False

                if unique:
                    self.login = login
                    self.sendLine("Welcome!".encode())
                    self.send_history()

                else:
                    self.sendLine(f"Клиент {login} занят, попробуйте другой".encode())
                    self.transport.loseConnection()
            else:
                self.sendLine("invalid login".encode())

    def send_history(self):
        for message in self.factory.messages:
            self.sendLine(message.encode())


class Server(ServerFactory):
    protocol = ServerProtocol
    clients: list
    messages: list = []

    def startFactory(self):
        self.clients = []
        print("Server started")

    def stopFactory(self):
        print("Server closed")

    def save_history(self,message):
        if len(self.messages) >= 10:
            self.messages.pop(0)
        self.messages.append(message)


reactor.listenTCP(1234, Server())
reactor.run()
