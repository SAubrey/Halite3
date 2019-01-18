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
  
def check_for_self_collision(position):
    position = make_position(position)
    for ship_id in ships:
        if ships[ship_id]["next_pos"] == position:
            return True


def navigate(ship, target):
    
    """
    # Returns a list of tuples
    moves = game_map.get_unsafe_moves(ship.position, make_position(target))
    #if len(moves) > 0:
    for j in range(0, len(moves)):
        cardinals[4 + j] = moves[j]

    for i in range(3 + len(moves), 0, -1):
        card = cardinals[i]
        target = ship.position.directional_offset(card)
        """

    moves = game_map.get_unsafe_moves(ship.position, make_position(target))
    for m in moves:
        r = random.randint(0, len(moves) - 1)
        new_pos = ship.position.directional_offset(moves[r])

        if not game_map[new_pos].is_occupied:
            if not check_for_self_collision(new_pos):
                return moves[r]
                
        
    flip = random.randint(0, 2)
    open = get_open_directions(ship)
    if flip == 0 and len(open) > 0:
        r = random.randint(0, len(open) - 1) 
        return open[r]

    return (0, 0)

cardinals = {0: Direction.North, 1: Direction.East, 2: Direction.South, 3: Direction.West}

def get_open_directions(ship):
    open = []
    for i in range(0, 4):
        position = ship.position.directional_offset(cardinals[i])
        if not check_for_self_collision(position):
            open.append(cardinals[i])
    return open
"""
def get_direction(source, target):
    logging.info("THis shouldn't print often")
    dx = source[0] - target[0]
    dy = source[1] - target[1]

    if abs(dx) > abs(dy):
        if dx < 0:
            return Direction.East
        else:
            return Direction.West
    else:
        if dy < 0:
            return Direction.South
        else:
            return Direction.North

def get_perpindicular_cardinals(direction):
    direction = make_tuple(direction)
    if direction == Direction.North or direction == Direction.South:
        return Direction.East, Direction.West
    else:
        return Direction.North, Direction.South
"""

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
                #worthy_cells[(c, r)] = cell
                worthy_cells.append(cell)
    return worthy_cells

def get_nearest_worthy_target(game_map, ship_position, worthy_cells):
    if len(worthy_cells) <= 0:
        return (0, 0)
    # Set course target for nearest worthy cell
    nearest_cell_distance = 1000 # arbitrarily large
    nearest_cell = None
    nearest_ind = 0
    
    i = 0
    for cell in worthy_cells:
        distance = game_map.calculate_distance(make_position(ship_position), cell.position)
        if distance < nearest_cell_distance:
            nearest_cell_distance = distance
            nearest_cell = cell
            nearest_ind = i
        i = i + 1

    return make_tuple(nearest_cell.position), nearest_ind

def set_ship_move(ship, move):
    new_pos = ship.position.directional_offset(move)
    ships[ship.id]['next_pos'] = new_pos
    ships[ship.id]['next_move'] = move

def get_bigger_halite_thresh(thresh_divisor, divisor_increment):
    thresh_divisor = thresh_divisor + divisor_increment
    halite_thresh = constants.MAX_HALITE/thresh_divisor 
    return halite_thresh, thresh_divisor

sector_width = game.game_map.width/len(game.players)
thresh_divisor = 11
halite_thresh = constants.MAX_HALITE/thresh_divisor
#worthy_cells = 
# Nested dictionaries of ship attributes
ships = {} 

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []

    # Decrease threshhold for worthy cells
    worthy_cells = scan_for_targets(game_map, halite_thresh)
    if len(worthy_cells) < len(me.get_ships()) / 2:
        halite_thresh, thresh_divisor = get_bigger_halite_thresh(thresh_divisor, 1)
        worthy_cells = scan_for_targets(game_map, halite_thresh)
        logging.info("INCREASING THRESH DIV by "+ str(thresh_divisor))

    for ship in me.get_ships():

        # If ship was just born
        if ship.id not in ships:
            target, i = get_nearest_worthy_target(game_map, ship.position, worthy_cells)
            if len(worthy_cells) > 1:
                del worthy_cells[i]

            ships[ship.id] = {  
                                'obj': ship,
                                'status': COLLECTING,
                                'next_move': (0, 0),
                                'next_pos': ship.position,
                                'alive': True, # Used to detect destroyed ships
                                'target': target
                             } 
        else:
            ships[ship.id]['alive'] = True
            

            if ship.halite_amount > 985 and ships[ship.id]['status'] == COLLECTING:
                ships[ship.id]['status'] = RETURNING
                ships[ship.id]['target'] = make_tuple(me.shipyard.position)
                logging.info(str(ship.id) + " SWITCHED TO RETURNING")


        # Returning to base or a dropoff
        if ships[ship.id]['status'] == RETURNING:
            #dropoff = find_closest_dropoff(ship.position, game_map, me)

            # Set a ship that has dropped off to collecting
            #if game_map[ship.position.directional_offset(move)].has_structure:
            if game_map[ship.position].has_structure:
                logging.info(str(ship.id) + " SWITCHED TO COLLECTING")
                ships[ship.id]['status'] = COLLECTING
                ships[ship.id]['target'] = None
            else:
                move = navigate(ship, me.shipyard.position)
                set_ship_move(ship, move)

        # Collecting - ship should always have a target 
        if ships[ship.id]['status'] == COLLECTING:

            # If ship is not currently heading to a cell for collection
            #if make_tuple(ship.position) == target:

             # If current cell is worth mining, stay
            if game_map[ship.position].halite_amount > halite_thresh:
                set_ship_move(ship, (0, 0))
            else:
                target, i = get_nearest_worthy_target(game_map, ship.position, worthy_cells)
                if len(worthy_cells) > 1:
                    del worthy_cells[i]
       
                # Get next move towards target
                ships[ship.id]['target'] = target
                move = navigate(ship, target)
                set_ship_move(ship, move)   

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port or a ship is moving
    # into port
    if game.turn_number <= 200 and \
        me.halite_amount >= constants.SHIP_COST and not \
        game_map[me.shipyard].is_occupied:

        conflict = False
        for ship_id in ships:
            if ships[ship_id]["next_pos"] == me.shipyard.position:
                conflict = True
        if not conflict:
            command_queue.append(me.shipyard.spawn())
    
    kill_list = []
    for ship_id in ships:

        # If a ship was not handled, it was destroyed.
        if ships[ship_id]['alive'] == False:
            kill_list.append(ship_id)
        else:
            command_queue.append(ships[ship_id]['obj'].move(ships[ship_id]['next_move']))
            ships[ship_id]['alive'] = False

    # Delete destroyed ships
    for destroyed_ship_id in kill_list:
        del ships[destroyed_ship_id]

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

"""
TODO

- re-work threshhold criterion. Should approach zero towards the end
- IF branch for dog-pile algorithm in the final moves
- avoid colliding with the enemy!
"""