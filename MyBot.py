#!/usr/bin/env python3
# Python 3.6
# Sean Aubrey, Lanndon Rose
# January 2019

import hlt
#from hlt import constants 
#from hlt import player
from hlt import *
#from hlt.positionals import Direction
#from hlt.positionals import Position
import random
import logging

""" <<<Game Begin>>> """
game = hlt.Game()

RETURNING = 0
COLLECTING = 1
"""
# Not currently used
def find_closest_dropoff(position, game_map, player):
    closest_dropoff = None
    closest_distance = 100
    
    logging.info(player.get_dropoffs())
    for dropoff in player.get_dropoffs():
    
        distance = game_map.calculate_distance(make_position(position), dropoff.position)  
        if distance < closest_distance:
            closest_distance = distance
            closest_dropoff = dropoff
    if closest_dropoff is None:
        return me.shipyard
    return closest_dropoff
"""

def make_tuple(position):
    if type(position) == hlt.positionals.Position:
        return (position.x, position.y)
    else:
        return position

def make_position(tup):
    if type(tup) == tuple:
        return Position(tup[0], tup[1])
    else:
        return tup

def check_enemy_collision(game_map, me, position):
    if game_map[position].is_occupied:
        if not me.has_ship(game_map[position].ship.id):
            return True
    return False

def check_self_collision(ship, position, potential_move, game_map, me):
    position = make_position(position)
    for ship_id in ships:
        if ships[ship_id]["next_pos"] == position \
            and ships[ship_id]['obj'] != ship:

            # Process the unprocessed problematic ship, then decide if it's a problem.
            if ships[ship_id]['handled'] == False:

                 # Set what this ship *would* do before the problematic ship gets handled
                set_ship_move(ship, potential_move)
                handle_ship(ships[ship_id]['obj'])
                return check_self_collision(ship, position, potential_move, game_map, me)
            else:
                #logging.info("Ship #" + str(ship.id) + " would've collided with " + str(ship_id))
                return True
    return False

def navigate(ship, target, game_map, me, dog_pile_mode):
    if not has_halite_to_move(ship):
        return (0, 0)

    previous_move = ships[ship.id]['next_move']
    moves = game_map.get_unsafe_moves(ship.position, make_position(target))
    for m in moves:
        r = random.randint(0, len(moves) - 1)
        new_pos = ship.position.directional_offset(moves[r])

        logging.info(me.shipyard.position == new_pos)
        if dog_pile_mode and me.shipyard.position == new_pos:
            return moves[r]
        elif not check_enemy_collision(game_map, me, new_pos) \
            and not check_self_collision(ship, new_pos, moves[r], game_map, me):
            return moves[r]
        

    # Way forward is blocked, move sideways sometimes CAUSES COLLISIONS
    """
    flip = random.randint(0, 1)
    open = get_open_perpindiculars(ship, game_map, me, previous_move)
    if flip == 0 and len(open) > 0:
        r = random.randint(0, len(open) - 1) 
        logging.info("Ship #" + str(ship.id) + " is about to move " + str(open[r]))
        return open[r]
    """
    return (0, 0)
    
def get_open_perpindiculars(ship, game_map, me, previous_move):
    open = []
    perpindiculars = get_perpindicular_cardinals(previous_move)
    for i in range(0, 2):
        position = ship.position.directional_offset(perpindiculars[i])
        if not check_self_collision(ship, position, perpindiculars[i], game_map, me) \
            and not check_enemy_collision(game_map, me, position):
            open.append(perpindiculars[i])
    return open

def has_halite_to_move(ship):
    if ship.halite_amount >= game_map[ship.position].halite_amount * 0.1:
        return True
    return False

def get_perpindicular_cardinals(direction):
    direction = make_tuple(direction)
    if direction == Direction.North or direction == Direction.South:
        return Direction.East, Direction.West
    else:
        return Direction.North, Direction.South

"""
scan whole 16x16 sector,
find all positions above a threshhold of halite,
send ships to the closest one (add target attribute in ship dicts, each ship has unique target)
"""
def scan_for_targets(game_map, thresh):
    maxRow = game_map.height
    maxCol = game_map.width
    worthy_cells = []

    for r in range(0, maxRow):
        for c in range(0, maxCol):
            cell = game_map[Position(c, r)]
            if cell.halite_amount >= thresh:
                worthy_cells.append(cell)
    return worthy_cells

def get_nearest_worthy_target(me, game_map, ship_position, worthy_cells):
    if len(worthy_cells) <= 0:
        return (0, 0)
    # Set course target for nearest worthy cell
    nearest_cell_distance = 1000 # arbitrarily large
    nearest_cell = None
    nearest_ind = 0
    
    i = 0
    for cell in worthy_cells:
        ship_distance = game_map.calculate_distance(make_position(ship_position), cell.position)
        #base_distance = game_map.calculate_distance(make_position(game_map.), cell.position)
        if ship_distance < nearest_cell_distance:
            nearest_cell_distance = ship_distance
            nearest_cell = cell
            nearest_ind = i
        i = i + 1

    return make_tuple(nearest_cell.position), nearest_ind

def set_ship_move(ship, move):
    new_pos = ship.position.directional_offset(move)
    if move == (0, 0):
        #logging.info("No movement on ship #" + str(ship.id))
        new_pos = ship.position
    ships[ship.id]['next_pos'] = new_pos
    ships[ship.id]['next_move'] = move

def get_bigger_halite_thresh(thresh_divisor, divisor_increment):
    thresh_divisor = thresh_divisor + divisor_increment
    halite_thresh = constants.MAX_HALITE/thresh_divisor 
    return halite_thresh, thresh_divisor

def return_by_end(ship, me):
    if ship.halite_amount > 150:
        distance = game_map.calculate_distance(ship.position, me.shipyard.position)
        turns_left = constants.MAX_TURNS - turn
        if distance + 10 > turns_left:
            ships[ship.id]['status'] = RETURNING

def handle_ship(ship, dog_pile_mode=False):
    ships[ship.id]['handled'] = True

    if ship.halite_amount > 985 and ships[ship.id]['status'] == COLLECTING:
        ships[ship.id]['status'] = RETURNING
        ships[ship.id]['target'] = make_tuple(me.shipyard.position)

    if ships[ship.id]['status'] == COLLECTING and turn > constants.MAX_TURNS * .95:
        dog_pile_mode = True
        return_by_end(ship, me)

    # Returning to base or a dropoff
    if ships[ship.id]['status'] == RETURNING:
        #dropoff = find_closest_dropoff(ship.position, game_map, me)

        # Set a ship that has dropped off to collecting
        if game_map[ship.position].has_structure:
            ships[ship.id]['status'] = COLLECTING
            ships[ship.id]['target'] = None
        else:
            move = navigate(ship, me.shipyard.position, game_map, me, dog_pile_mode)
            set_ship_move(ship, move)

    # Collecting - ship should always have a target 
    if ships[ship.id]['status'] == COLLECTING:

         # If current cell is worth mining, stay
        if game_map[ship.position].halite_amount >= halite_thresh:
            set_ship_move(ship, (0, 0))
        else:
            target, i = get_nearest_worthy_target(me, game_map, ship.position, worthy_cells)
            if len(worthy_cells) > 1:
                del worthy_cells[i]
   
            # Get next move towards target
            ships[ship.id]['target'] = target
            move = navigate(ship, target, game_map, me, dog_pile_mode)
            set_ship_move(ship, move)   


sector_width = game.game_map.width/len(game.players)
thresh_divisor = 11
halite_thresh = constants.MAX_HALITE/thresh_divisor
turn = 0
dog_pile_mode = False
#worthy_cells = 
# Nested dictionaries of ship attributes
ships = {} 

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("Trogdor")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" 
<<<Game Loop>>> 

"""

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    turn = turn + 1

    # Get worthy cells, decrease threshhold if too few
    worthy_cells = scan_for_targets(game_map, halite_thresh)
    if len(worthy_cells) < len(me.get_ships()) / 2:
        halite_thresh, thresh_divisor = get_bigger_halite_thresh(thresh_divisor, 4)
        worthy_cells = scan_for_targets(game_map, halite_thresh)
        logging.info("INCREASING THRESH DIV by "+ str(thresh_divisor))

    # Turtle down? Stop tracking it
    kill_list = []
    for ship_id in ships:
        if not me.has_ship(ship_id):
            kill_list.append(ship_id)

    for destroyed_ship_id in kill_list:
        del ships[destroyed_ship_id]

    # New ship? Rev 'er up!
    for ship in me.get_ships():
        if ship.id not in ships:
            target, i = get_nearest_worthy_target(me, game_map, ship.position, worthy_cells)
            if len(worthy_cells) > 1:
                del worthy_cells[i]

            ships[ship.id] = {  
                                'obj': ship,
                                'status': COLLECTING,
                                'next_move': (0, 0),
                                'next_pos': ship.position,
                                'handled': False,
                                'target': target
                             } 
            handle_ship(ship)

    for ship in me.get_ships():

        # Only handle ships that have not been forced to be handled from
        # potential collisions of other ships (navigate())
        if ships[ship.id]['handled'] is False:
            handle_ship(ship, dog_pile_mode)

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port or a ship is moving
    # into port
    if game.turn_number <= 220 and \
        me.halite_amount >= constants.SHIP_COST and not \
        game_map[me.shipyard].is_occupied:

        conflict = False
        for ship_id in ships:
            if ships[ship_id]["next_pos"] == me.shipyard.position:
                conflict = True
        if not conflict:
            command_queue.append(me.shipyard.spawn())

    for ship_id in ships:
        command_queue.append(ships[ship_id]['obj'].move(ships[ship_id]['next_move']))
        ships[ship_id]['handled'] = False

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

"""
TODO

- re-work threshhold criterion. Should approach zero towards the end
- IF branch for dog-pile algorithm in the final moves
- avoid colliding with the enemy!

__
Only check current collisions base on current map with enemies.
Only consider perpindiculars for declustering movement
use distance from base as weight for targeting
"""