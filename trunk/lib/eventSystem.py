'''
Created on 26 dec. 2011
Copyright: Jev Kuznetsov
License: BSD

sender-reciever pattern.

'''

import tradingWithPython.lib.logger as logger
import types

class Sender(object):
    """
    Sender -> dispatches messages to interested callables 
    """
    def __init__(self):
        self.listeners = {}
        self.logger = logger.getLogger()
        
        
    def register(self,listener,events=None):
        """
        register a listener function
        
        Parameters
        -----------
        listener : external listener function
        events  : tuple or list of relevant events (default=None)
        """
        if events is not None and type(events) not in (types.TupleType,types.ListType):
            events = (events,)
             
        self.listeners[listener] = events
        
    def dispatch(self,event=None, msg=None):
        """notify listeners """
        for listener,events in self.listeners.items():
            if events is None or event is None or event in events:
                try:
                    listener(self,event,msg)
                except (Exception,):
                    self.unregister(listener)
                    errmsg = "Exception in message dispatch: Handler '{0}' unregistered for event '{1}'  ".format(listener.func_name,event)
                    self.logger.exception(errmsg)
            
    def unregister(self,listener):
        """ unregister listener function """
        del self.listeners[listener]             
                   
#---------------test functions--------------

class ExampleListener(object):
    def __init__(self,name=None):
        self.name = name
    
    def method(self,sender,event,msg=None):
        print "[{0}] got event {1} with message {2}".format(self.name,event,msg)
                   

if __name__=="__main__":
    print 'demonstrating event system'
    
    
    alice = Sender()
    bob = ExampleListener('bob')
    charlie = ExampleListener('charlie')
    dave = ExampleListener('dave')
    
    
    # add subscribers to messages from alice
    alice.register(bob.method,events='event1') # listen to 'event1'
    alice.register(charlie.method,events ='event2') # listen to 'event2'
    alice.register(dave.method) # listen to all events
    
    # dispatch some events
    alice.dispatch(event='event1')
    alice.dispatch(event='event2',msg=[1,2,3])
    alice.dispatch(msg='attention to all')
    
    print 'Done.'
    
    
    