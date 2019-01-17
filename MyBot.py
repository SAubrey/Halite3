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

def find_closest_dropoff(position, game_map, player):
    closest_dropoff = None
    closest_distance = 100
    
    logging.info(player.get_dropoffs())
    for dropoff in player.get_dropoffs():
    
        distance = game_map.calculate_distance(position, dropoff.position)  
        if distance < closest_distance:
            closest_distance = distance
            closest_dropoff = dropoff
    if closest_dropoff is None:
        return me.shipyard
    return closest_dropoff
    
def navigate(ship, target):
    # Returns a list of Direction.North type directions
    moves = game_map.get_unsafe_moves(ship.position, target)
    #logging.info(len(moves))

    for move in moves:
        # Collision check
        new_pos = ship.position.directional_offset(move)

        if not game_map[new_pos].is_occupied:
            conflict = False
            for ship_id in ships:
                if ships[ship_id]["next_pos"] == new_pos:
                    conflict = True
            if not conflict:
                return move
    return (0, 0)

player_count = len(game.players)
sector_width = game.game_map.width/player_count
"""
scan whole 16x16 sector,
find all positions above a threshhold of halite,
send ships to the closest one (add target attribute in ship dicts, each ship has unique target)
"""


def get_moves(ship, target):
    pass

def tuple(position):
    return (position.x, position.y)
"""
def tuple_to_dir(t):
    cards = Direction.get_all_cardinals()
    if t[0] == 1:
        #return cards[2]
        return "e"
    elif t[0] == -1:
        #return cards[3]
        return "w"
    elif t[1] == 1:
        #return cards[1]
        return "s"
    elif t[1] == -1:
        #return cards[0]
        return "n"
    else:
        return "o" 
"""
def set_ship_status(ship, move):
    new_pos = ship.position.directional_offset(move)
    ships[ship.id]['next_pos'] = new_pos
    ships[ship.id]['next_move'] = move

# Dictionary of each ship's data in a dictionary
ships = {} 

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []

    for ship in me.get_ships():
        """
        For each ship, 
        if the current square does not contain > 1/10th max halite, move
        else if ship is full, return to a dropoff
        otherwise, collect Halite
        """
        if ship.id not in ships:
            ships[ship.id] = {  'obj': ship,
                                'status': COLLECTING,
                                'next_move': (0, 0),
                                'next_pos': ship.position,
                                'alive': True } # Used to detect destroyed ships
        ships[ship.id]['alive'] = True

        if ship.is_full:
            ships[ship.id]['status'] = RETURNING
            logging.info("SWITCH TO RETURNING")

        if ships[ship.id]['status'] == RETURNING:
            #dropoff = find_closest_dropoff(ship.position, game_map, me)
            move = navigate(ship, me.shipyard.position)
            set_ship_status(ship, move)

            # Set a ship that has dropped off to collecting
            if game_map[ship.position.directional_offset(move)].has_structure:
                logging.info("SWITCH TO COLLECTING")
                ships[ship.id]['status'] = COLLECTING
        elif ships[ship.id]['status'] == COLLECTING:
            if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10:
                x = random.randrange(0, 20)
                target = Position(x, x)
            
                move = navigate(ship, target)
                set_ship_status(ship, move)
            else:
                set_ship_status(ship, (0, 0))
        else:
            logging.info(ships[ship.id])
            set_ship_status(ship, (0, 0))
            
        
    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port or a ship is moving
    # into port
    if game.turn_number <= 200 and \
        me.halite_amount >= constants.SHIP_COST * 4 and not \
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

