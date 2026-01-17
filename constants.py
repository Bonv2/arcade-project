import enum

class Direction(enum.Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

PLAYER_TEXTURE = "./assets/alien_placeholder.png"
PLAYER_SCALE = 0.5
ANIMATION_FPS = 10

##############################
# Physics engine stuff below #
##############################

GRAVITY_VECTOR = (0, -1000)
DEFAULT_DAMPING = 1.0

PLAYER_MASS = 2.0
PLAYER_FRICTION = 0.4
PLAYER_DAMPING = 0.005
PLAYER_MAX_HOR_SPEED = 400
PLAYER_MAX_VERT_SPEED = 1000

PLAYER_SPEED = 7000
PLAYER_JUMP_IMPULSE = 1500

WALL_FRICTION = 0.7