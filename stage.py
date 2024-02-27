from definitions import *
from objects import Object
from threading import Thread
import curses
import time
import numpy as np

class Stage:

    idnum = 0
    threads = []                # lista che contiene tutti i thread 
    objects = []                # lista che contiene tutti gli oggetti
    current_time = time.time()  # indicazione del tempo
    cycle_time = 0.0            # azzera il tempo del ciclo
    running = True              # esegue il ciclo di visualizzazione
    light = set()               # lista che contiene le zone illuminate
    won = 0
    lost = 0
    round = 0

    def __init__(self, screen):
        
        # Definisci i colori
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)     # colore del muro
        curses.init_pair(2, curses.COLOR_YELLOW, COLOR_BACKGROUND_LIT)      # colore proiettili robot
        curses.init_pair(3, curses.COLOR_RED, COLOR_BACKGROUND_LIT)         # colore proiettile mostro
        curses.init_pair(4, curses.COLOR_BLACK, COLOR_BACKGROUND_LIT)    # colore del robot
        curses.init_pair(5, curses.COLOR_MAGENTA, COLOR_BACKGROUND_LIT)     # colore del mostro
        curses.init_pair(6, curses.COLOR_BLACK, COLOR_BACKGROUND_LIT)    # colore sfondo illuminato
        curses.init_pair(7, curses.COLOR_BLACK, COLOR_BACKGROUND_DARK)       # colore sfondo oscurato
        curses.init_pair(8, curses.COLOR_YELLOW, curses.COLOR_BLACK)    # colore finestra riepilogo
    
        screen.nodelay(True)  # Non bloccare le chiamate I/O
        screen.erase()
        
        # Ottieni le dimensioni dello schermo
        self.height, self.width = screen.getmaxyx()
        self.height -= 3
    
        # Prepara l'array logica e l'handle allo schermo
        self.array = np.zeros((self.height, self.width), dtype=int)
        self.screen = screen
       
    def obj_write(self, object):
        self.array[object.y : object.y + object.h, object.x : object.x + object.w] = object.idnum
    
    def obj_erase(self, object):
        self.array[object.y : object.y + object.h, object.x : object.x + object.w] = 0
    
    def obj_read(self, h, w, y, x):
        temp_array = self.array[y : y + h, x : x + w]
        return temp_array.flatten()
    
    def update_pos(self, object: Object):
        dy, dx = general_directions.get(object.direction)
        y_eff = object.y + object.h * dy if dy >= 0 else object.y + object.speed * dy
        x_eff = object.x + object.w * dx if dx >= 0 else object.x + object.speed * dx
        h_eff = object.h if dy == 0 else object.speed * abs(dy)
        w_eff = object.w if dx == 0 else object.speed * abs(dx)
        object_temp = Object("temp", h_eff, w_eff, y_eff, x_eff, self.current_time)
        obstacles = self.get_obstacles(object_temp)
        can_be_moved = not any(obstacles)
        if can_be_moved:
            # aggiorna la posizione della finestra
            object.window.mvwin(object.y + dy * object.speed, object.x + dx * object.speed)
            # aggiorna l'array logica per le collisioni
            self.obj_erase(object)
            object.y += dy * object.speed
            object.x += dx * object.speed
            self.obj_write(object)
        else:
            object.blocked = True
            object.collisions = obstacles    

    def show(self, object: Object):
        for y, line in enumerate(object.outlook):
            for x, ch in enumerate(line):
                method = object.window.addch if (y + 1, x + 1) != object.window.getmaxyx() else object.window.insch        
                method(y, x, ch)
        object.window.noutrefresh()

    def clear(self, object: Object):
        # for y, line in enumerate(object.outlook):
        #     for x, ch in enumerate(line):
        #         method = object.window.addch if (y + 1, x + 1) != object.window.getmaxyx() else object.window.insch        
        #         method(y, x, " ")
        object.window.erase()
        object.window.noutrefresh()


    def kill(self, object: Object):
        self.objects.remove(object)
        self.obj_erase(object)
        object.window.erase()
        object.window.noutrefresh()
        #self.screen.touchline(self.y, self.h)
        # self.window.touchwin()                    
        # self.window.noutrefresh()
        # del self.window

    def get_objects(self, id: str) -> Object:
        # estrae il riferiemento al robot
        objects = [obj for obj in self.objects if obj.id == id]
        return objects
    
    def add(self, object: Object):
        # aggiorna lo scenario
        self.obj_write(object)          # aggiorna l'array
        self.objects.append(object)     # aggiorna l'elenco oggetti
    
    def start(self, object: Object):
        # inserisce l'oggetto nella scena
        self.add(object)

        # crea e lancia il processo
        thread = Thread(target=object.thread, args=(object, self), name=f"{object.id} {object.idnum}", daemon=True)
        self.threads.append(thread)
        thread.start()

    def visible(self, object: Object):
        is_visible = [(y, x) in self.light for y in range(object.y, object.y + object.h) for x in range(object.x, object.x + object.w)]
        return any(is_visible)
    
    def inside_border(self, object: Object):
        condition = 0 <= object.x <= (self.width - object.w) and 0 <= object.y <= (self.height - object.h)
        return condition

    def collisions(self, object: Object):
        scan = self.obj_read(object.h, object.w, object.y, object.x)
        if np.all(scan == 0):
            collisions = []
        else:
            scan_ordered = np.flip(np.sort(scan)).tolist()
            
            # rimuovi i casi in cui collide con se stesso
            while object.idnum in scan_ordered:
                scan_ordered.remove(object.idnum)
            
            # rimuovi i casi in cui non c'è alcun oggetto
            while 0 in scan_ordered:
                scan_ordered.remove(0)

            # estrae i rifierimenti agli oggetti
            collisions = [obj for obj in self.objects if obj.idnum in scan_ordered]

        return collisions
        
    def get_obstacles(self, object: Object):
        
        is_inside_border = self.inside_border(object)
        if is_inside_border: 
            objects_collided = self.collisions(object)
        else:
            objects_collided = [-1]
        return objects_collided
