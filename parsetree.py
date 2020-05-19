import re

def b2h(bytmsg):
    """takes bytearray returns hex"""
    return bytearray(bytmsg).hex()
def h2b(hexmsg):
    """takes bytearray or hex returns bytearray"""
    if(type(hexmsg)==bytearray):
        return(hexmsg)
    return(bytearray.fromhex(hexmsg))

######################
##    base class    ##
######################
class StaticBytes():
    """
    will accept any regex for match. Make sure you know what you're doing.
    """
    last_id=1
    def __init__(self,name,parent,mtch):
        StaticBytes.last_id+=1
        self.id=StaticBytes.last_id
        self.name=name
        self._parent=parent
        self._children=[]
        if(parent):
            self._root=parent._root
            parent._children+=[self]
        else:
            self._root=self
        #mtch = cleanMsg(mtch)
        self._match=re.compile(b"^"+mtch)
    def __str__(self):
        return("<{}:{}:{}>".format(
            self._root.name,
            str(type(self))[8:-2],
            self.name))
    def __repr__(self):
        return(self.__str__())
    def c(self,childName):
        """return child with given name or None if no such child"""
        for child in self._children:
            if child.name == childName:
                return(child)
        return(None)
    def _decrement(self):
        if(self._parent):
            self._parent._decrement()
    def match(self, msg, static=False):
        return(self._match.search(msg))
    def split(self,index):
        """splits this at index,
        returning the newly created begining part"""
        mtch = self._match.pattern[1:]
        new,old = mtch[:index], mtch[index:]
        newBytes = StaticBytes(
                self.name+"x",
                self._parent,
                new)
        self._parent = newBytes
        self._match = re.compile(b"^"+old)
        return(newBytes)
    def parse(self, msg, static=False, mapping=True):
        """ returns:
                (node that message matched,
                 remaining unmatched message,
                 True iff node is leaf)
        """
        # look for a matching pattern
        for child in self._children:
            cur_match = child.match(msg,static=static)
            if(cur_match):
                msg_left = msg[cur_match.end():]
                if(len(child._children)>0):
                    return(child.parse(msg_left,
                                       static=static,
                                       mapping=mapping))
                else:
                    return(child,msg_left,True)
        #no match
        if(mapping):
            #look for partial match at start of msg
            longest_match=0
            longest_child=None
            for child in self._children:
                ii=0
                child_pattern = child._match.pattern[1:]
                while ii<len(child_pattern) and ii<len(msg):
                    if(msg[ii]==child_pattern[ii]):
                        ii+=1
                        if(ii>longest_match):
                            longest_match=ii
                            longest_child=child
                    else:
                        break
            if(longest_child):
                if(len(longest_child._match.pattern)-1>longest_match):
                    new_matching_child = longest_child.split(longest_match)
                    # longest_child no longer exists!
                    # ok, it does, but it's now the child of
                    # new_matching_child
                # longest match cannot be longer than msg
                msg_left = msg[longest_match:]
                if(msg_left):
                    return(new_matching_child.parse(msg_left,
                                           static=static,
                                           mapping=mapping))
                else:
                    return(new_matching_child,msg_left,False)
            # if no partial match with any existing child
            else:
                StaticBytes(
                        "sv%d"%self.id,
                        self,
                        msg)
        return(self,msg,False)
    def create(self, msg="", static=False):
        """returns:
              hex for message that would match this node
           msg: hex to be attached to the end of hex, used for construction
           --
           warning: Does increment counters (and vars?) unless static=True
        """
        #the only time _parent should be None is in root
        return(self._parent.create(
            msg=self._match.pattern[1:]+msg,static=static))
    def send(self,msg=b""):
        if not msg:
            msg = self.create()
        self._root.send(msg)
    def recieve(self):
        return(self._root.recieve())

#####################
##    subclasses   ##
#####################
class Root(StaticBytes):
    def __init__(self,name,getsFrom,sendsTo):
        super(Root,self).__init__(name,None,b"")
        self.getsFrom=getsFrom
        self.sendsTo=sendsTo
    def create(self,msg="",static=False):
        # handle checksum
        chckr = Crc16AugCcitt()
        valid_senDmp1BYTES=bytearray.fromhex(msg)
        checkd = chckr.process(valid_senDmp1BYTES)
        final = checkd.finalhex(byteorder='little')
        # return fully created message
        return(msg+final)
    def send(self,bmsg):
        """sends to device if connected, or if not connected, silently fails"""
        if(self.sendsTo):
            self.sendsTo.write(bmsg)
    def recieve(self):
        """gets from device if connected, or if not connected, silently fails"""
        if(self.getsFrom):
            return(self.getsFrom.readline())
        else:
            return(b"")
class CountBytes(StaticBytes):
    """one byte of counting!"""
    #TODO: multiple bytes. And specific case of transition function bytes?
    def __init__(self,name,parent,init=None,friendly=True):
        self.friendly=friendly
        if(init==None) or friendly:
            init=".."
            self.uninit=True
            self.count=0
        else:
            self.uninit=False
            self.count = init%256
            init="%0.2x"%self.count
        ##TODO: Must be made to count in one byte overflow hex!
        super(cnt,self).__init__(name,parent,init)
    def _increment(self):
        if not self.uninit:
            self.count+=1
            if(self.count==256):
                self.count=0
            if not self.friendly:
                self._match=re.compile(b"^"+h2b("%0.2x" % self.count))
    def _decrement(self):
        self.count-=1
        if(self.count==-1):
            self.count=255# TODO there might be an edge case error here
                            # yup, there was. not 256, 255!
        if not self.friendly:
            self._match=re.compile(b"^"+h2b("%0.2x" % self.count))
        super(cnt,self)._decrement()
    def match(self,msg,static=False):
        if self.uninit or self.friendly:
            self.count=int(msg[:2],16)
            self.uninit=False
            if not self.friendly:
                self._match=re.compile(b"^"+h2b("%0.2x" % self.count))
        mtch = self._match.search(msg)
        if not static:
            self._increment()
        return(mtch)
    #TODO: probably hex, needs to be bytes
    def create(self, msg="", static=False):
        msg="%0.2x"%self.count + msg
        if not static:
            self._increment()
        return(self._parent.create(msg=msg,static=static))

class VariableBytes(StaticBytes):
    # matches any values??
    #TODO: add variable number of bytes to eat
    def __init__(self,name,parent,default="00"):
        self.blinkval=1
        self.blinking=False
        self._defalut=default
        super(var,self).__init__(name,parent,"")
        self._match=re.compile(b"^..")
    def create(self, msg="", static=False):
        """returns:
              hex for message that would match this node
           msg: hex to be attached to the end of hex, used for construction
           --
           warning: Does increment counters (and vars?) unless static=True
        """
        if(self._parent):
            #TODO make this return other interesting things?
            if(self.blinking):
                msg="%0.2x"%self.blinkval + msg
                self.blinkval+=1
                if(self.blinkval==128):
                    self.blinkval=1
                return(self._parent.create(
                    msg=msg,static=static))
            else:
                return(self._parent.create(
                    msg=self._defalut+msg,static=static))
        else:
            return(msg)
    def match(self, msg, static=False):
        self._defalut=msg[:2]
        return(self._match.search(msg))

