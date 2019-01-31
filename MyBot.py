#!/usr/bin/env python3
# Python 3.6
# Sean Aubrey, Lanndon Rose
# January 2019

import hlt
from hlt import *
import random
import logging

RETURNING = 0
COLLECTING = 1

""" <<<Game Begin>>> """
game = hlt.Game()

def make_tuple(position):
    """Returns a tuple from the given Halite Position object."""
    if type(position) == hlt.positionals.Position:
        return (position.x, position.y)
    else:
        return position

def make_position(tup):
    """Returns a Halite Position object from the given tuple."""
    if type(tup) == tuple:
        return Position(tup[0], tup[1])
    else:
        return tup

def get_total_halite(game_map):
    """Returns the total unmined halite on the game map."""
    maxRow = game_map.height
    maxCol = game_map.width
    sum = 0

    for r in range(0, maxRow):
        for c in range(0, maxCol):
            cell = game_map[Position(c, r)]
            sum = sum + cell.halite_amount
    return sum

def clean_dead_ships(ships):
    """Returns the number of friendly ships collided in the last turn
    while removing them from the ships dictionary."""
    kill_list = []
    ships_collided = 0
    for ship_id in ships:
        if not me.has_ship(ship_id):
            kill_list.append(ship_id)
            ships_collided += 1

    for destroyed_ship_id in kill_list:
        del ships[destroyed_ship_id]
    return ships_collided

def get_lower_halite_thresh(thresh_divisor, divisor_increment):
    """Returns a smaller halite threshhold above which worthy targets
     will be found and the larger corresponding divisor."""
    thresh_divisor = thresh_divisor + divisor_increment
    halite_thresh = constants.MAX_HALITE/thresh_divisor
    return thresh_divisor, halite_thresh

def has_halite_to_move(ship):
    """Used to prevent a ship from being forced to be still."""
    if ship.halite_amount >= game_map[ship.position].halite_amount * 0.1:
        return True
    return False

def return_by_end(ship):
    """This makes sure a ship returns to the shipyard before the game ends."""
    if ship.halite_amount > 50:
        distance = game_map.calculate_distance(ship.position, shipyard.position)
        turns_left = constants.MAX_TURNS - turn
        if distance + 15 > turns_left:
            ships[ship.id]['status'] = RETURNING

# This is unsafe, it does not account for enemy's projected movement.
def check_enemy_collision(position):
    """This checks if a cell is occupied with an enemy."""
    if game_map[position].is_occupied:
        if not me.has_ship(game_map[position].ship.id):
            return True
    return False

# Check for collisions without accounting for 
def simple_check_self_collision(ship, position):
    """Returns true if another ship already intends to move into the
     given position.  Will base comparisons on the previous game state."""
    position = make_position(position)
    for ship_id in ships:
        if ships[ship_id]["next_pos"] == position \
            and ships[ship_id]['obj'] != ship:
            return True
    return False

# If a collision is found, this function will attempt to handle the conflicting
# ship to avoid returning a false positive based on that ship's next move
# from the previous game state. The check will then continue recursively until
# the position of the ideal move is freed or exhaustively confirmed to have
# already been set within this game cycle. 
def check_self_collision(ship, position, potential_move):
    """Returns true if another ship intends to move into given position, 
    updating conflicting ships that have not been handled in the current 
    game state."""
    position = make_position(position)
    for ship_id in ships:
        if ships[ship_id]["next_pos"] == position \
            and ships[ship_id]['obj'] != ship:

            # Process the unprocessed problematic ship, then decide if it's a problem.
            if ships[ship_id]['handled'] is False:

                 # Set what this ship *would* do before the problematic ship gets handled.
                 # This allows ships to move through each other.
                set_ship_move(ship, potential_move)
                handle_ship(ships[ship_id]['obj'])
                return check_self_collision(ship, position, potential_move)
            else:
                return True
    return False

def navigate(ship, target):
    """Returns a random, safe move from the best available moves towards
    a destination position.  Multiple uses results in diagonal movement.
    Handles a deadlock by moving sideways half of the time."""
    if not has_halite_to_move(ship):
        return (0, 0)

    previous_move = ships[ship.id]['next_move']
    moves = game_map.get_unsafe_moves(ship.position, make_position(target))
    r = random.randint(0, len(moves) - 1)
    new_pos = ship.position.directional_offset(moves[r])

    if dog_pile_mode and shipyard.position == new_pos:
        return moves[r]
    elif (not check_enemy_collision(new_pos) and not 
            check_self_collision(ship, new_pos, moves[r])):
        return moves[r]

    # Way forward is blocked, so move sideways sometimes.
    flip = random.randint(0, 1)
    open = get_open_perpindiculars(ship, moves[r])
    if flip == 0 and len(open) > 0:
        r = random.randint(0, len(open) - 1) 
        return open[r]
    return (0, 0)
    
def get_open_perpindiculars(ship, move):
    """Returns a list of safe moves perpindicular to the given target move."""
    open = []
    perpindiculars = get_perpindicular_cardinals(move)
    for i in range(0, 2):
        position = ship.position.directional_offset(perpindiculars[i])

        if (not simple_check_self_collision(ship, position) and not 
            check_enemy_collision(position)):
            open.append(perpindiculars[i])
    return open

def get_perpindicular_cardinals(direction):
    """Returns a tuple of the directions perpindicular to the given direction."""
    direction = make_tuple(direction)
    if direction == Direction.North or direction == Direction.South:
        return Direction.East, Direction.West
    else:
        return Direction.North, Direction.South

def scan_for_targets(thresh):
    """Returns a list of map cells that are equal or greater to the 
    given halite threshold."""
    maxRow = game_map.height
    maxCol = game_map.width
    worthy_cells = []

    for r in range(0, maxRow):
        for c in range(0, maxCol):
            cell = game_map[Position(c, r)]
            if cell.halite_amount >= thresh:
                worthy_cells.append(cell)
    return worthy_cells

def get_nearest_worthy_target(ship_position):
    """Returns a tuple position of the nearest cell to the given position
    that meets the halite treshold, then deletes that cell from the list."""
    if len(worthy_cells) <= 0:
        return (0, 0)

    nearest_cell_distance = 1000 # arbitrarily large
    nearest_cell = None
    nearest_ind = 0
    
    # Find the cell nearest to the ship
    i = 0
    for cell in worthy_cells:
        ship_distance = game_map.calculate_distance(ship_position, cell.position)
        if ship_distance < nearest_cell_distance:
            nearest_cell_distance = ship_distance
            nearest_cell = cell
            nearest_ind = i
        i += 1

    # Remove cell from list to avoid duplicate assignment
    del worthy_cells[nearest_ind]  
    return make_tuple(nearest_cell.position)

def set_ship_move(ship, move):
    """Updates the ships dictionary for the given ship and its move."""
    new_pos = ship.position.directional_offset(move)
    if move == (0, 0):
        new_pos = ship.position
    ships[ship.id]['next_pos'] = new_pos
    ships[ship.id]['next_move'] = move

def able_to_spawn():
    """Returns true if a ship does not intend to move into the shipyard."""
    conflict = False
    for ship_id in ships:
        if ships[ship_id]["next_pos"] == shipyard.position:
            conflict = True
    if not conflict:
        return True
    else:
        return False

def handle_ship(ship):
    """Performs the decision making of the given ship and accordingly 
    assigns its destination and next move to get there."""
    id = ship.id
    ships[id]['handled'] = True

    # Begin return journey slightly before max capacity to avoid wasting
    # a turn on an insignificant gather.
    if ship.halite_amount > 985 and ships[id]['status'] == COLLECTING:
        ships[id]['status'] = RETURNING
        ships[id]['target'] = make_tuple(shipyard.position)

    # Turn on end-game dog pile onto the shipyard
    if dog_pile_mode:
        return_by_end(ship)

    # Returning - Traveling to shipyard to drop off halite
    if ships[id]['status'] == RETURNING:

        # Set a ship that has dropped off to collecting
        if game_map[ship.position].has_structure:
            ships[id]['status'] = COLLECTING
            ships[id]['target'] = None
        else:
            move = navigate(ship, shipyard.position)
            set_ship_move(ship, move)

    # Collecting - Ship is gathering halite
    if ships[id]['status'] == COLLECTING:

         # If current cell is worth mining, stay
        if game_map[ship.position].halite_amount >= halite_thresh:
            set_ship_move(ship, (0, 0))
        else:
            target = get_nearest_worthy_target(ship.position)
   
            # Get next move towards target
            ships[id]['target'] = target
            move = navigate(ship, target)
            set_ship_move(ship, move)   


thresh_divisor = 11
#thresh_divisor_increment = 5 + game.game_map.width / 6
thresh_divisor_increment = thresh_divisor
halite_thresh = constants.MAX_HALITE/thresh_divisor

total_initial_halite = get_total_halite(game.game_map)
max_possible_halite = (game.game_map.width ** 2) * constants.MAX_HALITE
halite_density = total_initial_halite / max_possible_halite

dog_pile_mode = False
turn = 0
ships_collided = 0
ships = {} 
worthy_cells = []

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("Trogdor")

""" <<<Game Loop>>> """
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    shipyard = me.shipyard
    command_queue = []
    turn += 1

    # Get worthy cells, decrease halite threshhold if too few so that 
    # the number of worthy cells increases.
    worthy_cells = scan_for_targets(halite_thresh)
    if len(worthy_cells) < len(me.get_ships()):
        thresh_divisor, halite_thresh = get_lower_halite_thresh(thresh_divisor,
                                                     thresh_divisor_increment)
        worthy_cells = scan_for_targets(halite_thresh)
        logging.info("INCREASING THRESH DIV to "+ str(thresh_divisor))

    # Turtle down? Stop tracking it
    ships_collided += clean_dead_ships(ships)

    if turn > constants.MAX_TURNS * .90 and not dog_pile_mode:
        dog_pile_mode = True

    # New ship? Rev 'er up!
    for ship in me.get_ships():
        if ship.id not in ships:
            target = get_nearest_worthy_target(ship.position)

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
        # potential collisions of other ships.
        if ships[ship.id]['handled'] is False:
            handle_ship(ship)

    # Don't spawn a ship if you currently have a ship at port or a ship is moving into port.
    if (me.halite_amount >= constants.SHIP_COST and not
        game_map[me.shipyard].is_occupied
        and able_to_spawn()):

        if game.turn_number <= constants.MAX_TURNS / 2:  
            command_queue.append(me.shipyard.spawn())

        # Between the half and 2/3 point, spawn to make up for collided ships if the 
        # map has a sufficient halite density.
        elif (game.turn_number <= constants.MAX_TURNS * 0.66 and 
              ships_collided > 0 and
             (get_total_halite(game_map) / max_possible_halite) > 0.08):
            ships_collided -= 1
            command_queue.append(me.shipyard.spawn())

    # Add all ships' next move to the Halite command queue.
    for ship_id in ships:
        command_queue.append(ships[ship_id]['obj'].move(ships[ship_id]['next_move']))
        ships[ship_id]['handled'] = False

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)