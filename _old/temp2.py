# if key == ord("w"):
        #     for obj in objects:
        #         if obj.id == "monster":
        #             obj.energy -= 1

        # if staging.actual_robots > 0:
            # Movimento del robot
            # if key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            #     # setta la lista degli aspetti per il movimento
            #     robot.outlook = robot_directions
            #     # aggiorna lo stato dell'oggetto
            #     robot.direction = get_direction(key)
            #     # esegue il movimento solo se consentito
            #     can_be_moved = len(robot.get_obstacles()) == 0
            #     if can_be_moved: robot.move(screen) 
            #     # reset del contatore per la sequenza idle    
            #     robot.creation_time = current_time
            #     robot.frame = INIT_FRAME         
                
            # # Sparo del proiettile
            # if key == ord('z') and actual_robot_bullets < MAX_NO_BULLETS:
            #     robot.outlook = robot_fire_directions
            #     robot.display(robot.outlook.get(robot.direction))
            #     can_be_generated, bullet = generate_robot_bullet(robot)
            #     if can_be_generated:
            #         actual_robot_bullets += 1
            #         # reset del contatore per la sequenza idle
            #         robot.creation_time = current_time
            #         robot.frame = INIT_FRAME
            #         thread = th.Thread(target=robot_bullet_thread, name=bullet.id, args=(bullet,))
            #         threads.append(thread)
            #         thread.start()

            # # Creazione dello scudo
            # if key == ord('x') and actual_shields < MAX_NO_SHIELDS:
            #     robot.outlook = robot_fire_directions
            #     robot.display(robot.outlook.get(robot.direction))
            #     if generate_shield(robot): actual_shields += 1
            #     # reset del contatore per la sequenza idle
            #     robot.creation_time = current_time
            #     robot.frame = INIT_FRAME

        # # Processa gli eventi
        # for object in objects:
        #     if current_time != object.creation_time:
        #         if   object.id == "robot":         robot_event(object, screen)
        #         elif object.id == "shield":        shield_event(object, screen)
            
        # # Aggiorna il numero di mostri
        # 

# can_be_moved = not any(monster.get_obstacles())
        # if can_be_moved:
        #     # esegue il movimento in assenza di ostacoli
        #     if random.randrange(0, 100) > MONSTER_BUL_THRESHOLD and on_target(robot, monster):
        #         # spara un proiettile se il robot è in linea sulla direzione del moto del mostro
        #         # e se è superata una soglia di probabilità
        #         can_be_generated, bullet = generate_monster_bullet(monster)
        #         if can_be_generated:
        #             thread = th.Thread(target=monster_bullet_thread, name=bullet.id, args=(bullet,))
        #             threads.append(thread)
        #             thread.start()
        #     else:
        #         # muove il mostro
        #         monster.move(act_screen)
        # else:
        #     # se si incontra un ostacolo cancella la coda del percorso
        #     monster.path = []