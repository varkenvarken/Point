from time import sleep

class Point:
    def __init__(self, port, pwm, default="left"):
        self.port = port
        self.pwm = pwm
        self.mid = 0.0      # range [-1.0, 1.0]
        self.left = 0.0     # range [-1.0, 1.0]
        self.right = 0.0    # range [-1.0, 1.0]
        self.speed = 0.01   # step size when changing position
        self.default = default  # left, right, mid
        self.current = 0.0  # range [-1.0, 1.0]
        self.deltat = 0.02   # seconds between micro steps
    
    def mid(self):
        self.move(self.mid)
    
    def left(self):
        self.position(self.current, self.left, self.speed)
        
    def right(self):
        self.position(self.current, self.right, self.speed)
        
    def start(self):
        self.move(self.left if self.default == "left" else self.right)
        
    def position(self, start, end, speed):
        if start > end:
            speed = -speed
        for pos in range(start, end, speed):
            self.move(pos)
            self.delay()
        self.move(end)
    
    def delay(self):
        sleep(self.deltat)
    
    def move(self, position):
        p = ((position + 1.0) / 2.0 ) * 4095  # map [-1, 1] -> [0, 4095] 
        self.pwm.setServoPulse(self.port, p)
        self.current = position
        
    def getMid(self):
        return self.mid
      
    def setMid(self, pos):
        if pos < -1 or pos > 1:
            raise ArgumentError("pos not in range [-1, 1]")
        self.mid = pos
        
    def getLeft(self):
        return self.left
      
    def setLeft(self, pos):
        if pos < -1 or pos > 1:
            raise ArgumentError("pos not in range [-1, 1]")
        self.left = pos
        
    def getRight(self):
        return self.right
      
    def setRight(self, pos):
        if pos < -1 or pos > 1:
            raise ArgumentError("pos not in range [-1, 1]")
        self.right = pos
        
