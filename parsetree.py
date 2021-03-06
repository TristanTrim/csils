import re
import crccheck

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
    def _recompile(self,regex):
        self._pattern = regex
        self._match=re.compile(b"^"+re.escape(regex))
    def __init__(self,name,parent,mtch):
        StaticBytes.last_id+=1
        self.id=StaticBytes.last_id
        self._aname=name
        self._parent=parent
        self._children=[]
        self.terminations=0
        self.tags=set()
        if(parent):
            self._root=parent._root
            parent._children+=[self]
        else:
            self._root=None
        self._recompile(mtch)
    def __str__(self):
        return("<{}:{}:{}>".format(
            self._root._aname,
            str(type(self))[8:-2],
            self._aname))
    def __repr__(self):
        return(self.__str__())
    def c(self,childName):
        """return child with given name or None if no such child"""
        for child in self._children:
            if child._aname == childName:
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
        mtch = self._pattern
        new,old = mtch[:index], mtch[index:]
        newBytes = StaticBytes(
                self._aname+"a",
                None,
                new)
        index = self._parent._children.index(self)
        self._parent._children[index]=newBytes
        newBytes._parent=self._parent
        newBytes._root=self._root
        self._parent = newBytes
        newBytes._children+=[self]
        self._aname+="b"
        self._recompile(old)
        return(newBytes)
    def removeNBytes(self,n):
        pattern = self._pattern
        if(n>=len(pattern)):
            remainToRemove=n-len(pattern)
            children = []
            for child in self._children:
                children+=child.removeNBytes(remainToRemove)
            return(children)
            # does not remove self from parent because calling function will take care of that
        else:
            newPattern = pattern[n:]
            self._recompile(newPattern)
            return([self])
    def convertToVar(self):

        parent = self._parent
        leng = len(self._pattern)
        newB = VariableBytes(
                self._aname,
                None,
                leng)
        index = self._parent._children.index(self)
        for ii in range(index):
            child = parent._children[ii]
            newB._children+=child.removeNBytes(leng)
            child._parent=newB
        for child in self._children:
            newB._children+=[child]
            child._parent=newB
        for ii in range(index+1,len(parent._children)):
            child = parent._children[ii]
            newB._children+=child.removeNBytes(leng)
            child._parent=newB
        newB._parent = parent
        newB._root=self._root
        parent._children=[newB]
        del self


    def getTable(self):
        #selfword = "".join(str(x)[-2:] for x in self._match.pattern[1:])
        selfword = b2h(self._pattern)
        if(self._children):
            selfspace = " "*len(selfword)
            sub_table=[]
            for child in self._children:
                for row in child.getTable():
                    sub_table+=[[[selfspace,self]]+row]
            sub_table[0][0][0]=selfword
            return(sub_table)
        else:
            return([[[selfword,self]]])
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
                    child.terminations+=1
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
                newBytes = StaticBytes(
                                "s%d"%self.id,
                                self,
                                msg)
                newBytes.terminations+=1
                return(newBytes, b"", True)
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

def CrcChecker(msg,checksumType,isHex=False):
    checker = checksumType()
    if(isHex):
        msg=bytearray.fromhex(msg)
    checked = checker.process(msg)
    if(isHex):
        final = checkd.finalhex(byteorder='little')
    else:
        final = checked.finalbytes(byteorder='little')
    return(final)
#####################
##    subclasses   ##
#####################
class Root(StaticBytes):
    def __init__(self,name,getsFrom,sendsTo):
        super(Root,self).__init__(name,None,b"")
        self.getsFrom=getsFrom
        self.sendsTo=sendsTo
        self.checksum_leng=0
        self.checksum_type="crc"
        self.crc_checksum=crccheck.crc.Crc16AugCcitt
        self._root=self
    def create(self,msg="",static=False):
        # handle checksum
        if(self.checksum_type=="crc"):
            final = self.CrcChecker(msg,self.crc_checksum)
        # return fully created message
        return(msg+final)
    def parse(self, msg, static=False, mapping=True):
        msg=msg[:len(msg)-self.checksum_leng]+b"."*self.checksum_leng
        return(super(Root,self).parse(msg, static=static, mapping=mapping))
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
                self._recompile(h2b("%0.2x" % self.count))
    def _decrement(self):
        self.count-=1
        if(self.count==-1):
            self.count=255# TODO there might be an edge case error here
                            # yup, there was. not 256, 255!
        if not self.friendly:
            self._recompile(h2b("%0.2x" % self.count))
        super(cnt,self)._decrement()
    def match(self,msg,static=False):
        if self.uninit or self.friendly:
            self.count=int(msg[:2],16)
            self.uninit=False
            if not self.friendly:
                self._recompile(h2b("%0.2x" % self.count))
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
    def _recompile(self,match):
        self._pattern = b"."*self.length
        self._match=re.compile(b"^"+self._pattern)
    def __init__(self,name,parent,length,default="00"):
        self.length = length
        self.blinkval=1
        self.blinking=False
        self._defalut=default
        super(VariableBytes,self).__init__(name,parent,"")#this calls our recompile method
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

#class ParseTree():
#    def __init__(self,devices,logName="convoLog"):
#        if all( type(x)==Root for x in devices):
#            self.devices=devices
#        else:
#            raise Exception("All devices must be member of class parsetree.Root")
#        self.logName=logName

