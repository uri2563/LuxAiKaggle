import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None


def create_workers_instractions():
    instractions = {}
    un_used_workers = []
    cities_in_need = get_cities_in_need()
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            un_used_workers.append(unit);

    for worker in un_used_workers:
        if worker.unit.get_cargo_space_left() > 0:
            closest_resource_tile = get_close_resource(unit, resource_tiles, player)

            if closest_resource_tile is not None:
                move_dir = unit.pos.direction_to(closest_resource_tile.pos)
                instractions[worker.id] = unit.move(move_dir)
                un_used_workers.remove(worker)

    for k, city in cities_in_need:
        closest_worker = find_closest_worker(un_used_workers, city)
        move_dir = unit.pos.direction_to(city.pos)
        instractions[closest_worker.id] = unit.move(move_dir)
        un_used_workers.remove(closest_worker)

    for worker in un_used_workers:
        move_dir = unit.pos.direction_to( get_closest_free_tile().pos)
        instractions[closest_worker.id] = unit.move(move_dir)
        un_used_workers.remove(worker)

    return instractions

def create_workers_instractions(player):
    instractions = {}
    count = len(player.cities) - (len(player.units))
    if count > 0:
        for k, city in player.cities.items():
            if city.can_act() and count > 0:
                count= count - 1
                instractions[city.cityid] = city.build_worker()
    return instractions




def get_closest_city(player,unit):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return  closest_city_tile

def get_close_resource(unit,resource_tiles,player):
    closest_dist = math.inf
    closest_resource_tile = None
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return  closest_resource_tile

def get_resource_and_free_tiles(game_state, width,height):
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

def get_closest_free_tile(unit,free_tiles,player):
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

    [resource_tiles,free_tiles] = get_resource_and_free_tiles(game_state, width,height)

    workers_targets = {};
# control .
    # we iterate over all our units and do something with them
    # for unit in player.units:
    #     if unit.is_worker() and unit.can_act():
    #
    #         if unit.get_cargo_space_left() > 0:
    #             closest_resource_tile = get_close_resource(unit,resource_tiles,player)
    #
    #             if closest_resource_tile is not None:
    #                 move_dir = unit.pos.direction_to(closest_resource_tile.pos)
    #                 if not hash_pos(unit.pos.translate(move_dir,1)) in workers_targets:
    #                     actions.append(unit.move(move_dir))
    #                     workers_targets[hash_pos(unit.pos.translate(move_dir,1))] = unit
    #
    #         else:
    #             close_free_tile = get_closest_free_tile(unit,free_tiles,player)
    #             if unit.cargo.wood >= 100 and close_free_tile is not None and len(player.cities) < (len(player.units) * 2):
    #                 if unit.can_build(game_state.map):
    #                     actions.append(unit.build_city())
    #                 else:
    #                     move_dir = unit.pos.direction_to(close_free_tile.pos)
    #                     if not hash_pos(unit.pos.translate(move_dir,1)) in workers_targets:
    #                         actions.append(unit.move(move_dir))
    #                         workers_targets[hash_pos(unit.pos.translate(move_dir,1))] = unit
    #
    #             # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
    #             elif len(player.cities) > 0:
    #                 closest_city_tile = get_closest_city(player,unit)
    #
    #                 if closest_city_tile is not None:
    #                     move_dir = unit.pos.direction_to(closest_city_tile.pos)
    #                     if not hash_pos(unit.pos.translate(move_dir,1)) in workers_targets:
    #                         actions.append(unit.move(move_dir))
    #                         workers_targets[hash_pos(unit.pos.translate(move_dir,1))] = unit

    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))

    return actions
