import time
import curses
import random
import heapq
import numpy as np


from robot_def import *

# Costanti
MAX_NO_BULLETS = 10
MAX_NO_SHIELDS = 6
MAX_NO_MONSTERS = 4
MAX_NO_WALLS = 5

ROBOT_RADIUS = 4
ROBOT_SPEED = 1
ROBOT_IDLE_TIME = 10
ROBOT_ENERGY = 1
ROBOT_GEN_THRESHOLD = 95

BULLET_SPEED = 4

WALL_MIN_HEIGHT = 2
WALL_MIN_WIDTH = 2
WALL_MAX_HEIGHT = 10
WALL_MAX_WIDTH = 10

INIT_FRAME = -1

MONSTER_RADIUS = 5
MONSTER_ENERGY = 1
MONSTER_GEN_THRESHOLD = 80
MONSTER_BUL_THRESHOLD = 95
MONSTER_SPEED = 1

actual_robots = 0
actual_robot_bullets = 0
actual_monsters_bullet = 0
actual_shields = 0
actual_monsters = 0

actual_idnum = 0

class Scenery:
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.array = np.zeros((height, width), dtype=int)
    
    def obj_write(self, object):
        self.array[object.y : object.y + object.h, object.x : object.x + object.w] = object.idnum
    
    def obj_erase(self, object):
        self.array[object.y : object.y + object.h, object.x : object.x + object.w] = 0
    
    def obj_read(self, y, x, h, w):
        temp_array = self.array[y : y + h, x : x + w]
        return temp_array.flatten()

class Object:
    def __init__(self, id, window):
        self.id = id
        self.idnum = 0
        self.window = window
        self.y, self.x = self.window.getbegyx()
        self.h, self.w = self.window.getmaxyx()
        self.direction = "RIGHT"
        self.frame = INIT_FRAME
        self.creation_time = current_time

    def display(self, outlook):
        for y, line in enumerate(outlook):
            for x, ch in enumerate(line):
                method = self.window.addch if (y + 1, x + 1) != self.window.getmaxyx() else self.window.insch        
                method(y, x, ch)
    
    def check_movement(self):
        dy, dx = general_directions.get(self.direction)
        y_eff = self.y + self.h * dy if dy >= 0 else self.y + self.speed * dy
        x_eff = self.x + self.w * dx if dx >= 0 else self.x + self.speed * dx
        h_eff = self.h if dy == 0 else self.speed * abs(dy)
        w_eff = self.w if dx == 0 else self.speed * abs(dx)
        
        is_inside_border = inside_border(y_eff, x_eff, h_eff, w_eff)
        if is_inside_border: 
            objects_collided = collisions(y_eff, x_eff, h_eff, w_eff)
        else:
            objects_collided = [-1]
        return objects_collided
    
    def move(self, screen):
        dy, dx = general_directions.get(self.direction)
        self.window.mvwin(self.y + dy * self.speed, self.x + dx * self.speed)
        self.display(self.outlook.get(self.direction))
        screen.touchline(self.y, self.h)
        array_screen.obj_erase(self)
        self.y += dy * self.speed
        self.x += dx * self.speed
        array_screen.obj_write(self)
        

    def kill_object(self, screen):
        objects.remove(self)
        array_screen.obj_erase(self)
        self.window.erase()
        screen.touchline(self.y, self.h)
        self.window.touchwin()                    
        self.window.noutrefresh()
        del self.window
    
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


def main(screen):
    curses.initscr()
    curses.start_color()  # Abilita il supporto ai colori
    curses.curs_set(0)    # Nascondi il cursore
    curses.cbreak()
    screen.nodelay(True)  # Non bloccare le chiamate I/O
    screen.erase()
    
    # Definisci i colori
    COLOR_BACKGROUND = curses.COLOR_CYAN
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)     # colore del muro
    curses.init_pair(2, curses.COLOR_YELLOW, COLOR_BACKGROUND)      # colore proiettili robot
    curses.init_pair(3, curses.COLOR_RED, COLOR_BACKGROUND)         # colore proiettile mostro
    curses.init_pair(4, curses.COLOR_BLACK, COLOR_BACKGROUND)       # colore del robot
    curses.init_pair(5, curses.COLOR_MAGENTA, COLOR_BACKGROUND)     # colore del mostro
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_YELLOW)    # colore sfondo illuminato
    curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)    # colore finestra riepilogo

    global temp_screen
    temp_screen = screen

    # Ottieni le dimensioni dello schermo
    global screen_height, screen_width
    screen_height, screen_width = screen.getmaxyx()
    screen_height -= 3

    global array_screen
    array_screen = Scenery(screen_height, screen_width)
    
    # Inizializza le variabili
    global objects, robot, output, current_time
    global actual_robots
    global actual_robot_bullets, actual_monsters_bullet
    global actual_shields
    global actual_monsters
    global actual_idnum

    objects = []                # lista che continene tutti gli oggetti
    current_time = time.time()  # float che indica il tempo del ciclo iniziale
    flag_override = True        # bool che bypassa la prop. di generazione dei mostri

    # Disegna lo sfondo
    screen.bkgd(curses.color_pair(4))
    screen.refresh()

    output = curses.newwin(3, screen_width, screen_height, 0)
    output.bkgd(curses.color_pair(7))
    output.border()
    output.refresh()

    for _ in range(MAX_NO_WALLS):
        wall = generate_random_wall()
        wall.window.refresh()
        objects.append(wall)
    actual_idnum += 1
    
    robot = generate_robot()
    robot.window.refresh()
    objects.append(robot)
    actual_robots += 1
   
    while True:
        current_time = time.time()
        key = screen.getch()
        # screen.erase()

        # Gestisci l'input dell'utente
        if key == ord('q'):
            break

        if actual_robots > 0:
            # Movimento del robot
            if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                # setta la lista degli aspetti per il movimento
                robot.outlook = robot_directions
                # aggiorna lo stato dell'oggetto
                robot.direction = get_direction(key)
                # esegue il movimento solo se consentito
                can_be_moved = len(robot.check_movement()) == 0
                if can_be_moved: robot.move(screen) 
                # reset del contatore per la sequenza idle    
                robot.creation_time = current_time
                robot.frame = INIT_FRAME         
                
            # Sparo del proiettile
            if key == ord('z') and actual_robot_bullets < MAX_NO_BULLETS:
                robot.outlook = robot_fire_directions
                robot.display(robot.outlook.get(robot.direction))
                if generate_robot_bullet(robot): actual_robot_bullets += 1
                # reset del contatore per la sequenza idle
                robot.creation_time = current_time
                robot.frame = INIT_FRAME

            # Creazione dello scudo
            if key == ord('x') and actual_shields < MAX_NO_SHIELDS:
                robot.outlook = robot_fire_directions
                robot.display(robot.outlook.get(robot.direction))
                if generate_shield(robot): actual_shields += 1
                # reset del contatore per la sequenza idle
                robot.creation_time = current_time
                robot.frame = INIT_FRAME

        # Processa gli eventi
        for object in objects:
            if current_time != object.creation_time:
                if   object.id == "robot":         robot_event(object, screen)
                elif object.id == "monster":       monster_event(object, screen)
                elif object.id == "robot_bullet":  bullet_robot_event(object, screen)                     
                elif object.id == "monster_bullet":bullet_monster_event(object, screen)
                elif object.id == "shield":        shield_event(object, screen)
            
        # Aggiorna il numero di mostri
        if actual_monsters < MAX_NO_MONSTERS:
            if random.randrange(0, 100) > MONSTER_GEN_THRESHOLD or flag_override:
                empty, (monster_y, monster_x) = rnd_coors(MONSTER_HEIGHT, MONSTER_WIDTH)
                if empty:
                    monster = generate_monster(monster_y, monster_x)
                    actual_monsters += 1
                    objects.append(monster)
                    array_screen.obj_write(monster)
                    flag_override = False
                else:
                    flag_override = True
   
        # Genera un nuovo robot
        if actual_robots < 1:
            if random.randrange(0, 100) > ROBOT_GEN_THRESHOLD:
                robot = generate_robot()
                actual_robots += 1
                objects.append(robot)
                array_screen.obj_write(robot)


        # Disegna la scena
        screen.noutrefresh()

        for object in objects:
            object.window.touchwin()
            object.window.noutrefresh()


        cycle_time = (time.time() - current_time) * 1000
        output.addstr(1, 1, f"Cycle Time: {cycle_time:>6.2f} ms")
        output.touchwin()
        output.noutrefresh()

        curses.doupdate()
        time.sleep(0.08)
           
# eventi
        
def robot_event(robot, screen):
    global actual_robots
    keep_condition = robot.energy > 0
    if keep_condition:
        update_robot(robot)
        # visited = mod_dijkstra(robot)
        # for position in visited:
        #     temp_screen.chgat(position[0], position[1], 1, curses.color_pair(6))
        # temp_screen.refresh()
    else:
        # rimozione del robot
        robot.kill_object(screen)
        actual_robots -= 1

def shield_event(shield, screen):
    global actual_shields
    keep_condition = shield.energy > 0
    if keep_condition:
        update_shield(shield)
    else:
        # rimozione del robot
        shield.kill_object(screen)
        actual_shields -= 1


def monster_event(monster: Object, screen):
    global actual_monsters
    keep_condition = monster.energy > 0
    if keep_condition:
        update_monster(monster)
        can_be_moved = len(monster.check_movement()) == 0
        if can_be_moved:
            # esegue il movimento in assenza di ostacoli
            if random.randrange(0, 100) > MONSTER_BUL_THRESHOLD and on_target(robot, monster):
                # spara un proiettile se il robot è in linea sulla direzione del moto del mostro
                # e se è superata una soglia di probabilità
                generate_monster_bullet(monster)
            else:
                # muove il mostro
                monster.move(screen)
        else:
            # se si incontra un ostacolo cancella la coda del percorso
            monster.path = []
    else:
        # rimozione del mostro
        monster.kill_object(screen)
        actual_monsters -= 1

def bullet_robot_event(bullet: Object, screen):
    global actual_robot_bullets
    keep_condition = bullet.energy > 0
    if keep_condition:
        # esegue il movimento solo se consentito
        objects_collided = bullet.check_movement()
        can_be_moved = len(objects_collided) == 0
        if can_be_moved:
            bullet.move(screen)
        else:
            if not objects_collided[0] == -1:
                # collisione con un oggetto

                # per i proiettili è possibile che più di un oggetto venga colpito
                # perchè il proiettile si muove di una distanza molto grande
                # pertanto bisogna evitare che bypassi lo scudo
                shield_collision = [obj for obj in objects_collided if obj.id == "shield"]
                if not any(shield_collision):
                    objects_collided[0].energy -= 1
                else:
                    shield_collision[0].energy -= 1
            else:
                # collisione sul bordo
                pass
            # rimozione del proiettile
            actual_robot_bullets -= 1
            bullet.kill_object(screen)
    else:
        # rimozione del proiettile
        bullet.kill_object(screen)
        actual_robot_bullets -= 1

def bullet_monster_event(bullet, screen):
    keep_condition = bullet.energy > 0
    if keep_condition:
        # esegue il movimento solo se consentito
        objects_collided = bullet.check_movement()
        can_be_moved = len(objects_collided) == 0
        if can_be_moved:
            bullet.move(screen)
        else:
            if not objects_collided[0] == -1:
                # collisione con un oggetto

                # per i proiettili è possibile che più di un oggetto venga colpito
                # perchè il proiettile si muove di una distanza molto grande
                # pertanto bisogna evitare che bypassi lo scudo
                shield_collision = [obj for obj in objects_collided if obj.id == "shield"]
                if not any(shield_collision):
                    objects_collided[0].energy -= 1
                else:
                    shield_collision[0].energy -= 1
            else:
                # collisione sul bordo
                pass
            # rimozione del proiettile
            bullet.kill_object(screen)
    else:
        # rimozione del proiettile
        bullet.kill_object(screen)

# aggiornamento degli oggetti          

def update_robot(robot): 
    # controlla prima se il robot è fermo oltre il tempo morto
    is_idle = (current_time - robot.creation_time) > ROBOT_IDLE_TIME
    if is_idle:
        # avvia sequenza del tempo morto
        sequence = robot_greet_directions.get(robot.direction) 
        robot.frame += 1
        if robot.frame < len(sequence):
            # esecuzione della sequenza
            robot.display(sequence[robot.frame])
        else:
            # termine della sequenza
            robot.creation_time = current_time
            robot.display(robot.outlook.get(robot.direction))
            robot.frame = INIT_FRAME
    
def update_shield(shield):
    if (current_time - shield.creation_time) >= 1:
        shield.energy -= 1
        shield.frame  += 1
        shield.outlook = [SHIELD_SEQUENCE[shield.frame] * shield.w] * shield.h
        shield.display(shield.outlook)
        shield.creation_time = current_time
        
def update_monster(monster: Object):
        if len(monster.path) > 0:
            monster.direction = monster.path.pop(0)
        else:
            # salva le coordinate iniziali
            y, x = monster.y, monster.x
            empty, (monster.ty, monster.tx) = rnd_coors(monster.h, monster.w)
            if not empty:
                return
            else:
                start_time = time.time()
                shortest_distance, shortest_path = dijkstra(monster)
                if shortest_distance > 0:
                    dijkstra_time = (time.time() - start_time) * 1000
                    output.addstr(1, 30, f"Dijkstra Time: {dijkstra_time:>6.2f} ms")
                    monster.path = shortest_path
                    monster.direction = monster.path.pop(0)
                # riposiziona l'oggetto dopo la routine dijkstra
                # e imposta la prima direzione del moto
                monster.y, monster.x = y, x
        monster.creation_time = current_time
        
# funzioni varie

def get_color(y, x, color1, color2):
    color_pair = color1 if (x + y) % 2 == 0 else color2
    return color_pair

def get_direction(key):
    directions_mapping = {
        curses.KEY_UP: "UP",
        curses.KEY_DOWN: "DOWN",
        curses.KEY_LEFT: "LEFT",
        curses.KEY_RIGHT: "RIGHT"
    }
    return directions_mapping.get(key, "RIGHT")    
            
# funzioni di collisione
def on_target(target, object):
    target_coor = np.array([target.y, target.x])
    object_coor = np.array([object.y, object.x])
    distance = np.linalg.norm(target_coor - object_coor)
    direction_array = np.array(general_directions.get(object.direction))
    on_target = abs(np.inner(target_coor - object_coor, direction_array) / distance - 1) < 0.01
    return on_target


def inside_border(y, x, h, w):
    condition = 0 <= x <= (screen_width - w) and 0 <= y <= (screen_height - h)
    return condition

def collisions(y, x, h, w):
    scan = array_screen.obj_read(y, x, h, w)
    if np.all(scan == 0):
        collisions = []
    else:
        scan_ordered = np.flip(np.sort(scan))
        collisions = [obj for obj in objects if obj.idnum in scan_ordered.tolist()]
    return collisions

# generazione degli oggetti

def generate_random_wall():
    global actual_idnum

    # definisce le coordinate
    wall_height, wall_width = random.randint(WALL_MIN_HEIGHT, WALL_MAX_HEIGHT), random.randint(WALL_MIN_HEIGHT, WALL_MAX_WIDTH)
    while True:
        wall_x = random.randint(1, screen_width - 1 - wall_width)
        wall_y = random.randint(1, screen_height - wall_height)
        empty, (wall_y, wall_x) = rnd_coors(wall_height, wall_width)
        if empty:
            break

    # crea la finestra associata all'oggetto e l'oggetto
    wall_window = curses.newwin(wall_height, wall_width, wall_y, wall_x)
    wall_window.bkgd(curses.color_pair(1))
    wall = Object("wall", wall_window)
    # setta le proprietà dell'oggetto
    wall.energy = 100
    wall.idnum = 1
    # aggiorna all'array delle collisioni
    actual_idnum = 1
    array_screen.obj_write(wall)
    return wall

def generate_robot():
    global actual_idnum

    # definisce le coordinate
    while True:
        empty, (robot_y, robot_x) = rnd_coors(ROBOT_HEIGHT, ROBOT_WIDTH)
        if empty:
            break

    # Crea la finestra e poi l'oggetto e infine chiama il metodo per assegnare la figura
    robot_window = curses.newwin(ROBOT_HEIGHT, ROBOT_WIDTH, robot_y, robot_x)
    robot_window.bkgdset(curses.color_pair(4))
    robot = Object("robot", robot_window)
    # setta le proprietà dell'oggetto
    robot.speed = ROBOT_SPEED
    robot.radius = ROBOT_RADIUS
    robot.energy = ROBOT_ENERGY
    robot.idnum = actual_idnum
    # offset rispetto alle coordinate della finestra
    robot.osy = 1 
    robot.osx = 2 
    # prepara l'aspetto
    # assume inizialemente la configurazione DESTRA
    robot.outlook = robot_directions
    robot.display(robot.outlook.get("RIGHT"))
    # aggiorna all'array delle collisioni
    actual_idnum += 1
    array_screen.obj_write(robot)
    return robot

def generate_monster(monster_y, monster_x):
    global actual_idnum
    # Crea la finestra e poi l'oggetto e infine chiama il metodo per assegnare la figura
    monster_window = curses.newwin(MONSTER_HEIGHT, MONSTER_WIDTH, monster_y, monster_x)
    monster_window.bkgdset(curses.color_pair(5) | curses.A_BOLD)
    monster = Object("monster", monster_window)
    # setta le proprietà dell'oggetto
    monster.speed = MONSTER_SPEED
    monster.radius = MONSTER_RADIUS
    monster.energy = MONSTER_ENERGY
    monster.idnum = actual_idnum
    # offset rispetto alle coordinate della finestra
    monster.osy = 2 
    monster.osx = 2 
    # prepara l'aspetto
    # assume inizialemente la configurazione DESTRA
    monster.outlook = monster_directions
    monster.display(monster.outlook.get("RIGHT"))
    # Inizializza la lista con il percorso dei movimenti del monster
    monster.path = []
    # aggiorna all'array delle collisioni
    actual_idnum += 1
    array_screen.obj_write(monster)
    return monster

def generate_robot_bullet(source):
    global actual_idnum
    # prepara le coordinate di posizionamento
    bullet_y, bullet_x = source.bullet_deployment()

    # prepara le dimensioni del proiettile
    bullet_outlook = robot_bullet_directions.get(source.direction)
    bullet_height, bullet_width = len(bullet_outlook), len(bullet_outlook[0]) 

    # controlla che possa essere generato
    is_inside = inside_border(bullet_y, bullet_x, bullet_height, bullet_width) 
    objects_collided = collisions(bullet_y, bullet_x, bullet_height, bullet_width)
    can_be_generated = is_inside and len(objects_collided) == 0
    if can_be_generated:
        # Crea la finestra e poi l'oggetto e infine chiama il metodo per assegnare la figura
        bullet_window = curses.newwin(bullet_height, bullet_width, bullet_y, bullet_x)
        bullet_window.bkgdset(curses.color_pair(2))
        bullet = Object("robot_bullet", bullet_window)
        # setta le proprietà dell'oggetto
        bullet.direction = source.direction
        bullet.speed = BULLET_SPEED
        bullet.energy = 1
        bullet.idnum = actual_idnum
        # offset rispetto alle coordinate della finestra
        #bullet.osy = bullet_osy
        #bullet.osx = bullet_osx
        # prepara l'aspetto
        bullet.outlook = robot_bullet_directions
        bullet.display(bullet_outlook)
        objects.append(bullet)
        # aggiorna all'array delle collisioni
        actual_idnum += 1
        array_screen.obj_write(bullet)
    else:
        if is_inside: objects_collided[0].energy -= 1
    return can_be_generated

def generate_monster_bullet(source):
    global actual_idnum
    # prepara le coordinate di posizionamento
    bullet_y, bullet_x = source.bullet_deployment()

    # prepara le dimensioni del proiettile
    bullet_outlook = monster_bullet_directions.get(source.direction)
    bullet_height, bullet_width = len(bullet_outlook), len(bullet_outlook[0]) 

    # controlla che possa essere generato
    is_inside = inside_border(bullet_y, bullet_x, bullet_height, bullet_width) 
    objects_collided = collisions(bullet_y, bullet_x, bullet_height, bullet_width)
    can_be_generated = is_inside and len(objects_collided) == 0
    if can_be_generated:
        # Crea la finestra e poi l'oggetto e infine chiama il metodo per assegnare la figura
        bullet_window = curses.newwin(bullet_height, bullet_width, bullet_y, bullet_x)
        bullet_window.bkgdset(curses.color_pair(3))
        bullet = Object("monster_bullet", bullet_window)
        # setta le proprietà dell'oggetto
        bullet.direction = source.direction
        bullet.speed = BULLET_SPEED
        bullet.energy = 1
        bullet.idnum = actual_idnum
        # offset rispetto alle coordinate della finestra
        #bullet.osy = bullet_osy
        #bullet.osx = bullet_osx
        # prepara l'aspetto
        bullet.outlook = monster_bullet_directions
        bullet.display(bullet_outlook)
        objects.append(bullet)
        # aggiorna all'array delle collisioni
        actual_idnum += 1
        array_screen.obj_write(bullet)
    else:
        if is_inside: objects_collided[0].energy -= 1

def generate_shield(source):
    global actual_idnum
    # prepara le dimensioni dello scudo
    shield_height, shield_width = shield_directions.get(source.direction)
    # prepara le coordinate di posizionamento
    shield_y, shield_x = source.shield_deployment()
    # controlla che possa essere generato
    is_inside = inside_border(shield_y, shield_x, shield_height, shield_width) 
    objects_collided = collisions(shield_y, shield_x, shield_height, shield_width)
    can_be_generated = is_inside and len(objects_collided) == 0
    if can_be_generated:
        # Crea la finestra e poi l'oggetto e infine chiama il metodo per assegnare la figura
        shield_window = curses.newwin(shield_height, shield_width, shield_y, shield_x)
        shield_window.bkgdset(curses.color_pair(2))
        shield = Object("shield", shield_window)
        # setta le proprietà dell'oggetto
        shield.direction = source.direction
        shield.energy = len(SHIELD_SEQUENCE)
        shield.idnum = actual_idnum
        # offset rispetto alle coordinate della finestra
        pass
        # prepara l'aspetto
        shield.outlook = [SHIELD_SEQUENCE[0] * shield_width] * shield_height
        shield.display(shield.outlook)
        objects.append(shield)
        # aggiorna all'array delle collisioni
        actual_idnum += 1
        array_screen.obj_write(shield)
    return can_be_generated


# funzioni basate sulla geometria

def rnd_coors(object_height, object_width):
    # Calcola le coordinate dell'oggetto in un punto a caso
    y = random.randint(1, screen_height - object_height)
    x = random.randint(1, screen_width - 1 - object_width)

    # Controlla che non sia sovrapposto a qualcosa di già disegnato
    objects_collided = collisions(y, x, object_height, object_width)
    empty = len(objects_collided) == 0

    return empty, (y, x)

def offset_coors(object: Object):
    # Calcola le coordinate dell'oggetto in un punto a caso
    y = object.y
    x = object.x + 10
    # Crea una finestra temporanea
    win_temp = curses.newwin(object.h, object.w, y, x)
    obj_temp = Object("temp", win_temp)
    # Controlla che non sia sovrapposto a qualcosa di già disegnato
    is_inside = inside_border(y, x, object.h, object.w) 
    objects_collided = collisions(y, x, object.h, object.w)
    empty = is_inside and len(objects_collided) == 0
    del win_temp
    return empty, (y, x)


def dijkstra(object: Object):
    # Coda con priorità per mantenere i nodi con la distanza minima in cima
    start = (object.y, object.x)
    end = (object.ty, object.tx)
    path = []

    # for j in range(object.h):
    #     temp_screen.addstr(object.y + j, object.x, "§" * object.w)
    # temp_screen.refresh()

    # for j in range(object.h):
    #     temp_screen.addstr(object.ty + j, object.tx, "@" * object.w)
    # temp_screen.refresh()

    priority_queue = [(0, start, path)]
    # Crea un set delle posizioni già controllate
    visited = set()
    # Inizia il ciclo sulla coda di lavoro
    while priority_queue:
        current_distance, current_node, current_path = heapq.heappop(priority_queue)
        # Raggiunge il bersaglio
        if current_node == end:
            return (current_distance, current_path)
        # Ricade su un luogo già visitato
        if current_node in visited:
            continue
        # Aggiunge il nodo alla lista dei visitati (i valori doppi sono rimossi) 
        visited.add(current_node)
        # Esplora tutte e quattro le direzioni
        for direction in general_directions:
            dy, dx = general_directions.get(direction)
            dy, dx = general_directions.get(direction)
            new_y, new_x = current_node[0] + dy, current_node[1] + dx
            is_inside = inside_border(new_y, new_x, 1, 1) 
            objects_collided = [obj for obj in collisions(new_y, new_x, 1, 1) if obj.idnum != object.idnum]
            can_be_moved = is_inside and not any(objects_collided)
            if can_be_moved:
                y, x = current_node[0] + dy, current_node[1] + dx
                new_node = (y, x)
                new_path = current_path + [direction]
                heapq.heappush(priority_queue, (current_distance + 1, new_node, new_path))
    # Se non è possibile raggiungere la destinazione
    return (-1, [])

def mod_dijkstra(object: Object):
    # Coda con priorità per mantenere i nodi con la distanza minima in cima
    start = (object.y + object.osy, object.x + object.osx)
    obj_coor = np.array([start[0], start[1]])
    priority_queue = [(0, start)]
    # Crea un set delle posizioni già controllate
    visited = set()
    
    # Inizia il ciclo sulla coda di lavoro
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        # Ricade su un luogo già visitato
        if current_node in visited:
            continue
        # Aggiunge il nodo alla lista dei visitati (i valori doppi sono rimossi) 
        visited.add(current_node)
        # temp_screen.addstr(current_node[0], current_node[1], "§")
        # temp_screen.refresh()
        # # Esplora tutte e quattro le direzioni
        for direction in general_directions:
            dy, dx = general_directions.get(direction)
            new_y, new_x = current_node[0] + dy, current_node[1] + dx
            is_inside = inside_border(new_y, new_x, 1, 1) 
            objects_collided = [obj for obj in collisions(new_y, new_x, 1, 1) if obj.id == "wall"]
            empty = is_inside and not any(objects_collided)
            if empty:
                target_coor = np.array([new_y, new_x])
                vector = target_coor - obj_coor
                distance = np.linalg.norm(vector)
                a, b = abs(vector[0]), abs(vector[1])
                error = (current_distance + 1) ** 2 - distance ** 2 - 2 * a * b            
                if abs(error) <= 0.001 and distance < 8:
                    new_node = (new_y, new_x)
                    heapq.heappush(priority_queue, (current_distance + 1, new_node))
# Tutti i nodi sono stati visitati
    return visited

if __name__ == '__main__':
    curses.wrapper(main)
