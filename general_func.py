from definitions import *
from objects import Object
from stage import Stage

import numpy as np
import heapq
import random
import curses
            

def generate_wall(zone_h, zone_w, zone_y, zone_x, staging: Stage):

    # definisce le dimensioni
    wall_h = random.randint(2, zone_h)
    wall_w = WALL_AREA // wall_h
    wall = Object("wall", wall_h, wall_w, 0, 0, staging.current_time)
    wall.color = 1
    
    # definisce le coordinate
    empty = False
    while not empty:
        wall.y = random.randint(zone_y, zone_y + zone_h - wall.h)
        wall.x = random.randint(zone_x, zone_x + zone_w - wall.w)
        empty = not any(staging.get_obstacles(wall))

    deploy_object(wall)  

    # setta le proprietà dell'oggetto
    wall.energy = 100
    wall.idnum = staging.idnum

    # prepara l'aspetto
    wall.outlook = [" " * wall.w] * wall.h
    
    # aggiorna lo scenario
    staging.add(wall)
    
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

def on_target(target, object):
    target_coor = np.array([target.y, target.x])
    object_coor = np.array([object.y, object.x])
    distance = np.linalg.norm(target_coor - object_coor)
    direction_array = np.array(general_directions.get(object.direction))
    on_target = abs(np.inner(target_coor - object_coor, direction_array) / distance - 1)
    return (on_target, 1000 / distance)

def deploy_object(object: Object):

    # Crea la finestra e la aggiunge come proprietà all'oggetto
    window = curses.newwin(object.h, object.w, object.y, object.x)
    window.bkgdset(curses.color_pair(object.color))
    window.noutrefresh()
    object.window = window

def deploy_random_object(staging: Stage, object: Object):

    # definisce le coordinate
    empty = False
    while not empty:
        object.y = random.randint(1, staging.height - object.h)
        object.x = random.randint(1, staging.width - 1 - object.w)
        empty = not any(staging.get_obstacles(object))

    deploy_object(object)

def dijkstra(object: Object, staging: Stage):
    # Coda con priorità per mantenere i nodi con la distanza minima in cima
    start = (object.y, object.x)
    end = (object.ty, object.tx)
    path = []
    priority_queue = [(0, start, path)]

    # Crea un set delle posizioni già controllate
    visited = set()

    # Inizia il ciclo sulla coda di lavoro
    while priority_queue:
        current_distance, current_node, current_path = heapq.heappop(priority_queue)

        # Raggiunge il bersaglio
        if current_node == end:
            
            # riposiziona l'oggetto dopo la routine dijkstra
            object.y, object.x = start[0], start[1]
            return (current_distance, current_path)
        
        # Ricade su un luogo già visitato
        if current_node in visited:
            continue
        
        # Aggiunge il nodo alla lista dei visitati (i valori doppi sono rimossi) 
        visited.add(current_node)
        
        # Esplora tutte e quattro le direzioni
        for direction in general_directions:
            dy, dx = general_directions.get(direction)
            object.y, object.x = current_node[0] + dy, current_node[1] + dx
            obstacles = staging.get_obstacles(object)
            can_be_moved = not any(obstacles)
            if can_be_moved:
                y, x = current_node[0] + dy, current_node[1] + dx
                new_node = (y, x)
                new_path = current_path + [direction]
                heapq.heappush(priority_queue, (current_distance + 1, new_node, new_path))

    # Se non è possibile raggiungere la destinazione
    
    # riposiziona l'oggetto dopo la routine dijkstra
    object.y, object.x = start[0], start[1]

    return (-1, [])

def mod_dijkstra(object: Object, staging: Stage):
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

        # Esplora tutte e quattro le direzioni
        for direction in general_directions:

            # controlal che non ci siano collisioni su un oggetto temporaneo
            dy, dx = general_directions.get(direction)
            new_y, new_x = current_node[0] + dy, current_node[1] + dx
            object_temp = Object("temp", 1, 1, new_y, new_x, staging.current_time)
            obstacles = staging.get_obstacles(object_temp)

            if not BORDER_OBSTACLE in obstacles:
                walls_collided = [obj for obj in obstacles if obj.id == "wall"]    
                if not any(walls_collided):
                    target_coor = np.array([new_y, new_x])
                    vector = target_coor - obj_coor
                    distance = np.linalg.norm(vector)
                    a, b = abs(vector[0]), abs(vector[1])
                    error = (current_distance + 1.0) ** 2 - distance ** 2 - 2 * a * b            
                    if abs(error) <= 0.001 and distance <= ROBOT_RANGE_VIEW:
                        new_node = (new_y, new_x)
                        heapq.heappush(priority_queue, (current_distance + 1.0, new_node))
        
    # Tutti i nodi sono stati visitati
    return visited



