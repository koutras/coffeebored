
from google.appengine.ext import ndb

class ChatRoom(object):
	""" A chatroom"""

	rooms={}
	
	def __init__(self, name):
		self.name = name
		self.users =[]
		self.messages =[]
		ChatRoom.rooms[name]=self

	def addSubscriber(self, subscriber):
		self.users.append(subscriber)
		subscriber.sendMessage(self.name, "User %s has entered." %
			subscriber.username)

	def removeSubscriber(self, subscriber):
		if subscriber in self.users:
			subscriber.sendMessage(self.name,
				"User % is leaving." % subscriber.username)
		self.users.remove(subscriber)

	def addMessage(self, msg):
		self.messages.append(msg)

	def printMessages(self, out):
		print >>out, "Chat Transcript for: %s" %self.name
		for i in self.messages:
			print >> out, i

class ChatUser(object):
	"""A user participating in chats"""
	def __init__(self, username):
		self.username=username
		self.rooms = {}
	
	def subscribe(self, roomname):
		if roomname in ChatRoom.rooms:
			room = ChatRoom.rooms[roomname]
			room.addSubscriber(self)
		else:
			raise ChatError("No such room %s" % roomname)

	def sendMessage(self, roomname, text):
		if roomname in self.rooms:
			room = self.rooms[roomname]
			cm =ChatMesssage(self, text)
			room.addMessage(cm)
		else:
			raise ChatError("User %s not subscribed to chat %s" %
				(self.username, roomname))

	def displayChat(self, roomname, out):
		if roomname in self.rooms:
			room=self.rooms[roomname]
			room.printMessages(out)
		else:
			raise ChatError("User %s not subscribed to chat %s"
				(self.username, roomname))

class ChatMessage(ndb.Model):
	""" A single message sent by a user to a chatroom"""
	user = ndb.StringProperty(required=True)
	timestamp = ndb.DateTimeProperty(auto_now_add=True)
	message = ndb.TextProperty(required=True)
	"""
	def __init__(self, user, text):
		self.sender = user
		self.msg =text
		self.time = datetime.datetime.now()

	def __str_(self):
		return "From %s at %s: %s" % (self.sender.username,
												self.time,
												self.msg)
	"""
	def __str__(self):
		return "%s (%s): %s" % (self.user, self.timestamp, self.message)



def main():
	room = ChatRoom("Main")
	akis = ChatUser("akis")
	akis.subscribe("Main")
	
	marios = ChatUser("marios")
	marios.subscribe("marios")

	akis.sendMessage("Main", "hi all!")
	marios.sendMessage("Main", "hi!")
	akis.displayChat("Main", sys.stdout)

if __name__=="__main__":
	main()
