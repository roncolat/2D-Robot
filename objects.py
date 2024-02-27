from definitions import *

class Object:
    def __init__(self, id, h, w, y, x, creation_time):
        self.id = id
        self.idnum = 0
        self.y, self.x = y, x
        self.h, self.w = h, w
        self.speed = 1
        self.direction = "right"
        self.frame = INIT_FRAME
        self.creation_time = creation_time
        self.alive = True
        self.to_move = False
        self.fired = False
        self.blocked = False
        self.collisions = []
        self.seen = False     
    
    def bullet_deployment(self):
        dy, dx = general_directions.get(self.direction)
        # prepara le coordinate per il primo posizionamento
        # (bullet_y - bullet_osy, bullet_x - bullet_osx) definiscono 
        # la posizione della punta della freccia
        object_osy =  -(1 + dy) // 2
        object_osx =  -1 if dx > 0 else 0  
        object_y = self.y + self.osy + dy * self.radius + object_osy
        object_x = self.x + self.osx + dx * self.radius + object_osx
        return (object_y, object_x)

    def shield_deployment(self):
        dy, dx = general_directions.get(self.direction)
        # prepara le coordinate per il primo posizionamento
        # (bullet_y - bullet_osy, bullet_x - bullet_osx) definiscono 
        # la posizione della punta della freccia
        object_osy =  -1 - dy if dy >= 0 else 2
        object_osx =  - dx  if dy == 0 else - dx - 2
        object_y = self.y + self.osy + dy * self.radius + object_osy
        object_x = self.x + self.osx + dx * self.radius + object_osx
        return (object_y, object_x)
