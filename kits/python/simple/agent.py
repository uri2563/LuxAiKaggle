import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import logging#logging.info(len(player.units))

DIRECTIONS = Constants.DIRECTIONS
game_state = None

directions = ["n","w","s","e"]#CENTER = "c"

logging.basicConfig(filename="agent.log",level= logging.INFO)


def create_workers_instructions(player,resource_tiles,free_tiles):

    instructions = {}
    un_used_workers = []
    debug = []

    cities_in_need = get_cities_in_need(player)
    for unit in player.units:
        if unit.is_worker():
            if unit.can_act():
                un_used_workers.append(unit);
            else:
                instructions[hash_pos(unit.pos.translate("c", 0))] = "null"
                debug.append(annotate.sidetext("cooling " + unit.id))

    #get wood
    for worker in un_used_workers:
        if worker.get_cargo_space_left() > 0:
            closest_resource_tile = get_close_resource(unit, resource_tiles, player)

            if closest_resource_tile is not None:
                move_dir = worker.pos.direction_to(closest_resource_tile.pos)
                if is_free_pos(instructions, move_dir,worker.pos):
                    instructions[hash_pos(worker.pos.translate(move_dir, 1))] = worker.move(move_dir)
                    un_used_workers.remove(worker)
                    debug.append(annotate.sidetext("gathering " + worker.id + " " + move_dir))

    #fuel cities
    for city in cities_in_need:
        [closest_worker,city_tile] = find_closest_worker_to_city(un_used_workers, city)
        if closest_worker is not None:
            move_dir = closest_worker.pos.direction_to(city_tile.pos)
            if is_free_pos(instructions, move_dir, closest_worker.pos):
                instructions[hash_pos(closest_worker.pos.translate(move_dir, 1))] = closest_worker.move(move_dir)
                un_used_workers.remove(closest_worker)
                debug.append(annotate.sidetext("fuel " + closest_worker.id + " " + move_dir))

    #create city
    for worker in un_used_workers:
        if worker.can_build(game_state.map) and is_free_pos(instructions, "c", unit.pos,0):
            instructions[hash_pos(worker.pos)] = worker.build_city()
            un_used_workers.remove(worker)
            debug.append(annotate.sidetext("create " + worker.id))
        else:
            move_dir = worker.pos.direction_to(get_closest_free_tile(worker,free_tiles).pos)
            if is_free_pos(instructions, move_dir, worker.pos):
                instructions[hash_pos(worker.pos.translate(move_dir, 1))] = worker.move(move_dir)
                un_used_workers.remove(worker)
                debug.append(annotate.sidetext("move create " + worker.id + " " + move_dir))

    #move workers in the way
    for worker in un_used_workers:
        if hash_pos(worker.pos) in instructions:
            move_worker_to_rand_free_spot(worker, instructions)
            debug.append(annotate.sidetext("away " + worker.id))
        else:
            debug.append(annotate.sidetext("stay " + worker.id))
            instructions[hash_pos(worker.pos.translate("c", 0))] = "null"

    return [instructions,debug]


def create_cities_instructions(player,number_of_city_tiles):
    instructions = {}
    count = number_of_city_tiles - (len(player.units))
    if count > 0:
        for key, city in player.cities.items():
            for city_tile in city.citytiles:
                if city_tile.can_act():
                    if count > 0:
                        count = count - 1
                        instructions[city_tile.cityid] = city_tile.build_worker()
                    else:
                        instructions[city_tile.cityid] = city_tile.research()
    return instructions


#returns the best potential location
def potential_location(unit_pos,free_tiles,resource_tiles, max_distance):
    width, height = game_state.map.width, game_state.map.height
    max_resources_near_by = 0
    best_pos = unit_pos
    for tile in free_tiles:
        if unit_pos.distance_to(tile.pos) < max_distance:
            num = get_number_of_resources_in_radius(tile, resource_tiles, 5)
            if num > max_resources_near_by: #TODO - add check for better distance
                max_resources_near_by = num
                best_pos = tile.pos
    return best_pos

def get_number_of_resources_in_radius(tile, resource_tiles, radius):
    count = 0
    for resource_tile in resource_tiles:
        if tile.pos.distance_to(resource_tile.pos) <= radius:
            count = count + 1
    return count

def find_closest_worker_to_city(worker_list, city):
    closest_dist = math.inf
    closest_worker = None
    closest_city_tile = None
    for worker in worker_list:
        for city_tile in city.citytiles:
            dist = worker.pos.distance_to(city_tile.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_worker = worker
                closest_city_tile = city_tile
    return [closest_worker,closest_city_tile]

def get_cities_in_need(player):
    cities_in_need = [];
    for city in player.cities.items():
        if city[1].fuel < 230:
            cities_in_need.append(city[1])
    return cities_in_need

def get_closest_city(player,unit):
    closest_dist = math.inf
    closest_city_tile = None
    for city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile

def get_close_resource(unit,resource_tiles,player):
    closest_dist = math.inf
    closest_resource_tile = None
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.WOOD and is_depleted(resource_tile): continue
        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile

# return true if resource is going to deplete
#TODO - check if enemy is nearby
def is_depleted(cell):
    return cell.resource.amount < 150 and game_state.turn < 345


def get_resource_and_free_tiles(width,height):
    resource_tiles: list[Cell] = []
    free_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
            elif cell.citytile is None:
                free_tiles.append(cell)
    return [resource_tiles, free_tiles]

def get_closest_free_tile(unit,free_tiles):
    closest_dist = math.inf
    closest_resource_tile = None
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for free_tile in free_tiles:
        dist = free_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = free_tile
    return closest_resource_tile

def closest_city_without_fuel(player,unit):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist and (city.fuel < 230):
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile

def is_free_pos(workers_targets, move_dir,pos,step =1):
    return not (hash_pos(pos.translate(move_dir, step)) in workers_targets and game_state.map.get_cell_by_pos(pos.translate(move_dir, step)).citytile is None)

def pos_in_map(pos):
    width, height = game_state.map.width, game_state.map.height
    return pos.x < width and pos.x >= 0 and pos.y < width and pos.y >= 0

def move_worker_to_rand_free_spot(worker, instructions):
    for move_dir in directions:
        if is_free_pos(instructions,move_dir,worker.pos) and pos_in_map(worker.pos.translate(move_dir, 1)):
            instructions[hash_pos(worker.pos.translate(move_dir, 1))] = worker.move(move_dir)
            return

def hash_pos(pos):
    return pos.x + pos.y*1000



def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    [resource_tiles,free_tiles] = get_resource_and_free_tiles(width,height)
    number_of_city_tiles = player.city_tile_count #get_number_of_city_tiles(player)

    logging.info("turn:" + str(game_state.turn))

    #relocate
    if len(player.units) is 1 and player.units[0].get_cargo_space_left() is 0 and game_state.turn <= 20:
        worker = player.units[0]
        potential_loc = potential_location(worker.pos,free_tiles,resource_tiles, 15)#TODO change the 15 to somthing based on board size
        if worker.pos.distance_to(potential_loc) <= 0 and worker.can_build(game_state.map):
            worker.build_city()
        else:
            move_dir = worker.pos.direction_to(potential_loc)
            actions.append(worker.move(move_dir))
    else:
        [workers_inst, debug]= create_workers_instructions(player, resource_tiles, free_tiles)
        cities_inst = create_cities_instructions(player,number_of_city_tiles)

        for key, value in cities_inst.items():
            actions.append(value)
        for key, value in workers_inst.items():
            if value is not "null":
                actions.append(value)
        for value in debug:
            actions.append(value)

    return actions
