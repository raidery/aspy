
__all__ = ["PreCheckException", "PostCheckException"]

class PreCheckException(Exception):
    
    def __init__(self, messages):
        '''
        Constructor
        '''
        self.message = messages
    
    def __str__(self):
        return repr(self.message)


class PostCheckException(Exception):
    def __init__(self, messages):
        '''
        Constructor
        '''
        self.message = messages
    
    def __str__(self):
        return repr(self.message)
