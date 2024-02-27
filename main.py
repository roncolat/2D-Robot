from definitions import *
from map import Map
from stage import Stage
from threading import Thread
from robot_key import key_callback
from general_func import generate_wall
from hero_func import generate_robot
from monster_func import generate_monster
import random
import time
import keyboard


def main(screen):
    # Inizializza Curses
    curses.initscr()
    curses.start_color()  # Abilita il supporto ai colori
    curses.curs_set(0)    # Nascondi il cursore
    curses.cbreak()

    # Inizializza le variabili
    staging = Stage(screen)

    # Definisce la code di dati
    # staging_queue = queue.SimpleQueue()
    # staging.queue = staging_queue

    # Disegna lo sfondo
    staging.screen.bkgd(curses.color_pair(7))
    staging.screen.noutrefresh()

    output = curses.newwin(3, staging.width, staging.height, 0)
    output.bkgd(curses.color_pair(8))
    output.border()
    output.refresh()

    # attiva il thread per la finestra di output
    thread = Thread(target=output_thread, args=(output, staging,), name="output", daemon=True)
    staging.threads.append(thread)
    thread.start()

    # generazione dei muri
    staging.idnum = 1
    
    zone_h = staging.height // MAX_NO_VER_ZONES
    zone_w = staging.width // MAX_NO_HOR_ZONES
    for zone_y in range(0, staging.height - zone_h, zone_h):
            for zone_x in range(0, staging.width - zone_w, zone_w):
                # for _ in range(MAX_NO_WALLS):
                generate_wall(zone_h, zone_w, zone_y, zone_x, staging)
    
    # generazione del robot
    staging.idnum += 1
    robot = generate_robot(staging)
    
    # attiva il thread per la generazione della zona illuminata
    thread = Thread(target=FOV_thread, args=(staging,), name="FOV", daemon=True)
    staging.threads.append(thread)
    thread.start()

    # avvia la routine per la lettura da tastiera
    active_key = ["up", "down", "left", "right", "z", "x", "q"]
    for key in active_key:
        keyboard.add_hotkey(key, key_callback, args=(key, staging,), suppress=True)

    # attiva il thread per la generazione dei mostri ed eventuale rigenerazione
    # del robot
    thread = Thread(target=objects_thread, args=(staging,), name="objects", daemon=True)
    staging.threads.append(thread)
    thread.start()

    while staging.running and staging.round < MAX_ROUNDS:
        staging.current_time = time.time()
    
        # staging.screen.erase()
        # staging.screen.noutrefresh()


        if staging.light != []:
            staging.screen.erase()

            for (y, x) in staging.light:
                staging.screen.chgat(y, x, 1, curses.color_pair(6))
            staging.screen.noutrefresh()

        # aggiorna la scena ed elimina gli oggetti
        for object in staging.objects:
            if object.alive is True:
                                
                # controlla visibilità
                if staging.visible(object) or object.seen:

                    # cancella la vecchia posizione
                    object.window.bkgdset(curses.color_pair(object.color))
                    staging.clear(object)

                    # controlla se l'oggetto deve essere riposizionato
                    if object.to_move:   
                        # aggiorna la posizione
                        staging.update_pos(object)
                        object.to_move = False
                        
                    # visualizza l'oggetto
                    staging.show(object)
                    object.window.touchwin()

                    if object.id == "wall": object.seen = True

                else:

                    # cancella la vecchia posizione
                    object.window.bkgdset(curses.color_pair(7))
                    staging.clear(object)

                    # controlla se l'oggetto deve essere riposizionato
                    if object.to_move:   
                        # aggiorna la posizione
                        staging.update_pos(object)
                        object.to_move = False
                        
                    # visualizza l'oggetto
                    object.window.touchwin()

            else:
                staging.kill(object)

        
        staging.cycle_time = (time.time() - staging.current_time) * 1000
        # staging_queue.put_nowait(staging)
        
        output.touchwin()
        output.noutrefresh()

        curses.doupdate()
        time.sleep(0.08)

def output_thread(window, staging: Stage):
    while True:
        output_str = f"Cycle Time: {staging.cycle_time:_>6.2f} ms"
        window.addstr(1, 1, output_str)
        output_str = f"Round # {staging.round}"
        window.addstr(1, 30, output_str)
        output_str = f"Won-Lost: {staging.won}-{staging.lost}"
        window.addstr(1, 60, output_str)
        time.sleep(0.08)

def FOV_thread(staging: Stage):
    while True:
        robots = staging.get_objects("robot")
        if any(robots):
            robot = robots[0]
            map = Map(staging.array)
            map.do_fov(robot.x + robot.osx, robot.y + robot.osy, ROBOT_RANGE_VIEW)
            staging.light = map.light

        time.sleep(0.08)

        

def objects_thread(staging: Stage):
    no_monsters_old = 0
    no_robots_old = 1
    while True:
        no_monsters      = len(staging.get_objects("monster"))
        no_robots        = len(staging.get_objects("robot"))

        # assegna i punti
        if no_monsters < no_monsters_old:
            staging.won += 1
            staging.round += 1
        
        if no_robots < no_robots_old:
            staging.lost += 1
            staging.round += 1
        
        # genera un nuovo mostro
        if no_monsters < MAX_NO_MONSTERS:
            pool = random.randrange(0, 100)
            if pool > MONSTER_GEN_THRESHOLD:
                staging.idnum += 1
                monster = generate_monster(staging)   
    
        # Genera un nuovo robot
        if no_robots < 1:
            pool = random.randrange(0, 100)
            if pool > ROBOT_GEN_THRESHOLD:
                staging.idnum += 1
                robot = generate_robot(staging)

        no_robots_old = no_robots
        no_monsters_old = no_monsters
        time.sleep(0.08)

if __name__ == '__main__':
    curses.wrapper(main)
