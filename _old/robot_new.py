import time
import curses
import random
import heapq
import copy

from robot_def import *

# Costanti
BULLETS_MAX_NUMBER = 10
SHIELDS_MAX_NUMBER = 1
MONSTERS_MAX_NUMBER = 4
ROBOT_SPEED = 1
BULLET_SPEED = 4
NUMBER_WALLS = 6
WALL_MAX_HEIGHT = 5
WALL_MAX_WIDTH = 5
IDLE_TIME = 10
INIT_FRAME = -1
MONSTER_ENERGY = 1
MONSTER_RND_THRESHOLD = 8

class Scenery:
    def __init__(self, height, width):
        self.height = height
        self.width = width

class Object:
    def __init__(self, id, window, last_dir, outlook, frame, creation_time, color_odd, color_even):
        self.id = id
        self.window = window
        self.last_dir = last_dir
        self.outlook = outlook
        self.frame = frame
        self.creation_time = creation_time
        self.color_odd = color_odd
        self.color_even = color_even

    def display(self, outlook):
        y, x = self.window.getbegyx()
        odd, even = self.color_odd, self.color_even
        pair = get_color(y + i, x + j, odd, even)
        for i, line in enumerate(outlook):
            for j, ch in enumerate(line):
                self.window.addch(i, j, ch, curses.color_pair(pair) | curses.A_BOLD)


def main(screen):
    curses.initscr()
    curses.start_color()  # Abilita il supporto ai colori
    curses.curs_set(0)    # Nascondi il cursore
    curses.raw()
    curses.cbreak()
    screen.nodelay(True)  # Non bloccare le chiamate I/O
    screen.erase()
    
    # Definisci i colori
    COLOR_EVEN = curses.COLOR_BLUE
    COLOR_ODD = curses.COLOR_MAGENTA
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, COLOR_EVEN, curses.COLOR_BLACK)
    curses.init_pair(3, COLOR_ODD, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, COLOR_EVEN)
    curses.init_pair(5, curses.COLOR_BLACK, COLOR_ODD)
    curses.init_pair(6, curses.COLOR_WHITE, COLOR_EVEN)
    curses.init_pair(7, curses.COLOR_WHITE, COLOR_ODD)

    # Ottieni le dimensioni dello schermo
    height, width = screen.getmaxyx()
    scenery = Scenery(height, width)

    # Inizializza le variabili
    actual_bullets = 0
    actual_shields = 0
    actual_monsters = 0
    objects = []
    start_time = time.time()

    generate_random_walls(scenery, objects)
    draw_background(screen, scenery)
    for object in objects:
        draw_object(screen, object)
    screen.refresh()

    robot = generate_robot(screen, scenery, start_time)
    objects.append(robot)
    draw_object(screen, robot)
    screen.refresh()

    monster = generate_monster(screen, scenery, start_time)
    objects.append(monster)
    draw_object(screen, monster)
    screen.refresh()
    
    
    while True:
        current_time = time.time()
        key = screen.getch()

        # Gestisci l'input dell'utente
        if key == ord('q'):
            break

        # Movimento del robot
        if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            # movimento del robot temporaneo (il movimento è validato in update_robot)
            robot.last_dir = get_direction(key)
            robot.outlook = robot_directions.get(robot.last_dir)
            dy, dx = general_directions.get(robot.last_dir)   
            robot.y += dy
            robot.x += dx
            # controlla le collisioni con il bordo e con gli altri oggetti
            if not inside_border(scenery, robot) or any_collisions(screen, robot):
                # annulla il movimento
                robot.y -= dy
                robot.x -= dx
            # reset del contatore per la sequenza idle
            robot.creation_time = current_time
            robot.frame = INIT_FRAME
            
        # Sparo del proiettile
        if key == ord('z') and actual_bullets < BULLETS_MAX_NUMBER:
            if generate_bullet(scenery, objects, robot, current_time): actual_bullets += 1
            robot.outlook = robot_fire_directions.get(robot.last_dir)
            # reset del contatore per la sequenza idle
            robot.creation_time = current_time
            robot.frame = INIT_FRAME

        # Creazione dello scudo
        if key == ord('x') and actual_shields < SHIELDS_MAX_NUMBER:
            if generate_shield(scenery, objects, robot, current_time): actual_shields += 1
            robot.outlook = robot_fire_directions.get(robot.last_dir)
            # reset del contatore per la sequenza idle
            robot.creation_time = current_time
            robot.frame = INIT_FRAME

        # Processa gli eventi
        update_objects(screen, scenery, objects, current_time)
        actual_objects = [object.id for object in objects]
        actual_bullets = actual_objects.count("bullet")
        actual_shields = actual_objects.count("shield")
        actual_monsters = actual_objects.count("monster")
        if actual_monsters < MONSTERS_MAX_NUMBER:
            if random.randrange(0, 10) > MONSTER_RND_THRESHOLD:
                objects.append(generate_monster(screen, scenery, current_time))    
        
        # Disegna la scena
        screen.erase()
        draw_background(screen, scenery)
        for object in objects:
            draw_object(screen, object)
        screen.refresh()
        
        # Ripulisce il buffer di input da tastiera
        # curses.flushinp()
        time.sleep(0.1)

def update_objects(screen, scenery, objects, current_time):
        for object in objects:
            if object.id == "robot":
                update_robot(scenery, objects, object, current_time)
            elif object.id == "bullet":
                if not update_bullet(screen, scenery, objects, object, current_time): 
                    objects.remove(object)
            elif object.id == "shield":
                if not update_shield(object, current_time):
                    objects.remove(object)
            elif object.id == "monster":
                if not update_monster(screen, scenery, object, current_time):
                    objects.remove(object)

def update_robot(scenery, objects, robot, current_time):
    dy, dx = general_directions.get(robot.last_dir)   
    # si controlla prima se il robot è fermo oltre il tempo morto
    is_idle = (current_time - robot.creation_time) > IDLE_TIME
    if is_idle:
        # avvia sequenza del tempo morto
        sequence = robot_greet_directions.get(robot.last_dir) 
        robot.frame += 1
        if robot.frame < len(sequence):
            # esecuzione della sequenza
            robot.outlook = sequence[robot.frame]
        else:
            # termine della sequenza
            robot.creation_time = current_time
            robot.outlook = robot_directions.get(robot.last_dir)
            robot.frame = INIT_FRAME

def update_bullet(screen, scenery, objects, bullet, current_time):
    keep_condition = True
    direction = bullet.last_dir
    for i in range(BULLET_SPEED):
        if current_time != bullet.creation_time:
            dy, dx = general_directions.get(direction)
            bullet.outlook = bullet_directions.get(direction)[0]
            bullet.x += dx
            bullet.y += dy
        else:
            i += BULLET_SPEED
            
        # controlla le collisioni con il bordo e con gli altri oggetti per ogni step
       # new_collisions = any_collisions(screen, bullet)
       # if new_collisions:
       #     i = new_collisions.index(True)
       #     objects[i].creation_time -= 1
        new_condition = inside_border(scenery, bullet)
        #and not any(new_collisions)
        keep_condition = keep_condition and new_condition
    return keep_condition

def update_shield(shield, current_time):
    elapsed_time = int(current_time - shield.creation_time)
    keep_condition = elapsed_time < len(SHIELD_SEQUENCE)
    if keep_condition:
        shield.outlook = [SHIELD_SEQUENCE[elapsed_time] * shield.width] * shield.height
    return keep_condition

def update_monster(screen, scenery, monster, current_time):
    elapsed_time = int(current_time - monster.creation_time)
    keep_condition = elapsed_time < MONSTER_ENERGY
    if keep_condition:
        move_monster(screen, scenery, monster)
        monster.creation_time = current_time
    return keep_condition

def move_monster(screen, scenery, monster):
    if len(monster.path) > 0:
        direction = monster.path.pop(0)
        dy, dx = general_directions.get(direction)
        monster.y += dy
        monster.x += dx
        monster.last_dir = direction
        # controlla le collisioni con il bordo e con gli altri oggetti
        if not inside_border(scenery, monster) or any_collisions(screen, monster):
            # annulla il movimento
            monster.y -= dy
            monster.x -= dx
    else:
        target_ok = False
        while not target_ok:
            monster_temp = copy.deepcopy(monster)
            move_rnd_coors(screen, scenery, monster_temp)
            monster.target_y, monster.target_x = monster_temp.y, monster_temp.x
            shortest_distance, shortest_path = dijkstra(screen, scenery, monster)
            if shortest_distance > 0: target_ok = True
        monster.path = shortest_path

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

def draw_background(screen, scenery):
    for y in range(0, scenery.height - 1):
        for x in range(0, scenery.width):
            screen.addch(y, x, '█', curses.color_pair(get_color(y, x, 2, 3)))
            
def draw_object(screen, object):
    x, y = object.x, object.y
    color_odd = object.color_odd
    color_even = object.color_even
    for i, line in enumerate(object.outlook):
        for j, ch in enumerate(line):
            screen.addch(y + i, x + j, ch, curses.color_pair(get_color(y + i, x + j, color_odd, color_even)) | curses.A_BOLD)

def overlap_obstacle(affected, obstacle):
    affected_top = affected.y
    affected_bottom = affected.y + affected.height - 1
    affected_left = affected.x
    affected_right = affected.x + affected.width - 1

    obstacle_top = obstacle.y
    obstacle_bottom = obstacle.y + obstacle.height - 1
    obstacle_left = obstacle.x
    obstacle_right = obstacle.x + obstacle.width - 1

    return not (
        affected_top > obstacle_bottom or
        affected_bottom < obstacle_top or
        affected_left > obstacle_right or
        affected_right < obstacle_left
    )

def inside_border(scenery, object):
    condition = 0 <= object.x < (scenery.width - object.width) and 0 <= object.y < (scenery.height - object.height)
    return condition

def any_collisions(screen, object):
    direction = object.last_dir
    if   direction == "UP":
        pos = [[object.y, object.x + i] for i in range(object.width)]
    elif direction == "DOWN":
        pos = [[object.y + object.height - 1, object.x + i] for i in range(object.width)]
    elif direction == "LEFT":
        pos = [[object.y + i, object.x] for i in range(object.height)]
    elif direction == "RIGHT":
        pos = [[object.y + i, object.x + object.width - 1] for i in range(object.height)]
    # prima crea una lista con i caratteri della zona in cui andrà a posizionarsi l'oggetto
    collision = []
    for y, x in pos:
        char = screen.inch(y, x)
        char_num = char & curses.A_CHARTEXT
        char_pair_colors = char & curses.A_COLOR
        condition = not char_pair_colors in [curses.color_pair(2),curses.color_pair(3)]
        collision.append(condition)
    return any(collision)

def busy_space(screen, object):
    y, x = object.y, object.x
    is_full = []
    for i, line in enumerate(object.outlook):
        for j, ch in enumerate(line):
            char = screen.inch(y + i, x + j)
            char_num = char & curses.A_CHARTEXT
            char_pair_colors = char & curses.A_COLOR
            condition = not char_pair_colors in [curses.color_pair(2),curses.color_pair(3)]
            is_full.append(condition)
    return any(is_full)

def collisions(objects, affected):
    conditions = [
            overlap_obstacle(affected, obstacle) \
            for obstacle in objects if obstacle != affected
            ]
    return conditions

def generate_random_walls(scenery, objects):
    for _ in range(NUMBER_WALLS):
        wall_height, wall_width = random.randint(1, WALL_MAX_HEIGHT), random.randint(1, WALL_MAX_WIDTH)
        wall_x = random.randint(0, scenery.width - wall_width)
        wall_y = random.randint(0, scenery.height - wall_height)
        wall_outlook = ["█" * wall_width for _ in range(wall_height)]
        wall_temp = Object("wall", wall_y, wall_x, wall_height, wall_width, "NONE", wall_outlook, INIT_FRAME, time.time(), 1, 1)
        objects.append(wall_temp)
        curses.newwin(wall_y, wall_x, wall_height, wall_width)
        wind

def generate_robot(screen, scenery, generation_time):
    # Prende la figura del robot in configurazione DESTRA
    direction = "RIGHT"
    robot_outlook = robot_directions.get(direction)
    robot_height, robot_width = len(robot_outlook), len(robot_outlook[0])
    robot_temp = Object("robot", 0, 0, robot_height, robot_width, direction, robot_outlook, INIT_FRAME, generation_time, 4, 5)
    move_rnd_coors(screen, scenery, robot_temp)
    return robot_temp

def generate_monster(screen, scenery, generation_time):
    direction = "RIGHT"
    monster_outlook = MONSTER_ALL
    monster_height, monster_width = len(monster_outlook), len(monster_outlook[0])
    monster_temp = Object("monster", 0, 0, monster_height, monster_width, direction, monster_outlook, INIT_FRAME, generation_time, 4, 5)
    monster_temp.path = []
    move_rnd_coors(screen, scenery, monster_temp)
    return monster_temp

def move_rnd_coors(screen, scenery, object):
    empty = False
    while not empty:
        # Calcola le coordinate dell'oggetto in un punto a caso
        object.y = random.randint(0, scenery.height - object.height)
        object.x = random.randint(0, scenery.width - object.width)
        # Controlla che non sia sovrapposto a qualcosa di già disegnato
        empty = not busy_space(screen, object)

def generate_bullet(scenery, objects, source, generation_time):
    bullet_direction = source.last_dir
    bullet_outlook, dy, dx = bullet_directions.get(bullet_direction)
    bullet_y, bullet_x = source.y + 2 + dy, source.x + 2 + dx
    bullet_height, bullet_width = len(bullet_outlook), len(bullet_outlook[0])
    bullet_temp = Object("bullet", bullet_y, bullet_x, bullet_height, bullet_width, bullet_direction, bullet_outlook, INIT_FRAME, generation_time, 6, 7)
    can_be_generated = inside_border(scenery, bullet_temp)
    if can_be_generated:
        objects.append(bullet_temp)
    return can_be_generated

def generate_shield(scenery, objects, source, generation_time):
    shield_direction = source.last_dir
    shield_height, shield_width, dy, dx =  shield_directions.get(shield_direction)
    shield_outlook = [SHIELD_SEQUENCE[0] * shield_width] * shield_height
    shield_y, shield_x = source.y + dy, source.x + 2 + dx
    shield_temp = Object("shield", shield_y, shield_x, shield_height, shield_width, shield_direction, shield_outlook, INIT_FRAME, generation_time, 6, 7)
    can_be_generated = inside_border(scenery, shield_temp) and not any(collisions(objects, shield_temp))
    if can_be_generated:
        objects.append(shield_temp)
    return can_be_generated            
    
def generate_random_coors(scenery, objects, object_height, object_width):
    overlap = True
    while overlap:
        # Calcola le coordinate del monster in un punto a caso
        object_y = random.randint(0, scenery.height - object_height)
        object_x = random.randint(0, scenery.width - object_width)
        object_temp = Object("object", object_y, object_x, object_height, object_width, "", "", INIT_FRAME, 0, 4, 5)
        # Controlla che non sia sovrapposto a un muro, altrimenti ripete il ciclo
        overlap = any(collisions(objects, object_temp))
    return [object_y, object_x]

def dijkstra(screen, scenery, object):
    # Coda con priorità per mantenere i nodi con la distanza minima in cima
    start = (object.y, object.x)
    end = (object.target_y, object.target_x)
    path = []
    priority_queue = [(0, start, path)]
    # Crea un set delle posizioni già controllate
    visited = set()

    while priority_queue:
        current_distance, current_node, current_path = heapq.heappop(priority_queue)

        if current_node == end:
            object.y, object.x = start
            return (current_distance, current_path)

        if current_node in visited:
            continue

        visited.add(current_node)

        for direction in general_directions:
            dy, dx = general_directions.get(direction)
            object.y, object.x = current_node[0] + dy, current_node[1] + dx
            object.last_dir = direction 
            if inside_border(scenery, object) and not any_collisions(screen, object):
                new_node = (object.y, object.x)
                new_path = current_path.copy()
                new_path.append(direction)
                heapq.heappush(priority_queue, (current_distance + 1, new_node, new_path))

    # Se non è possibile raggiungere la destinazione
    object.y, object.x = start
    return (-1, [])

if __name__ == '__main__':
    curses.wrapper(main)
