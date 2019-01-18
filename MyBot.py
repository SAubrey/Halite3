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

"""
def assign_targets(game_map, ships, worthy_cells):

    for ship_id in ships:

        # If ship is not currently heading to a cell for collection
        if ships[ship_id]['target'] == None:

            # Set course target for nearest worthy cell
            current_position = ships[ship_id]['obj'].position
            nearest_cell_distance = 1000 # arbitrarily large
            nearest_cell = None
            
            for cell in worthy_cells:
                distance = game_map.calculate_distance(current_position, cell.position)
                if distance < nearest_cell_distance:
                    nearest_cell_distance = distance
                    nearest_cell = cell
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
    
def navigate(ship, target):
    # Returns a list of tuples
    moves = game_map.get_unsafe_moves(ship.position, make_position(target))

    for move in moves:
        # Collision check
        new_pos = ship.position.directional_offset(move)

        #if not game_map[new_pos].is_occupied:
        conflict = False
        for ship_id in ships:
            if ships[ship_id]["next_pos"] == new_pos:
                conflict = True
        if not conflict:
            return move
    return (0, 0)

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
    
    # Set course target for nearest worthy cell
    nearest_cell_distance = 1000 # arbitrarily large
    nearest_cell = None
    
    for cell in worthy_cells:
        distance = game_map.calculate_distance(make_position(ship_position), cell.position)
        if distance < nearest_cell_distance:
            nearest_cell_distance = distance
            nearest_cell = cell

    return make_tuple(nearest_cell.position)

def set_ship_move(ship, move):
    new_pos = ship.position.directional_offset(move)
    ships[ship.id]['next_pos'] = new_pos
    ships[ship.id]['next_move'] = move


sector_width = game.game_map.width/len(game.players)
halite_thresh = constants.MAX_HALITE/6
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

    worthy_cells = scan_for_targets(game_map, halite_thresh)

    for ship in me.get_ships():

        # If ship was just born
        if ship.id not in ships:
            ships[ship.id] = {  
                                'obj': ship,
                                'status': COLLECTING,
                                'next_move': (0, 0),
                                'next_pos': ship.position,
                                'alive': True, # Used to detect destroyed ships
                                'target': get_nearest_worthy_target(game_map, ship.position, worthy_cells)
                             } 
        else:
            ships[ship.id]['alive'] = True
            
            if ship.is_full and ships[ship.id]['status'] == COLLECTING:
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
            target = ships[ship.id]['target']

            # If ship is not currently heading to a cell for collection
            if target == None:
                target = get_nearest_worthy_target(game_map, ship.position, worthy_cells)
            else:
                # If at target
                if make_tuple(ship.position) == target:

                    # Cell sufficiently depleted, but ship is not full yet
                    if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10:
                        target = get_nearest_worthy_target(game_map, ship.position, worthy_cells)
                else:
                    target = get_nearest_worthy_target(game_map, ship.position, worthy_cells)
       
            # Get next move towards target
            ships[ship.id]['target'] = target
            move = navigate(ship, target)
            set_ship_move(ship, move)   

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port or a ship is moving
    # into port
    if game.turn_number <= 200 and \
        me.halite_amount >= constants.SHIP_COST * 3 and not \
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
