from definitions import *
from objects import Object
from stage import Stage
from general_func import on_target, dijkstra, deploy_random_object, deploy_object

import time
import random

# eventi

def monster_thread(monster: Object, staging: Stage):
            
    while monster.energy > 0:

        # condizione se l'oggetto trova un ostacolo improvviso
        if monster.blocked == True:
            monster.outlook =monster_directions_bump.get(monster.direction) 
            monster.path = []
            monster.blocked = False
            monster.collisions = []

        # non esegue alcuna operazione se l'oggetto è in movimento
        if not monster.to_move and not monster.fired:

            # controlla dove si trova il robot
            robots = staging.get_objects("robot")
            if any(robots):
                robot = robots[0]
                (cos_dir, pool_th) = on_target(robot, monster)
                pool = random.randint(1, 200)

                if cos_dir < 0.005 and pool < pool_th:
                    # spara un proiettile
                    staging.idnum += 1
                    monster_bullet = generate_monster_bullet(monster, staging)
                    monster.fired = True
                    monster.creation_time = time.time()
                    continue
                    
            # esegue la sequenza se la stack di mosse è piena
            if any(monster.path):
                monster.direction = monster.path.pop(0)
                monster.outlook = monster_directions.get(monster.direction)
                monster.to_move = True
            
            # altrimenti genera un nuovo percorso
            else:
                generate_path(monster, staging)
        
        # pausa dovuta allo sparo del proiettile
        is_idle = (time.time() - monster.creation_time) > MONSTER_IDLE_TIME
        if is_idle: monster.fired = False

        # velocità di esecuzione del ciclo
        time.sleep(0.08)
    
    # rimozione del mostro
    monster.alive = False

def monster_bullet_thread(bullet: Object, staging: Stage):

    while bullet.energy > 0:

        if bullet.blocked == True:
            # aggiorna la figura del proiettile
            bullet.outlook = robot_bullet_directions.get(bullet.direction)

            # controllo delle collisioni
            if not BORDER_OBSTACLE in bullet.collisions:
                # collisione con un oggetto

                # per i proiettili è possibile che più di un oggetto venga colpito
                # perchè il proiettile si muove di una distanza molto grande
                # pertanto bisogna evitare che bypassi lo scudo
                shield_collision = [obj for obj in bullet.collisions if obj.id == "robot_shield"]
                if not any(shield_collision):
                    bullet.collisions[0].energy -= 1
                else:
                    shield_collision[0].energy -= 1
            else:
                # collisione sul bordo
                pass

            bullet.blocked = False
            bullet.collisions = []
            break

        time.sleep(0.08)
        if bullet.to_move == False: bullet.to_move = True
            
    # rimozione del proiettile
    bullet.alive = False
        
def generate_path(object: Object, staging: Stage):
    
    temp = Object("temp", object.h, object.w, object.y, object.x, staging.current_time)
    temp.idnum = object.idnum
        
    # definisce le coordinate di destinazione
    empty = False
    while not empty:
        temp.y = random.randint(1, staging.height - temp.h)
        temp.x = random.randint(1, staging.width - 1 - temp.w)
        empty = not any(staging.get_obstacles(temp))

    # inizializza la partenza e la destinazione del percorso
    temp.ty, temp.tx = temp.y, temp.x
    temp.y, temp.x = object.y, object.x
               
    # calcola il percorso più breve   
    shortest_distance, shortest_path = dijkstra(temp, staging)
    
    # se esiste un percorso salva la sequenza di monvimenti
    if shortest_distance > 0: object.path = shortest_path

def generate_monster(staging: Stage):
    
    monster = Object("monster", MONSTER_HEIGHT, MONSTER_WIDTH, 0, 0, staging.current_time)
    monster.color = 3
    
    deploy_random_object(staging, monster)  

    # setta le proprietà dell'oggetto
    monster.speed = MONSTER_SPEED
    monster.radius = MONSTER_RADIUS
    monster.energy = MONSTER_ENERGY
    monster.idnum = staging.idnum

    # offset rispetto alle coordinate della finestra
    monster.osy = 2 
    monster.osx = 2 

    # prepara l'aspetto
    monster.outlook = monster_directions.get(monster.direction)

    # Inizializza la lista con il percorso dei movimenti del monster
    monster.path = []

    # crea e lancia il processo
    monster.thread = monster_thread
    staging.start(monster)

    return monster

def generate_monster_bullet(monster: Object, staging: Stage):

    # prepara le coordinate di posizionamento
    bullet_y, bullet_x = monster.bullet_deployment()

    # prepara le dimensioni del proiettile
    bullet_outlook = monster_bullet_directions.get(monster.direction)
    bullet_height, bullet_width = len(bullet_outlook), len(bullet_outlook[0]) 

    bullet = Object("monster_bullet", bullet_height, bullet_width, bullet_y, bullet_x, staging.current_time)
    bullet.color = 2

    # controlla che possa essere generato
    obstacles = staging.get_obstacles(bullet)
    can_be_generated = not any(obstacles)

    if can_be_generated:

        deploy_object(bullet)  

        # setta le proprietà dell'oggetto
        bullet.direction = monster.direction
        bullet.speed = BULLET_SPEED
        bullet.energy = 1
        bullet.idnum = staging.idnum

        # offset rispetto alle coordinate della finestra
        #bullet.osy = bullet_osy
        #bullet.osx = bullet_osx

        # prepara l'aspetto
        bullet.outlook = monster_bullet_directions.get(bullet.direction)
        
        # crea e lancia il processo
        bullet.thread = monster_bullet_thread
        staging.start(bullet)

    else:
        # collisione con un oggetto che non sia il bordo
        if not BORDER_OBSTACLE in obstacles:
            obstacles[0].energy -= 1

    return can_be_generated, bullet



