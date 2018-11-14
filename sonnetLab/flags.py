class FLAG:
    FALSE = (0).to_bytes(2,byteorder="big")
    TRUE = (1).to_bytes(2,byteorder="big")
    
class RESPONSE:
    OK = 0
    ERROR = 1

