#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random

import numpy as np
from numpy.random import choice

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

directions = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

ship_status = {}

""" <<<Game Loop>>> """
while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map


    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        if ship.id not in ship_status.keys() or ship.position == me.shipyard.position:
            ship_status[ship.id] = "exploring" 

        if ship.is_full:
            ship_status[ship.id] = "returning"

        position_options = ship.position.get_surrounding_cardinals() + [ship.position]

        position_dict = {}
        halite_amounts = []

        for i, direction in enumerate(directions):
            position_dict[direction] = position_options[i]
            if game_map[position_options[i]].is_occupied:
                if i == 4:
                    halite_amounts.append(game_map[position_options[i]].halite_amount)
                    continue
                halite_amounts.append(0)
            else:
                halite_amounts.append(game_map[position_options[i]].halite_amount)
        
        halite_amounts = np.array(halite_amounts)
        halite_amounts = halite_amounts/np.sum(halite_amounts)
        halite_amounts = [np.asscalar(item) for item in halite_amounts]
        logging.info(halite_amounts)

        if ship_status[ship.id] == "exploring":
            if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
                command_queue.append(ship.move(directions[choice(4, 1, halite_amounts)[0]]))
            else:
                command_queue.append(ship.stay_still())
        elif ship_status[ship.id] == "returning":
            command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

