import curses

# Costanti
MAX_NO_BULLETS = 10
MAX_NO_SHIELDS = 2
MAX_NO_MONSTERS = 2
MAX_NO_WALLS = 1
MAX_NO_VER_ZONES = 4
MAX_NO_HOR_ZONES = 4
MAX_ROUNDS = 5

ROBOT_RADIUS = 4
ROBOT_SPEED = 1
ROBOT_IDLE_TIME = 10
ROBOT_ENERGY = 1
ROBOT_GEN_THRESHOLD = 95
ROBOT_RANGE_VIEW = 128


MONSTER_RADIUS = 5
MONSTER_ENERGY = 1
MONSTER_GEN_THRESHOLD = 80
MONSTER_BUL_THRESHOLD = 95
MONSTER_SPEED = 1
MONSTER_IDLE_TIME = 1

# Varie
BULLET_SPEED = 4
WALL_AREA = 20
INIT_FRAME = -1
BORDER_OBSTACLE = -1


# Colori
COLOR_BACKGROUND_LIT = curses.COLOR_CYAN
COLOR_BACKGROUND_DARK = curses.COLOR_BLUE

# Carica l'immagine del robot
ROBOT_LEFT = [
        "  Ó  ",
        " /|\\ ",
        " / \\ "
    ]

# Carica l'immagine del robot
ROBOT_RIGHT = [
        "  Ò  ",
        " /|\\ ",
        " / \\ "
    ]

ROBOT_FIRE_RIGHT = [
        "  Ò__",
        " /|  ",
        " / \\ "
    ]

ROBOT_FIRE_LEFT = [
        "__Ó  ",
        "  |\\ ",
        " / \\ "
    ]

ROBOT_GREET_LEFT_1 = [
        "\_Ò  ",
        "  |\\ ",
        " / \\ "
    ]

ROBOT_GREET_LEFT_2 = [
        "|_Ò  ",
        "  |\\ ",
        " / \\ "
    ]

ROBOT_GREET_RIGHT_1 = [
        "  Ò_/",
        " /|  ",
        " / \\ "
    ]

ROBOT_GREET_RIGHT_2 = [
        "  Ò_|",
        " /|  ",
        " / \\ "
    ]

ROBOT_HEIGHT = len(ROBOT_RIGHT)
ROBOT_WIDTH = len(ROBOT_RIGHT[0])

# Carica l'immagine del robot
MONSTER_RIGHT = [
        " / +\\ ",
        "(====)",
        " \\__/ "
    ]

MONSTER_LEFT = [
        " /+ \\ ",
        "(====)",
        " \\__/ "
    ]

MONSTER_LEFT_BUMP = [
        " /x \\ ",
        "(====)",
        " \\__/ "
    ]

MONSTER_RIGHT_BUMP = [
        " / x\\ ",
        "(====)",
        " \\__/ "
    ]

MONSTER_HEIGHT = len(MONSTER_LEFT)
MONSTER_WIDTH = len(MONSTER_LEFT[0])

robot_bullet_directions = {
           "up":  ["^", "|"],
         "down":  ["|", "v"],
        "right":  ["->"]    ,
         "left":  ["<-"]    
    }

monster_bullet_directions = {
           "up": ["O","o"],
         "down": ["o","O"],
        "right": ["oO"],
         "left": ["Oo"]
    }

shield_directions = {
           "up": [ 1, 5],
         "down": [ 1, 5],
        "right": [ 3, 1],
         "left": [ 3, 1]
    }

SHIELD_DURATION_1 = 5
SHIELD_DURATION_2 = 5
SHIELD_DURATION_3 = 5

SHIELD_SEQUENCE = ["#"] * SHIELD_DURATION_1 + ["+"] * SHIELD_DURATION_2 + ["."]*SHIELD_DURATION_3

robot_directions = {
           "up": ROBOT_LEFT,
         "down": ROBOT_RIGHT,
         "left": ROBOT_LEFT,
        "right": ROBOT_RIGHT
    }

robot_fire_directions = {
           "up": ROBOT_FIRE_LEFT,
         "down": ROBOT_FIRE_RIGHT,
         "left": ROBOT_FIRE_LEFT,
        "right": ROBOT_FIRE_RIGHT
    }

ROBOT_GREET_LEFT_SEQ = [ROBOT_FIRE_LEFT] + [ROBOT_GREET_LEFT_1, ROBOT_GREET_LEFT_2] * 3 + [ROBOT_FIRE_LEFT]
ROBOT_GREET_RIGHT_SEQ = [ROBOT_FIRE_RIGHT] + [ROBOT_GREET_RIGHT_1, ROBOT_GREET_RIGHT_2] * 3 + [ROBOT_FIRE_RIGHT]

robot_greet_directions = {
           "up": ROBOT_GREET_LEFT_SEQ ,
         "down": ROBOT_GREET_RIGHT_SEQ,
         "left": ROBOT_GREET_LEFT_SEQ ,
        "right": ROBOT_GREET_RIGHT_SEQ
    }

monster_directions = {
           "up": MONSTER_LEFT,
         "down": MONSTER_RIGHT,
         "left": MONSTER_LEFT,
        "right": MONSTER_RIGHT
    }

monster_directions_bump = {
           "up": MONSTER_LEFT_BUMP,
         "down": MONSTER_RIGHT_BUMP,
         "left": MONSTER_LEFT_BUMP,
        "right": MONSTER_RIGHT_BUMP
    }

general_directions = {
           "up": [ -1,  0],
         "down": [  1,  0],
         "left": [  0, -1],
        "right": [  0,  1]
    }

