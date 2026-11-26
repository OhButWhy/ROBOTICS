# SceneDescription v1: perception observation, never an actuator command.
std_msgs/Header header
uint8 version

uint8 STATUS_VALID=0
uint8 STATUS_UNKNOWN=1
uint8 status
string status_reason

uint8 LIGHT_NONE=0
uint8 LIGHT_RED=1
uint8 LIGHT_YELLOW=2
uint8 LIGHT_GREEN=3
uint8 LIGHT_UNKNOWN=255
uint8 traffic_light

uint8 SIGN_NONE=0
uint8 SIGN_LEFT=1
uint8 SIGN_RIGHT=2
uint8 SIGN_STRAIGHT=3
uint8 SIGN_UNKNOWN=255
uint8 direction_sign

float32 lane_offset_m
bool has_stop_line
float32 stop_line_distance_m
bool has_turn
float32 turn_distance_m
bool has_obstacle
float32 obstacle_distance_m
float32 confidence
string source
