import enum
import arcade.texture


class Direction(enum.Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class EndTypes(enum.Enum):
    START = 0
    INTERMEDIATE = 1 # this will probably be unused
    END = 2
    UNKNOWN = 3

DEBUG_INFO = False

DEVS_RECORDS = {
    "tutorial": {0: 6.761270900009549},
    "race": {0: 5.88888888763, 1:10.862115900003118}
}

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

PLAYER_TEXTURE = "./assets/alien_placeholder.png"
PLAYER_SCALE = 0.33
COYOTE_TIME = 0.12
ANIMATION_FPS = 10
TIME_TILL_TP = 0.5

TP_PARTICLE = arcade.load_spritesheet("assets/levels/tileset.png").get_texture(
    arcade.rect.LBWH(576, 448, 64, 64),
    y_up=True,
)
CHECKPOINT_PARTICLE = arcade.texture.make_soft_circle_texture(8, arcade.color.ELECTRIC_CYAN)
JUMP_PARTICLE = arcade.texture.make_circle_texture(9, arcade.color.GAINSBORO)

##############################
# Physics engine stuff below #
##############################

GRAVITY_VECTOR = (0, -3000)
DEFAULT_DAMPING = 1.0

PLAYER_MASS = 2.0
PLAYER_FRICTION = 0.4
PLAYER_DAMPING = 0.4
PLAYER_MAX_HOR_SPEED = 350
PLAYER_MAX_VERT_SPEED = 5000

PLAYER_SPEED = 4000
PLAYER_JUMP_IMPULSE = 2000

WALL_FRICTION = 0.7