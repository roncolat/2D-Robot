from definitions import *
from objects import Object
from stage import Stage
from general_func import deploy_object, deploy_random_object

import time     
        
def robot_thread(robot: Object, staging: Stage):

    while robot.energy > 0:
        if robot.blocked == True:
            robot.outlook = robot_fire_directions.get(robot.direction) 
            robot.blocked = False
            robot.collisions = []

        update_robot(robot)

        # if not robot.to_move and not robot.fired:
        #     visited = mod_dijkstra(robot, staging)
        #     staging.view = visited
        
        time.sleep(0.08)
            

    # rimozione del robot
    robot.alive = False

def robot_shield_thread(shield: Object, staging: Stage):
    
    while shield.energy > 0:
        update_shield(shield)
        
        # velocità di esecuzione del ciclo
        time.sleep(0.08)
    
    # rimozione del mostro
    shield.alive = False

def robot_bullet_thread(bullet: Object, staging: Stage):

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

def update_robot(robot: Object): 
    # controlla prima se il robot è fermo oltre il tempo morto
    is_idle = (time.time() - robot.creation_time) > ROBOT_IDLE_TIME
    if is_idle:
        # avvia sequenza del tempo morto
        sequence = robot_greet_directions.get(robot.direction) 
        robot.frame += 1
        if robot.frame < len(sequence):
            # esecuzione della sequenza
            robot.outlook = sequence[robot.frame]
        else:
            # termine della sequenza
            robot.creation_time = time.time()
            robot.outlook = robot_directions.get(robot.direction)
            robot.frame = INIT_FRAME
    
def update_shield(shield: Object):
    if (time.time() - shield.creation_time) >= 1:
        shield.energy -= 1
        shield.frame  += 1
        shield.outlook = [SHIELD_SEQUENCE[shield.frame] * shield.w] * shield.h
        shield.creation_time = time.time()

def generate_robot(staging: Stage):

    robot = Object("robot", ROBOT_HEIGHT, ROBOT_WIDTH, 0, 0, staging.current_time)
    robot.color = 4
    
    deploy_random_object(staging, robot)  

    # setta le proprietà dell'oggetto
    robot.speed = ROBOT_SPEED
    robot.radius = ROBOT_RADIUS
    robot.energy = ROBOT_ENERGY
    robot.idnum = staging.idnum

    # offset rispetto alle coordinate della finestra
    robot.osy = 1 
    robot.osx = 2 

    # prepara l'aspetto
    robot.outlook = robot_directions.get(robot.direction)

    # crea e lancia il processo
    robot.thread = robot_thread
    staging.start(robot)

    return robot

def generate_robot_shield(staging: Stage):
    # recupera i riferimenti al robot per la posizione iniziale
    robot = (staging.get_objects("robot"))[0]
    shield_y, shield_x = robot.shield_deployment()

    # prepara le dimensioni del proiettile
    shield_outlook = shield_directions.get(robot.direction)
    shield_height, shield_width = shield_outlook[0], shield_outlook[1]

    shield = Object("robot_shield", shield_height, shield_width, shield_y, shield_x, staging.current_time)
    shield.color = 2

    # controlla che possa essere generato
    obstacles = staging.get_obstacles(shield)
    can_be_generated = not any(obstacles)

    if can_be_generated:
        
        deploy_object(shield)  

        # setta le proprietà dell'oggetto
        shield.energy = len(SHIELD_SEQUENCE)
        shield.idnum = staging.idnum
        
        # offset rispetto alle coordinate della finestra
        pass

        # prepara l'aspetto
        shield.outlook = [SHIELD_SEQUENCE[0] * shield_width] * shield_height
        
        # crea e lancia il processo
        shield.thread = robot_shield_thread
        staging.start(shield)
    
    return shield

def generate_robot_bullet(staging: Stage):
    # recupera i riferimenti al robot per la posizione iniziale
    robot = (staging.get_objects("robot"))[0]
    bullet_y, bullet_x = robot.bullet_deployment()

    # prepara le dimensioni del proiettile
    bullet_outlook = robot_bullet_directions.get(robot.direction)
    bullet_height, bullet_width = len(bullet_outlook), len(bullet_outlook[0]) 

    bullet = Object("robot_bullet", bullet_height, bullet_width, bullet_y, bullet_x, staging.current_time)
    bullet.color = 2

    # controlla che possa essere generato
    obstacles = staging.get_obstacles(bullet)
    can_be_generated = not any(obstacles)

    if can_be_generated:
        
        deploy_object(bullet)  

        # setta le proprietà dell'oggetto
        bullet.direction = robot.direction
        bullet.speed = BULLET_SPEED
        bullet.energy = 1
        bullet.idnum = staging.idnum

        # offset rispetto alle coordinate della finestra
        #bullet.osy = bullet_osy
        #bullet.osx = bullet_osx
        
        # prepara l'aspetto
        bullet.outlook = robot_bullet_directions.get(bullet.direction)
    
        # crea e lancia il processo
        bullet.thread = robot_bullet_thread
        staging.start(bullet)

    else:
        # collisione con un oggetto che non sia il bordo
        if not BORDER_OBSTACLE in obstacles:
            obstacles[0].energy -= 1

    return bullet




