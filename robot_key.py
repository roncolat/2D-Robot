from definitions import *
from stage import Stage
from hero_func import generate_robot_bullet, generate_robot_shield
import time


def key_callback(key: str, staging: Stage):
        # estrae il riferiemento al robot
        robots = staging.get_objects("robot")
        if any(robots):
                robot = robots[0]
        else:
            return

        if key in ["up", "down", "left", "right"]:
            robot.direction = key
            robot.outlook = robot_directions.get(key)
            robot.to_move = True

        if key == "z":
            # sparo del proiettile
            robot.outlook = robot_fire_directions.get(robot.direction)
            robot.to_move = False

            # Genera un nuovo proiettile del robot
            no_robot_bullets = len(staging.get_objects("robot_bullet"))
            if no_robot_bullets < MAX_NO_BULLETS:
                    staging.idnum += 1
                    robot_bullet = generate_robot_bullet(staging)

        if key == "x":
            # generazione dello scudo
            robot.outlook = robot_fire_directions.get(robot.direction)
            robot.to_move = False

            # Genera un nuovo scudo del robot
            no_robot_shields = len(staging.get_objects("robot_shield"))
            if no_robot_shields < MAX_NO_SHIELDS:
                    staging.idnum += 1
                    robot_shield = generate_robot_shield(staging)
            
        if key == "q":
            # esce dal programma
            staging.running = False

        # reset del contatore per la sequenza idle    
        robot.creation_time = time.time()
        robot.frame = INIT_FRAME    

