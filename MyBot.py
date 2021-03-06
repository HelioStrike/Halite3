#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

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
game.ready("GreedyBoi")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

directions = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

#stores harvestable(is that a word?) points
meat_points = []

taken = []

game_map = game.game_map

meat_factor = 3

#storing meat points
def getMeatPoints():
    global meat_points
    meat_points = []
    for x in range(game_map.height):
        for y in range(game_map.height):
            pos = Position(x, y)
            if game_map[pos].halite_amount > constants.MAX_HALITE/meat_factor:
                meat_points.append(pos)
                taken.append(0)

#returns nearest meat point
def nearestMeatPoint(pos, ship_positions):
    global taken

    min_dist = 10000
    min_pos = None
    for p in range(len(meat_points)):
        if meat_points[p] in ship_positions or taken[p] == 1: continue

        dist = abs(meat_points[p].x - pos.x) + abs(meat_points[p].y - pos.y)
        logging.info(dist)
        if(dist < min_dist):
            min_dist = dist
            min_pos = p

    taken[p] = 1
    return meat_points[min_pos]

#maps ship id to their designated destination
ship_dests = {} 

""" <<<Game Loop>>> """
while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    logging.info("Meat factor " + str(meat_factor))

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    #stores current and next positions of ships, so that other ships can avoid these stops(even turtles need personal space!)
    ship_positions = []

    taken = [0 for i in range(len(meat_points))]

    #storing initial positions of ships
    for ship in me.get_ships():
        ship_positions.append(ship.position)


    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.

        #if the ship id doesn't exist in ship_dests or the ship is at the shipyard, give his life a meaning
        if ship.id not in ship_dests.keys() or ship.position == me.shipyard.position:
            ship_dests[ship.id] = nearestMeatPoint(ship.position, ship_positions)

        ship_positions.append(ship.position)

        #if ship is full, draw him to the shipyard
        if ship.is_full:
            ship_dests[ship.id] = me.shipyard.position

        #if its a returning ship
        if ship_dests[ship.id] == me.shipyard.position:
            #the next 10 lines of code make sure that the ship doesn't collide with any other step, and updates ship_positions
            next_move = game_map.naive_navigate(ship, me.shipyard.position)
            if next_move == Direction.Still or ship.position.addDirection(next_move) in ship_positions:
                for p in range(5):
                    move = directions[random.randint(0, 3)]
                    if(not game_map[ship.position.addDirection(move)].is_occupied and ship.position.addDirection(move) not in ship_positions):
                        next_move = move
                        break
            ship_positions.append(ship.position.addDirection(next_move))
            command_queue.append(ship.move(next_move))
        #else if the ship's cell if almost clear
        elif game_map[ship.position].halite_amount < constants.MAX_HALITE/max(10, meat_factor):
            #if ship is at its destination((possibly former) meat point), remove it from meat points as it is exhausted
            if ship.position in meat_points:
                meat_points.remove(ship.position)
            if ship.position == ship_dests[ship.id]:
                ship_dests[ship.id] = nearestMeatPoint(ship.position, ship_positions)
            if game_map[ship_dests[ship.id]].halite_amount < constants.MAX_HALITE/meat_factor:
                ship_dests[ship.id] = nearestMeatPoint(ship.position, ship_positions)

            #the next 10-ish lines of code make sure that the ship doesn't collide with any other step, and updates ship_positions
            next_move = game_map.naive_navigate(ship, ship_dests[ship.id])
            if next_move == Direction.Still or ship.position.addDirection(next_move) in ship_positions:
                for p in range(5):
                    move = directions[random.randint(0, 3)]
                    if(not game_map[ship.position.addDirection(move)].is_occupied and ship.position.addDirection(move) not in ship_positions):
                        next_move = move
                        break
            ship_positions.append(ship.position.addDirection(next_move))
            command_queue.append(ship.move(next_move))

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    #if we're running out of meat points, reduce standards
    if len(meat_points) <= len(me.get_ships()) + 1:
        meat_factor *= 2
        getMeatPoints()

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

