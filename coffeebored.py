# -*- coding: utf-8 -*- 
#log: 1/4/2014 added DataRequestHandler
import cgi
from google.appengine.api import channel #channel!!!
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db #needing the two databases
import os
import jinja2 #for the templates
import webapp2 #for the sessions
from basechat import *
import sys
import facebook
import myFacebook #my Library!
import myDistance #distance between places
import json
import signal #can I use it for a periodic heartbeat?
import datetime #setting the lastHeartBeat time 
from google.appengine.api import memcache
import logging


# types of channel requests
# iu : interested_user
# rua : are you alive?
# ni : new invitation 

# check if received, after a time considered it declined
# if not received ...
# post to my wall inorder for someone to go to my coffeetable
# 28/04/2014 taken from the example 
# 14/06 implementing cleanupUsers, sendHeartBeat and onbeforeunload(see javascript)
# cleanUpUsers.... not yet done commenting out
# fix user with no friends
FACEBOOK_APP_ID = "713075282078422"
FACEBOOK_APP_SECRET = "c63b36d06fa1c4086590c3f282901f82"

import urllib2

from google.appengine.ext import db
from webapp2_extras import sessions

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='superUnguessableString!!')


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

'''
class City(db.Model):
    #represent city as a circle
    name
    radius
    latitude
    longitude 
    cafeterias
    residents
    online_residents
'''
class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    isOnline = db.BooleanProperty() #keep a flag of user is online
    facebookLocation = db.StringProperty(required=False)
    googleLongitude = db.StringProperty(required=False)
    googleLatitude = db.StringProperty(required=False)
    facebookFriends = db.StringListProperty()
    nearbyCafeterias = db.StringListProperty()
    channel_token = db.StringProperty()
    lastHeartBeat = db.DateTimeProperty()
    cityLat = db.StringProperty()
    cityLong = db.StringProperty()
    appengineCity = db.StringProperty()
    hasSentHb = db.BooleanProperty()

class CoffeeTable(db.Model):
    host_user = db.StringProperty(required=True)
    sitted_users = db.StringListProperty()

class FbFriend(db.Model):
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

class Cafeteria(db.Model):
    id = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    street = db.StringProperty(required=False)
    fbLongitude = db.StringProperty(required=False)
    fbLatitude = db.StringProperty(required=False)

class Invitation(db.Model):
    sender_name = db.StringProperty(required=True)
    sender_id = db.StringProperty()
    receiver_id = db.StringProperty()
    place = db.StringProperty()
    startTime = db.IntegerProperty()
    endTime = db.IntegerProperty()
    accepted = db.BooleanProperty()
    received = db.BooleanProperty()
    


class BaseHandler(webapp2.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
     # session->cookie->create_user->set cookie -> create session
    @property
    def current_user(self):
        if self.session.get("user"):
            # hack to add the google latitude, longitude, in case
            # they are defined
            db_user=User.get_by_key_name(self.session.get('user')['id'])
            if db_user is not None:
                if self.session["user"]["channel_token"]=="":
                    self.session["user"]["channel_token"]=db_user.channel_token 
                    logging.info("channel token renewed form db")
                               
                if db_user.googleLongitude!=None:
                    self.session['user']['googleLongitude']=db_user.googleLongitude
                    self.session['user']['googleLatitude']=db_user.googleLatitude
            # User is logged in
            logging.info('in current_user user has a session')
            return self.session.get("user")
        else:
            # Either used just logged in or just saw the first page
            # We'll see here
            
            cookie = facebook.get_user_from_cookie(self.request.cookies,
                                                   FACEBOOK_APP_ID,
                                                   FACEBOOK_APP_SECRET)

            logging.info('in current_user user hasnt got a session')
            if cookie:
                logging.info('in current_user user has a cookie')
                # Okay so user logged in.
                # Now, check to see if existing user
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    logging.info('in current_user user hasnt got a db entry ')
                    # Not an existing user so get user info
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    #create the channel to the client here
                    channel_token = channel.create_channel(str(profile["id"]))
                    user = User(
                        key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        access_token=cookie["access_token"],
                                isOnline=True,
                        facebookFriends=[],
                        nearbyCafeterias=[],
                        channel_token=channel_token,
                        hasSentHb = False,
                    )
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                # User is now logged in
                # when a user is logged in, also do a cleanup of users who have not 
                user.isOnline=True
                user.lastHeartBeat= datetime.datetime.now() 
                user.put()
                #self.cleanupUsers() #change state to offline for inactive users 
                # closed the application properly
                logging.info('in current user, rewriting session')
                facebookLocation=user.facebookLocation
                #if geolocation not issued, draw location by facebook
                if user.googleLatitude!=None or  user.googleLatitude!="":
                    if facebookLocation==None or facebookLocation=="":
                        facebookLocation=self.getFacebookLocation(cookie["access_token"])
                if facebookLocation!=None:
                    user.facebookLocation=facebookLocation
                #must refresh channel_token, because a new session will be created
                channel_token =  channel.create_channel(str(user.id))
                self.session["user"] = dict(
                    name=user.name,
                    profile_url=user.profile_url,
                    id=user.id,
                    access_token=user.access_token,
                    facebookLocation=user.facebookLocation,                      
                    channel_token=channel_token
                )
                user.channel_token=channel_token
                logging.info('session of new user');
                logging.info(self.session.get("user"))
                user.put()
                return self.session.get("user")
        return None
    @property
    def current_location(self):
        # get location from headers, appengine supports that
        location={'cityLat' : '', 'cityLong': '','appengineCity': '', 
             'googleLatitude':'','googleLongitude':'',
             'facebookLocation':'','stigma':'','lat':'','long':''}
        if self.current_user is not None:
            user = User.get_by_key_name(self.current_user['id'])
            if user is not None:
                if user.googleLatitude is not None and user.googleLatitude!='':
                    logging.info('current_location google location found')
                    location['googleLatitude']=user.googleLatitude
                    location['googleLongitude']=user.googleLongitude
                if user.cityLat:
                    logging.info('current location appengine location found')
                    location['cityLat']=user.cityLat
                    location['cityLong']=user.cityLong
                    location['appengineCity']=user.appengineCity
                    return location
                if user.facebookLocation is not None:
                    # get location user has set in facebook
                    location['facebookLocation']=user.facebookLocation

                else:
                    user.facebookLocation = ""
            user.put()
            if location['googleLatitude'] is not '':
                (lat,long)=(location['googleLatitude'], location['googleLongitude']) 
            elif location['cityLat'] is not '':
                (lat,long)=(location['cityLat'], location['cityLong']) 
            else:
                (lat,long)=('','') 
            location['stigma']=(lat,long)
            location['lat']=lat
            location['long']=long
            
            logging.info(location)
            #logging.info('in current location stigma: '  +location['stigma'])
            return location 
        return None
    

        
   
   
    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        """

        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        return self.session_store.get_session()
    def getFacebookLocation(self,token):
        try:
            ans=myFacebook.fql("me?fields=location",token)
        except:
            logging.info('connection error when querying fb location')
            self.session['user'] = None
            self.redirect('/')
             
        logging.info(ans)
         
        """ 
        cookie = facebook.get_user_from_cookie(self.request.cookies,
                                                   FACEBOOK_APP_ID,
                                                   FACEBOOK_APP_SECRET)
        """
        logging.info('ans is:')
        logging.info(ans)
        if ans==None or ans=="":
            location=None
        else:
            try:
                location = ans['location']['name']
            except: #sb might have not set location
                location=""
        if location==None:
            location=""
        logging.info(location)
        return location

class testChannelHandler(BaseHandler):
    def get(self):
         channel.send_message('100003945170954','shit')

#implement functionality for many users to go for coffee
class CoffeeTableHandler(BaseHandler):
    def get(self):
        if self.request.get("action")=='join':
           table_id=self.request.get("table_id")      
           coffeeTable=CoffeeTable.get_by_key_name(table_id)
           if coffeetable is not Null:
            interested_user=self.request.get("interested_user")
            coffeeTable.sitted_users+=interested_user
            coffeeTable.put()
            data = {'interested_user': interested_user,
            }
            jsonData.json.dumps(data)
            channel.send_message(coffeeTable.host_user,jsonData)
            
        if self.request.get("action")=='create':
            host_user= CoffeeTable
        

class notifyPresenceHandler(BaseHandler):
    def get(self):
        self.response.headers["Content-Type"]="text/html"
        self.response.out.write(
        '''<form action="/notifyPresence" method="post">
          <input type="submit" value="Post it!">
        </form>''')
    def post(self):
        user = self.current_user
        logging.info("posting on facebook!!!")
        graph = facebook.GraphAPI(self.current_user['access_token'])
        #graph.put_object("me", "feed", message="min kanete like! its a test!")
        self.redirect('/')

        
       
        
class nearbyCafeteriasHandler(BaseHandler):
    def get(self):
        # if user has somehow changed location then he must be far for his favorite cafeterias
        location = self.current_location
        if self.current_user is None:
            return 
        user_id = self.current_user['id']
        user =User.get_by_key_name(user_id)
        if user is None:
            return
        elif not(user.googleLatitude or user.cityLat):
            return 
        user_stigma= self.current_location['stigma']
        lat = self.current_location['lat']
        long = self.current_location['long']
        userCafeterias = user.nearbyCafeterias 
        distFromCafe = 10000
        
        #must have a better check in case the first cafeteria
        #has stored geographic location
        if (userCafeterias is not None) and userCafeterias!=[]:
            firstCafeteria=Cafeteria.get_by_key_name(userCafeterias[0])
            distFromCafe=myDistance.distance(
                (float(firstCafeteria.fbLatitude),float(firstCafeteria.fbLongitude)), (float(lat),float(long)))
        
        logging.info('distance from first cafeteria')
        logging.info(distFromCafe)
        logging.info('nearbyCafeterias session')
        logging.info(user)
        cafeterias=[]
        userCafeterias=user.nearbyCafeterias
        if userCafeterias==None or userCafeterias==[] or (distFromCafe>10000): #draw them from fb
            logging.info('user has none stored nearby cafeterias, or moved,  quering fb..')
            logging.info('user stigma')
            logging.info(user_stigma)
            graph = facebook.GraphAPI(self.current_user['access_token'])
            fqlCafeterias=myFacebook.fql("search?q=coffee&type=place&center=%s,%s&distance=1000"%user_stigma,user.access_token)
            logging.info(cafeterias)
            #store the newly acquired data of nearby cafeterias
            # into the user account
            nearbyCafeterias=[]
            logging.info('extracting cafeterias data')
            for cafeteria in fqlCafeterias['data']:
                nearbyCafeterias.append(str(cafeteria['id']))
                cafeterias.append(dict(name=cafeteria['name']))
                #check cache-> check db-> write in db
                cached_cafeteria = memcached.get(cafeteria['id'])
                if cached_cafeteria is None:
                    cafeteria_db = Cafeteria.get_by_key_name(cafeteria['id'])
                    if cafeteria_db is None:
                        cafeteria_db= Cafeteria(
                             key_name=str(cafeteria["id"]),
                             id=str(cafeteria["id"]),
                             name=cafeteria['name'],
                             street=cafeteria['location']['street'],
                             fbLongitude=str(cafeteria['location']['longitude']),
                             fbLatitude=str(cafeteria['location']['latitude'])
                        )
                        cafeteria_db.put()
            logging.info('cafeterias to save')
            logging.info(nearbyCafeterias)
            user.nearbyCafeterias=nearbyCafeterias
            user.put()
        else:
            #now use the stored ones if they are near current location
            cafeterias=[]
            for cafeteria_id in userCafeterias:
                if len(cafeterias)>10: #prevent overusing
                    break
                #try to use memached cafeteria at first
                cached_cafeteria = memcache.get(cafeteria_id)
                if cached_cafeteria is not None:
                    cafeterias.append(cached_cafeteria)
                else:
                    db_cafeteria=Cafeteria.get_by_key_name(cafeteria_id)
                    cafeterias.append(db_cafeteria)
                    memcache.add(key=db_cafeteria.id,value=db_cafeteria.name)
            logging.info('using stored nearby cafeterias')
            #logging.info(cafeterias)

        self.response.headers["Content-Type"]= "application/xml"
        self.response.headers.add_header("Access-Control-Allow-Origin","*")
        self.response.headers.add_header("Access-Control-Allow-Methods",
                                                    "GET, POST, OPTIONS")

        template = JINJA_ENVIRONMENT.get_template('./templates/general.xml')
        #logging.info(cafeterias)
        self.response.write(template.render(dict(data=cafeterias)))

#manage acceptance or no of a clients invitation
class acceptHandler(BaseHandler):
    def post(self):
        accepted= self.request.get("accepted").strip()
        invitation_key = self.request.get("invitation_key").strip()
        receiver_name = self.request.get("receiver_name").strip()
        invitation= Invitation.get_by_key_name(invitation_key)
        #user = User.get_by_key_name(invitation.receiver_id)
        logging.info('invitation in acceptHandler')
        logging.info(invitation)
        if accepted=='Yes':
            invitation.accepted=True
        else:
            invitation.accepted=False
        data = {'accepted':accepted,
                'receiver_name': receiver_name, 
                'type': 'ni'
        }
        jsonData=json.dumps(data)
        #notify initial sender of the invitation receivers
        #response
        channel.send_message(invitation.sender_id,jsonData)
        invitation.put() #update database
        self.redirect('/')
 
 
        
#this handler is called periodically from the user browser
#and the last heartbeat is saved.. Used for periodically
# logging out users of the system.. for example, if user
# has turnedoff javascript from his browser
class heartBeatHandler(BaseHandler):
    def post(self):
        receiver_id = self.request.get("receiver_id").strip()
        user = User.get_by_key_name(receiver_id)
        if user is not None:
            user.lastHeartBeat = datetime.datetime.now()
            user.put()
        self.redirect('/')

#create the invitation from a client and send it to the receiver
class invitationHandler(BaseHandler):
    def post(self):
        sender_id = self.request.get("sender_id").strip()
        sender_name = self.request.get("sender_name").strip()
        receiver_id = self.request.get("receiver_id").strip()
        receiver_name = self.request.get("receiver_name").strip()
        place = self.request.get("place").strip()
        startTime = self.request.get("startTime").strip()
        endTime = self.request.get("endTime").strip()
        #beware the key
        invitation_key = sender_id+receiver_id
        invitation = Invitation(
                key_name = invitation_key,
                sender_name=sender_name,
                sender_id=sender_id,
                receiver_id=receiver_id,
                receiver_name=receiver_name,
                place=place,
                startTime=int(startTime),
                endTime = int(endTime),
                accepted = False,
        )
        invitation.put()
        invitationData={
            'key' : invitation_key,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'receiver_id': receiver_id,
            'receiver_name' : receiver_name,
            'place': place,
            'startTime': startTime,
            'endTime': endTime,
            'accepted': 'notYet',
            'type': 'ni',
        } 
        invitationJson=json.dumps(invitationData)
        logging.info('about to send invitation to')
        phrase = '<'+str(receiver_id)+'>'
        #channel.send_message('100003945170954','shit')
        channel.send_message(receiver_id.strip(),invitationJson)
        self.redirect('/')
class myLocationHandler(BaseHandler):
        
    """ receives the post request that the modified by me,
         google snippet (Geolocation) , sends 
        the snippet is embedded in templates/base.html and it uses another snippet,
        a javascript function post to send the request to this handler here """ 
        
    def post(self):
        if self.current_user is None:
            self.redirect('/')
        try:
            (cityLat,cityLong)=self.request.get("X-AppEngine-CityLatLong") 
            appengineCity =  self.request.get("X-AppEngine-City")
        except ValueError:
            appengineCity=''
            cityLat=''
            cityLong=''
        latitude=self.request.get("latitude") or '' 
        longitude=self.request.get("longitude") or ''
        logging.info("latitude:%s longitude:%s"%(latitude,longitude))
        #get the id of the logged user, hope it works well
        user_id=self.current_user['id']
        #get user from database
        user = User.get_by_key_name(user_id)
        user.cityLat=cityLat
        user.cityLong=cityLong
        user.appengineCity=appengineCity
        user.googleLongitude=longitude
        user.googleLatitude=latitude
        token=self.current_user['access_token']
        if user.facebookLocation is None:
            try:
                ans=myFacebook.fql("me?fields=location",token)
                facebookLocation = ans['location']['name']
                user.facebookLocation= facebooklocation
            except:
                user.facebookLocation=""        
        user.put()
        #update session also
        #for some reason, the session cant' be updated so I do a hack
        #at current_user ...
        '''
        self.session['user']['googleLongitude']=longitude
        self.session['user']['googleLatitude']=latitude
        logging.info('in myLocation handler the session is')
        logging.info(self.session.get('user'))
        self.session_store.save_sessions(self.response)
        '''

        self.redirect('/')
    
class HomeHandler(BaseHandler):
    def get(self):
        template = jinja_environment.get_template('./templates/index.html')
        #messages = ndb.gql("SELECT * From ChatMessage ORDER BY timestamp desc").fetch(17)
        logging.info('current user in home handler')
        logging.info(self.current_user)
        
        logging.info('session in home handler')
        logging.info(self.session.get('user'))
        if self.current_user is not None:
            user = User.get_by_key_name(self.current_user['id']) 
            if user is not  None:
                token=user.channel_token
            else:
                token=''
        else: 
            token=''

        self.response.out.write(template.render(dict(
            facebook_app_id=FACEBOOK_APP_ID,
            current_user=self.current_user,
            channel_token=token,
        #        messages= messages
        )))
    def post(self):
        user = self.current_user
        msgtext = self.request.get("message")
        if user is None or user['name'] == "":
            nick = "No Nickname"
        else:
            nick = user['name']
        msg = ChatMessage(user=nick, message=msgtext)
        msg.put()
        sys.stderr.write("**** Just stored message: %s" % msg)
        # added message to chat, redirecting to root page,
        self.redirect('/')

        #from facebook-sdk example
        """ 
            def post(self):
                url = self.request.get('url')
                file = urllib2.urlopen(url)
                graph = facebook.GraphAPI(self.current_user['access_token'])
                response = graph.put_photo(file, "Test Image")
                photo_url = ("http://www.facebook.com/"
                            "photo.php?fbid={0}".format(response['id']))
                self.redirect(str(photo_url))
        """ 

class onlineFriendsHandler(BaseHandler):
    def get(self): 
        
        #not really needed but self.current_user
        #checks if a session exists
        theuser = self.current_user 
        if theuser==None:
            return
        user_id = self.current_user['id']
        user =User.get_by_key_name(user_id)
        if user is None:
            return
        friends = user.facebookFriends #list of ids of facebook friends for user
        logging.info('user fb friends')
        logging.info(friends)
        if friends==None or friends==[] : #draw them with a facebook request
            graph = facebook.GraphAPI(self.current_user['access_token'])
            graph = facebook.GraphAPI(user.access_token)
            profile = graph.get_object("me")
            friends = graph.get_connections("me", "friends")['data']
            fbFriends=friends # data for the template
            logging.info("onlineFriendsHandler:drawing friends with facebook query")
            logging.info(friends)
            facebookFriends=[]
            for friend in friends:
                facebookFriends.append(str(friend['id']))
                fb_friend_db = FbFriends.get_by_key_name(str(friend['id']))
                if fb_friend_db is None:
                    fb_friend = FbFriend(
                         key_name=str(friend['id']),
                         id = str(friend['id']),
                         name = friend['name'],
                    )
                    fb_friend.put()
            #insert facebook friends in user
            user.facebookFriends=facebookFriends
            user.put()
        friends = user.facebookFriends #list of ids of facebook friends for user
        onlineFriends=[]
        onlineFofs=[]
        offlineFriends=[]
        for friend_id in friends:
            cached_friend=memcache.get(friend_id)
            if cached_friend is not None:
                onlineFriends.append(cached_friend)
            else:
                fb_friend = User.get_by_key_name(friend_id)
                if fb_friend is not None:
                    if fb_friend.isOnline==True:
                        onlineFriends.append(fb_friend)
                        friendsOfFriend = fb_friend.facebookFriends 
                        fofIds=[]
                        if friendsOfFriend is not None:
                            for fof_id in friendsOfFriend:
                                cached_fof = memcache.get(fof_id)
                                if cached_fof is not None:
                                    #prevent current user in list a well as duplicates
                                    if not fofIds.__contains__(fof_id) and (fof_id!=user_id):
                                        onlineFofs.append(cached_fof)
                                else:
                                    fof = User.get_by_key_name(fof_id) 
                                    if fof is not None:
                                        if fof.isOnline==True:
                                           if not fofIds.__contains__(fof_id) and (fof_id!=user_id):
                                                onlineFofs.append(fof)
                                                fofIds.append(fof_id)
                else:
                    offlineFriends.append(fb_friend)

        #online_friends = db.GqlQuery("SELECT * From User Where name in :1",friends_list)
        # online friends are not really friends, but people who are logged in
        
        #online_users = db.GqlQuery("SELECT * From User where isOnline=True")
        #current_user = self.current_user
        ''' 
        for online_user in online_users:  
            onlineFriends.append(online_user)
            logging.info(online_user)
        '''
        logging.info('onlineFriends')
        logging.info(onlineFriends)
        logging.info('onlineFofs')
        logging.info(onlineFofs)

        template_values = {
                'onlineFriends' : onlineFriends,
                'onlineFofs' : onlineFofs,
               # 'offlineFriends' : offlineFriends
        }
        #path = os.path.join(os.path.dirname(__file__), './templates/update.xml')
        self.response.headers["Content-Type"]= "application/xml"
        self.response.headers.add_header("Access-Control-Allow-Origin","*")
        self.response.headers.add_header("Access-Control-Allow-Methods",
                                                    "GET, POST, OPTIONS")

        template = JINJA_ENVIRONMENT.get_template('./templates/onlineFriends.xml')
        self.response.write(template.render(template_values))
 
class refreshChannel(BaseHandler):
    def post(self):
        user = User.get_by_key_name(self.current_user['id'])
        if user is not None:
            user.channel_token = channel.create_channel(str(user.id))
            user.isOnline=True
            user.put()
        self.redirect('/')
   
class LogoutHandler(BaseHandler):
    def get(self):
        user = User.get_by_key_name(self.current_user['id'])
        if user:
            logging.info("successfull logout")
            user.isOnline=False
            user.hasSentHb=False
            user.put()
        else:
            logging.info("unsuccessfull logout")

        if self.current_user is not None:
                    self.session['user'] = None
                    self.redirect('/')

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)


class DataRequestHandler(webapp2.RequestHandler):
    def get(self):
            messages = ndb.gql("SELECT * From ChatMessage ORDER BY timestamp desc").fetch(17)
            template_values = {
                'messages': messages,
                'time': messages[0].timestamp
            }
            #path = os.path.join(os.path.dirname(__file__), './templates/update.xml')
            self.response.headers["Content-Type"]= "application/xml"
            self.response.headers.add_header("Access-Control-Allow-Origin","*")
            self.response.headers.add_header("Access-Control-Allow-Methods",
                                                        "GET, POST, OPTIONS")

            template = JINJA_ENVIRONMENT.get_template('./templates/update.xml')
            self.response.write(template.render(template_values))

class ChatRoomPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            messages = ndb.gql("SELECT * From ChatMessage ORDER BY timestamp desc").fetch(17)
            template_values = {
                    'messages': messages,
                    'user': user,
             }
            self.response.headers["Content-Type"]= "text/html"
            template = JINJA_ENVIRONMENT.get_template('./templates/index.html')
            #template = JINJA_ENVIRONMENT.get_template('./templates/fb.html')
            self.response.write(template.render(template_values))
    
            """ 
            for msg in messages:
                self.response.out.write("<p>%s</p>" % msg)
            """ 
    
    def post(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        user = users.get_current_user()
        msgtext = self.request.get("message")
        if user.nickname() is None or user.nickname() == "":
            nick = "No Nickname"
        else:
            nick = user.nickname()
        msg = ChatMessage(user=user.nickname(), message=msgtext)
        msg.put()
        sys.stderr.write("**** Just stored message: %s" % msg)
        # added message to chat, redirecting to root page,
        self.redirect('/')

class cleanupUsersHandler(BaseHandler):
    #probably not the best implementation as heartbeats my not have been 
    #registered before logging users out, maybe two cronjobs must be made...
    online_people = db.GqlQuery("SELECT * From User where isOnline=True")
    #send heartbeats
    for person in online_people:
        channel.send_message(person.id, json.dumps(dict(type="rua",receiver_id=person.id)))

    for person in online_people:
        minutes_dead=myDistance.minutes_passed(datetime.datetime.now(),person.lastHeartBeat)
        if minutes_dead > 7 :
            logging.info(person.name + " offline for " + minutes_dead+ " logging him out")
            person.isOnline=False
            person.put()
            
application = webapp2.WSGIApplication([
 ('/', HomeHandler),
 #('/latest', DataRequestHandler), 
 ('/onlineFriends', onlineFriendsHandler),
 ('/notifyPresence', notifyPresenceHandler),
 ('/myLocation', myLocationHandler),
 ('/nearbyCafeterias', nearbyCafeteriasHandler),
 ('/invite', invitationHandler),
 ('/accept', acceptHandler),
 ('/refreshC', refreshChannel),
 ('/heartBeat', heartBeatHandler), # handle periodically heartbeats from clients
 ('/testChannel', testChannelHandler),
 ('/cleanupUsers', cleanupUsersHandler),
   
# ('/', ChatRoomPage),
 ('/logout', LogoutHandler),
], debug=True,
    config=config)

