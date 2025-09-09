from mesa import Agent, Model

from mesa.space import MultiGrid

from mesa.time import RandomActivation

from mesa.time import BaseScheduler

from mesa.datacollection import DataCollector

from mesa.batchrunner import batch_run

import matplotlib.lines as plt
import random
import numpy as np
import pandas as pd
import seaborn as sns
sns.set()

import time
import datetime

# ------------------------------------------------------
# ------------------ AGENTE ----------------------------
# ------------------------------------------------------

class AstronautAgent(Agent):
    def __init__(self, model, id):
        super().__init__(model)
        self.action_points = 4
        self.carrying_victim = False
        self.unique_id = id

    def aux_reveal_POI(self, pos):
      x, y = pos
      if self.carrying_victim == False:
        if self.model.cell_state[x][y] == 1:
          self.model.set_state(x, y, 0)
        else:
          self.model.set_state(x, y, 3)
        self.model.set_victims()
        self.carrying_victim = True
      else:
        if self.model.cell_state[x][y] == 1:
          self.model.set_state(x, y, 5)
        else:
          self.model.set_state(x, y, 6)
        self.model.set_victims()

    def move(self, position, state):
      x, y = position
      self.model.grid.move_agent(self, position)
      if state != 4 and self.carrying_victim == False:
        self.action_points -= 1
        if state in (1, 2):
          vict = self.model.reveal_POI(position)
          print("- reveal move", position)
          if vict == True:
            self.aux_reveal_POI(position)
            print("AUX REVEAL")
        elif state in (5, 6):
          self.carry_victim(state)
      else:
        self.action_points -= 2
      if position in self.model.ambulance and self.carrying_victim == True:
          self.carrying_victim = False
          self.model.decrease_POI()
          print("move decrease")
          self.model.save_victim()

    def interactDoor(self, position, z):
      x, y = position
      if self.model.cell_walls[x][y][z] == 3:
        self.model.set_wall(x, y, z, 4)
      else:
        self.model.set_wall(x, y, z, 3)
      self.action_points -= 1

    def attack(self, position, kill):
      x, y = position
      state = self.model.cell_state[x][y]
      if state == 3:
        self.model.set_state(x, y, 0)
        self.action_points -= 0.5
      elif state == 2:
        self.model.set_state(x, y, 1)
        self.action_points -= 0.5
      elif state == 6:
        self.model.set_state(x, y, 5)
        self.action_points -= 0.5
      elif state == 4:
        if kill == True:
          self.model.set_state(x, y, 0)
          self.action_points -= 1
        else:
          self.model.set_state(x, y, 3)
          self.action_points -= 0.5

    def chop(self, position, z, demolish):
      x, y = position
      wall = self.model.cell_walls[x][y][z]
      if wall == 1:
        self.model.set_wall(x, y, z, 0)
        self.model.increase_damage(0.5)
        self.action_points -= 1
      elif wall == 2:
        if demolish == True:
          self.model.set_wall(x, y, z, 0)
          self.model.increase_damage(1)
          self.action_points -= 2
        else:
          self.model.set_wall(x, y, z, 1)
          self.model.increase_damage(0.5)
          self.action_points -= 1

    def knockedDown(self):
      x, y = self.pos
      nearest_ambulance = self.model.ambulance[0]
      min_distance = abs(x - nearest_ambulance[0]) + abs(y - nearest_ambulance[1])
      if self.carrying_victim == True:
        self.carrying_victim = False
        self.model.lose_victim()
        self.model.decrease_POI()
        print("knock decrease")
      for ambulance_pos in self.model.ambulance:
          dist = abs(x - ambulance_pos[0]) + abs(y - ambulance_pos[1])
          if dist < min_distance:
              min_distance = dist
              nearest_ambulance = ambulance_pos
      self.model.grid.move_agent(self, nearest_ambulance)

    def carry_victim(self, state):
      x, y = self.pos
      if state == 5:
        self.model.set_state(x, y, 0)
      elif state == 6:
        self.model.set_state(x, y, 3)
      self.carrying_victim = True

    def relative_position(self, position):
      x, y = self.pos
      x1, y1 = position
      res = -1, -1
      if x == x1 and y == y1 - 1:
        res = 0, 2
      elif x == x1 + 1 and y == y1:
        res = 1, 3
      elif x == x1 and y == y1 + 1:
        res = 2, 0
      elif x == x1 - 1 and y == y1:
        res = 3, 1
      return res

    def step(self):
      cont = True
      while cont == True and 0 <= self.action_points <= 4:
        pos = self.pos
        sx, sy = pos
        possible_positions = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        options = np.random.permutation(len(possible_positions))
        acted = False
        if self.model.cell_state[sx][sy] in (5, 6):
          self.carry_victim(state)
        for i in options:
          position = possible_positions[i]
          x, y = position
          z, a = self.relative_position(position)
          if z == -1 and a == -1:
            continue
          wall = self.model.cell_walls[sx][sy][z]
          state = self.model.cell_state[x][y]
          self_state = self.model.cell_state[sx][sy]
          action = np.random.permutation(5)
          for j in action:
            for amb in self.model.ambulance:
              if pos == amb and (self.carrying_victim == True or self.model.cell_state[sx][sy] in (5, 6)):
                self.carrying_victim = False
                self.model.save_victim()
                if self.model.cell_state[sx][sy] == 5:
                  self.model.set_state(sx, sy, 0)
                elif self.model.cell_state[sx][sy] == 6:
                  self.model.set_state(sx, sy, 3)
            if j == 0 and (wall in (0, 4)) and not(self.carrying_victim == True and state == 4):
              self.move(position, state)
              acted = True
              break
            elif j == 1 and wall in (3, 4):
              self.interactDoor(pos, z)
              self.interactDoor(position, a)
              acted = True
              break
            elif (j == 2 and ((1 < self_state < 5) or self_state == 6)) or (j == 3 and ((1 < state < 5) or state == 6)):
              kill = bool(random.getrandbits(1))
              if j == 2:
                aux_pos = pos
              else:
                aux_pos = position
                if kill == False or self.action_points > 1:
                  self.attack(aux_pos, kill)
                  acted = True
                  break
            elif j == 4 and wall in (1, 2):
              demolish = bool(random.getrandbits(1))
              if (wall == 1 and self.action_points >= 2) or (wall == 2 and self.action_points >= 4):
                self.chop(pos, z, demolish)
                self.chop(position, a, demolish)
                acted = True
                break
          if acted == True:
            break
        cont = bool(random.getrandbits(1))
      self.model.advanceInvasion()
      self.model.enviroment_update()
      self.model.replenish_POI()
      print("FINISHED STEP")
# ------------------------------------------------------
# ------------------ FUNC AUX --------------------------
# ------------------------------------------------------
def get_grid(model):
  grid = np.zeros( (model.grid.width, model.grid.height) )
  for content, (x,y) in model.grid.coord_iter():
    grid[x][y] = model.cell_state[x][y]
    if len(content) != 0:
      grid[x][y] = len(content) + 6
  return grid

# ------------------------------------------------------
# ---------------ALIEN INVASION MODEL ------------------
# ------------------------------------------------------
class AlienInvasionModel(Model):
  def __init__(self, width=8, height=6, players=4):
      super().__init__()
      self.grid = MultiGrid(width, height, torus=False)
      self.schedule = BaseScheduler(self)
      self.datacollector = DataCollector()
      self.gameWon = False
      self.gameLost = False
      self.damage = 0
      self.POI = 3
      self.victims = 10
      self.saved_victims = 0
      self.lost_victims = 0
      self.false_alarms = 5
      self.ambulance = [(5, 0), (0, 2), (2, 5), (7, 3)]
      self.width=width
      self.height=height
      self.cell_state = [[0,0,0,0,1,0],
                         [0,4,4,0,0,0],
                         [0,4,4,0,0,0],
                         [0,1,4,4,0,0],
                         [0,0,4,0,0,0],
                         [0,0,0,0,4,4],
                         [0,0,0,0,4,0],
                         [0,0,0,0,1,0]
                        ]
          # 0 - Nada
          # 1 - POI
          # 2 - POI en Hole
          # 3 - Hole - Humo
          # 4 - Alien - Fuego
          # 5 - Victima
          # 6 - Victima en Hole
      self.cell_walls = [[[2, 0, 0, 2],[0, 0, 0, 2],[0, 0, 0, 4],[0, 0, 2, 2],[2, 0, 0, 2],[0, 0, 2, 2]],
                         [[2, 0, 0, 0],[0, 0, 0, 0],[0, 3, 0, 0],[0, 2, 2, 0],[2, 0, 0, 0],[0, 0, 2, 0]],
                         [[2, 3, 0, 0],[0, 2, 2, 0],[2, 0, 0, 3],[0, 0, 2, 2],[2, 0, 0, 0],[0, 0, 3, 0]],
                         [[2, 0, 0, 3],[0, 0, 2, 2],[2, 0, 0, 0],[0, 0, 3, 0],[3, 0, 0, 0],[0, 0, 2, 0]],
                         [[2, 2, 0, 0],[0, 3, 2, 0],[2, 0, 0, 0],[0, 0, 2, 0],[2, 2, 0, 0],[0, 3, 2, 0]],
                         [[4, 0, 0, 2],[0, 0, 2, 3],[2, 2, 0, 0],[0, 3, 2, 0],[2, 0, 0, 2],[0, 0, 2, 3]],
                         [[2, 0, 0, 0],[0, 0, 2, 0],[2, 0, 0, 2],[0, 0, 2, 3],[2, 2, 0, 0],[0, 3, 2, 0]],
                         [[2, 2, 0, 0],[0, 2, 3, 0],[3, 2, 0, 0],[0, 4, 2, 0],[2, 2, 0, 2],[0, 2, 2, 3]]
                         ]
          # 0 - Nada
          # 1 - Pared con daño
          # 2 - Pared
          # 3 - Puerta cerrada
          # 4 - Puerta abierta

      self.datacollector = DataCollector(
            model_reporters={"Grid":get_grid,
                             "Steps":lambda model : model.steps,
                             "POIs": lambda model : model.POI})
      for i in range (players):
          # astronauta
          agent = AstronautAgent(self, i)
          self.grid.place_agent(agent, self.ambulance[i % 4])
          self.schedule.add(agent)

  def set_state(self, x, y, state):
    self.cell_state[x][y] = state

  def set_wall(self, x, y, z, wall):
    self.cell_walls[x][y][z] = wall

  def decrease_POI(self):
    self.POI -= 1

  def set_victims(self):
    self.victims -= 1

  def save_victim(self):
    self.saved_victims += 1

  def lose_victim(self):
    self.lost_victims += 1

  def increase_damage(self, points):
    self.damage += points

  def false_alarm(self, x, y):
    if self.cell_state[x][y] == 2:
      self.set_state(x, y, 3)
    if self.cell_state[x][y] == 1:
      self.set_state(x, y, 0)
    print("false alarm")

  def reveal_POI(self, pos):
      x, y = pos
      vict  = False
      if self.victims > 0 and self.false_alarms > 0:
        vict = bool(random.getrandbits(1))
      elif self.victims > 0:
        vict = True
      if vict == False:
        self.false_alarms -= 1
        self.false_alarm(x, y)
        self.POI -= 1
        print("reveal decrease", pos)
      return vict

  def replenish_POI(self):
    while self.POI < 3:
      x = random.randint(0, 7)
      y = random.randint(0, 5)
      position = (x, y)
      if self.cell_state[x][y] in (0, 3, 4):
        if not(self.grid.is_cell_empty(position)):
          vict = self.reveal_POI(position)
          print("- reveal replenish", position)
          if vict == True:
            agents = self.grid.get_cell_list_contents(position)
            self.agents[0].aux_reveal_POI(position)
        else:
          self.cell_state[x][y] = 1
        self.POI += 1
        for i in self.ambulance:
          agents = self.grid.get_cell_list_contents(i)
          for j in agents:
            pos = j.pos
            if pos == i and i == position:
              self.save_victim()
              self.cell_state[x][y] = 0
              print("saved by spawn")
        print("replenish increase", position)

  def eliminate_POI(self, pos):
    x, y = pos
    if self.cell_state[x][y] == 5:
      self.cell_state[x][y] = 0
    elif self.cell_state[x][y] == 6:
      self.cell_state[x][y] = 3

#problema
  def invasionRemains(self, pos, state):
    agents = self.grid.get_cell_list_contents(pos)
    for agent in agents:
      agent.knockedDown()
    x, y = pos
    vict = False
    if state in (1, 2):
      vict = self.reveal_POI(pos)
      self.cell_state[x][y] = 4
      print("- reveal remains", pos)
    if state in (5, 6) or vict == True:
      self.eliminate_POI(pos)
      self.lost_victims += 1
      self.POI -= 1
      self.cell_state[x][y] = 4
      print("remains decrease (5, 6)")
    self.cell_state[x][y] = 4

  def advanceInvasion(self):
    mapX = np.random.randint(0,7)
    mapY = np.random.randint(0,5)
    self.advanceInvasionAux(mapX,mapY,3)

  def enviroment_update(self):
    new_state = np.copy(self.cell_state)
    for x in range(self.width):
      for y in range(self.height):
        vecinos = []
        if x > 0 and self.cell_walls[x-1][y][3] in (1, 2, 4):
            vecinos.append(self.cell_state[x-1][y])
        if x < self.width-1 and self.cell_walls[x+1][y][1] in (1, 2, 4):
            vecinos.append(self.cell_state[x+1][y])
        if y > 0 and self.cell_walls[x][y-1][2] in (1, 2, 4):
            vecinos.append(self.cell_state[x][y-1])
        if y < self.height-1 and self.cell_walls[x][y+1][0] in (1, 2, 4):
            vecinos.append(self.cell_state[x][y+1])

        if self.cell_state[x][y] in (2, 3, 6): # ver que pasa con POI si se vuelve en alien ese hole
            if 4 in vecinos:
                state = self.cell_state[x][y]
                new_state[x][y] = 4 # soy hole y hay un alien = alien
                pos = (x, y)
                self.invasionRemains(pos, state)
                print("environment update")


    self.cell_state = new_state

  def step(self):
      self.datacollector.collect(self)
      self.schedule.step()


  def advanceInvasionAux(self, x, y, state):
      # Determinar mi estado
      if self.cell_state[x][y] == 0:
          self.cell_state[x][y] = state

      # hole + hole  = alien
      elif self.cell_state[x][y] in (2, 3, 6):
          state = self.cell_state[x][y]
          self.cell_state[x][y] = 4
          pos = (x, y)
          self.invasionRemains(pos, state)
          print("advace Invasion Aux")

      elif state == 3:
          # POI + hole
          if self.cell_state[x][y] == 1:
            self.cell_state[x][y] = 2

          # Victima + hole
          elif self.cell_state[x][y] == 5:
            self.cell_state[x][y] = 6

          # alien + hole = invasion
          elif self.cell_state[x][y] == 4:
              self.invasion(x, y)

  def invasion(self, x, y):
      vecinos = []

      if x > 0 and self.cell_walls[x-1][y][3] in (1, 2, 4):
          vecinos.append((x-1, y))
      if x < self.width-1 and self.cell_walls[x+1][y][1] in (1, 2, 4):
          vecinos.append((x+1, y))
      if y > 0 and self.cell_walls[x][y-1][2] in (1, 2, 4):
          vecinos.append((x, y-1))
      if y < self.height-1 and self.cell_walls[x][y+1][0] in (1, 2, 4):
          vecinos.append((x, y+1))

      for adjX, adjY in vecinos:
          if self.cell_state[adjX][adjY] == 4:
                self.shockwave(adjX, adjY, x, y) # shockwave
          elif self.cell_state[adjX][adjY] in (0, 1, 2, 3, 5, 6):  # ver que pasa con POI
            if self.cell_state[adjX][adjY] in (1, 2, 5, 6):
              state = self.cell_state[adjX][adjY]
              pos = (adjX, adjY)
              self.invasionRemains(pos, state)
              print("invasion")
            self.cell_state[adjX][adjY] = 4   # alien



  def endGameWin(self):
    if (self.saved_victims == 7):
      self.gameWon = True
  def endGameLoose(self):
    if(self.lost_victims >= 4 or self.damage >= 24):
       self.gameLost = True
  def shockwave(self, x, y, selfx, selfy):

    move = 0

    if self.cell_state[x][y] == 4: # Si ya hay alien
        next_x = x + (x - selfx)
        next_y = y + (y - selfy)

        # Determinar hacia donde esta avanzando
        if x > selfx:
            move = 3
        elif x < selfx:
            move = 1
        elif y > selfy:
            move = 2
        elif y < selfy:
            move = 1

        # Cuando topa con pared
        if self.cell_walls[x][y][move] == 2 or self.cell_walls[x][y][move] == 1:
            self.cell_walls[x][y][move] -= 1
            self.damage += 1
            return

        # Cuando topa con puerta cerrado
        elif self.cell_walls[x][y][move] == 3:
            self.cell_walls[x][y][move] == 0
            return

        # Si no continua
        if 0 <= next_x < 8 and 0 <= next_y < 6:
          self.shockwave(next_x, next_y, x, y)
    # Si es vacío o hay hole = alien
    elif self.cell_state[x][y] in (0, 2, 3, 6): # ver que pasa con POI:
        state = self.cell_state[x][y]
        self.cell_state[x][y] = 4
        pos = (x, y)
        self.invasionRemains(pos, state)
        print("shockwave")
        return

# ------------------------------------------------------
# ---------------Get Sim Data ------------------
# ------------------------------------------------------

def get_sim_data(model):
   model_data ={
      "saved_victims": model.saved_victims,
      "lost_victims": model.lost_victims,
      "damage_counters": model.damage,
      "steps": model.steps,
      "lost": model.gameLost,
      "won": model.gameWon
   }
   
   data_per_agent = []
   for agent in model.schedule.agents:
          data_per_agent.append({
              "id": agent.unique_id,
              "x": agent.pos[0],
              "y": agent.pos[1], 
              "action_points": agent.action_points,
              "carrying_victim": agent.carrying_victim
          })
   return {"model_data": model_data, "agents": data_per_agent}