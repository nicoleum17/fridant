from mesa import Agent, Model

from mesa.space import MultiGrid

from mesa.time import RandomActivation

from mesa.time import BaseScheduler

from mesa.datacollection import DataCollector

from mesa.batchrunner import batch_run

import matplotlib
import matplotlib.lines as plt
import random
import numpy as np
import pandas as pd
import seaborn as sns
sns.set()

import time
import datetime

import heapq

%matplotlib inline
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128



#-----------------------------------------------------------
#--------------------Clase Astronauta ----------------------
#-----------------------------------------------------------
class PriorityQueue:
    def __init__(self):
        self.__data = []

    # Función para verificar si la fila de prioridades está vacía
    def empty(self):
        return not self.__data

    # Función para limpiar la fila de prioridades
    def clear(self):
        self.__data.clear()

    # Función para insertar un elemento en la fila de prioridades
    def push(self, priority, value):
        heapq.heappush(self.__data, (priority, value))

    # Función para extraer el elemento con mayor prioridad (menor número)
    def pop(self):
        if self.__data: # not empty
            heapq.heappop(self.__data)
        else:
            raise Exception("No such element")

    # Función para obtener el primer elemento sin sacarlo
    def top(self):
        if self.__data: # not empty
            return self.__data[0]
        else:
            raise Exception("No such element")
        



def heuristics(src, dest):
    # Implementa una heurística aquí. Aquí usamos una heurística simple
    # (distancia Manhattan)
    return (abs(src[0] - dest[0]) + abs(src[1] - dest[1])) * 5


def to_int(matrix, position):
    (row, col) = position
    rows = len(matrix)
    cols = len(matrix[0])
    return (row * cols) + col


def is_valid(matrix, position):
    (row, col) = position
    rows = len(matrix)
    cols = len(matrix[0])
    return 0 <= row < rows and 0 <= col < cols

def get_neighborhood(matrix, position):
    result = []

    (ren, col) = position

    new_position = ((ren - 1), col)
    if is_valid(matrix, new_position):
        result.append(new_position)

    new_position = ((ren + 1), col)
    if is_valid(matrix, new_position):
        result.append(new_position)

    new_position = (ren, (col - 1))
    if is_valid(matrix, new_position):
        result.append(new_position)

    new_position = (ren, (col + 1))
    if is_valid(matrix, new_position):
        result.append(new_position)

    return result


class AstronautAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.action_points = 4
        self.carrying_victim = False

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

    def aux_reveal_POI(self, pos):
      x, y = pos
      if self.carrying_victim == False:
        if self.model.cell_state[x][y] == 1:
          self.model.cell_state[x][y] = 0
        else:
          self.model.cell_state[x][y] = 3
        self.model.victims -= 1
        self.carrying_victim = True
      else:
        if self.model.cell_state[x][y] == 1:
          self.model.cell_state[x][y] = 5
        else:
          self.model.cell_state[x][y] = 6
        self.model.victims -= 1

    def knockedDown(self):
      x, y = self.pos
      nearest_ambulance = self.model.ambulance[0]
      min_distance = abs(x - nearest_ambulance[0]) + abs(y - nearest_ambulance[1])
      if self.carrying_victim == True:
        self.carrying_victim = False
        self.model.lose_victim()
        self.model.decrease_POI()
      for ambulance_pos in self.model.ambulance:
          dist = abs(x - ambulance_pos[0]) + abs(y - ambulance_pos[1])
          if dist < min_distance:
              min_distance = dist
              nearest_ambulance = ambulance_pos
      self.model.grid.move_agent(self, nearest_ambulance)

    def carry_victim(self):
      x, y = self.pos
      if self.model.cell_state[x][y] == 5:
        self.model.cell_state[x][y] = 0
      elif self.model.cell_state[x][y] == 6:
        self.model.cell_state[x][y] = 3
      self.carrying_victim = True

    def a_star(self, matrix, src, dest):
      INFINITE = 1_000_000
      n = len(matrix) * len(matrix[0])
      dist = [INFINITE] * n
      prev = [None] * n
      pq = PriorityQueue()
      steps = 0

      dist[to_int(matrix, src)] = 0
      pq.push(0, src)
      while not pq.empty():
          current_dist, u = pq.top()
          pq.pop()

          # Si hemos llegado al destino, podemos salir del ciclo
          if u == dest:
              break

          for v in get_neighborhood(matrix, u):
              (row, col) = v
              if matrix[row][col] != -1:
                  z, a = self.relative_position(u)
                  new_dist = dist[to_int(matrix, u)] + matrix[row][col][z]

                  if new_dist < dist[to_int(matrix, v)]:
                      dist[to_int(matrix, v)] = new_dist
                      prev[to_int(matrix, v)] = u
                      priority = new_dist + heuristics(v, dest)
                      pq.push(priority, v)

          steps += 1

      # Reconstruir el camino
      path = []
      u = dest
      if prev[to_int(matrix, u)] is not None or u == src:
          while u is not None:
              path.insert(0, u)
              u = prev[to_int(matrix, u)]

      return dist[to_int(matrix, dest)], path

    def better_route(self, interest_points):
        distances = []
        paths = []

        for i in range(len(interest_points) - 1):
            dist, path = self.a_star(self.model.costs, self.pos, interest_points[i])
            distances.append(dist)
            paths.append(path)
        min_distance = min(distances)
        min_index = distances.index(min_distance)
        paths[min_index].pop(0)
        return paths[min_index]

    def wall_damage(self, x, y, z, nx, ny, nz):
        self.model.cell_walls[nx][ny][nz] -= 1
        self.model.cell_walls[x][y][z] -= 1
        self.action_points -= 2

        self.model.adjust_costs(nx, ny, nz)
        self.model.adjust_costs(x, y, z)

    def break_wall(self, x, y, z, nx, ny, nz):
        self.model.cell_walls[nx][ny][nz] = 0
        self.model.cell_walls[x][y][z] = 0
        self.action_points -= 4

        self.model.adjust_costs(nx, ny, nz)
        self.model.adjust_costs(x, y, z)

    def open_door(self, x, y, z, nx, ny, nz):
        self.model.cell_walls[nx][ny][nz] = 4
        self.model.cell_walls[x][y][z] = 4
        self.action_points -= 1

        self.model.adjust_costs(nx, ny, nz)
        self.model.adjust_costs(x, y, z)

    def go_forward(self, nx, ny):
        self.model.grid.move_agent(self, (nx, ny))
        self.path.pop(0)
        print(self.path)

        if (self.model.cell_state[nx][ny] == 4 or self.carry_victim == True) and (self.model.cell_state[nx][ny] == 4 and self.carry_victim == True):
            self.action_points -= 2
        else:
            self.action_points -= 1


    def move(self):
        while self.action_points > 0 and self.path:
            coords = self.path[0]
            x, y = self.pos
            nx, ny = coords
            nz, z = self.relative_position(coords)

            cell_type = self.model.cell_walls[nx][ny][nz]
            cost = self.model.costs[nx][ny][nz]

            match cell_type:
                case 0 | 4: # Nada o puerta abierta
                    # Moverse
                    if self.action_points >= cost:
                        self.go_forward(nx, ny)
                    else:
                        return

                case 1: # Pared con daño
                    # Dañar pared y mover
                    if self.action_points >= cost:
                        self.wall_damage(x, y, z, nx, ny, nz)
                        self.go_forward(nx, ny)
                    # Dañar pared
                    elif self.action_points >= 2:
                        self.wall_damage(x, y, z, nx, ny, nz)
                    else:
                        return

                case 2: # Pared
                    # Romper pared y moverse
                    if self.action_points >= cost:
                        self.break_wall(x, y, z, nx, ny, nz)
                        self.go_forward(nx, ny)
                    # Romper pared
                    elif self.action_points >= 4:
                        self.break_wall(x, y, z, nx, ny, nz)
                    # Dañar pared
                    elif self.action_points >= 2:
                        self.wall_damage(x, y, z, nx, ny, nz)
                    else:
                        return

                case 3: # Puerta cerrada
                    # Abrir puerta y moverse
                    if self.action_points >= 1:
                        self.open_door(x, y, z, nx, ny, nz)
                        self.go_forward(nx, ny)
                    # Abrir puerta
                    elif self.action_points >= 1:
                        self.open_door(x, y, z, nx, ny, nz)
                    else:
                        return

    def step(self):
        # Obtener el camino más corto al objetivo
        if self.carrying_victim:
            self.path = self.better_route(self.model.ambulance)
        else:
            self.path = self.better_route(self.model.cord_POIs)

        self.move()

        x, y = self.pos

        # Si encuentra un POI
        if self.model.cell_state[x][y] in (1, 2):
            vict = self.model.reveal_POI(self.pos)
            self.aux_reveal_POI(self.pos)

        else:
            for amb in self.model.ambulance:
                # Si llego a la ambulancia
                if amb == self.pos and self.carrying_victim == True:
                    self.carrying_victim = False
                    self.model.save_victim()
        print(self.action_points)

        # Recargar action points
        self.action_points += 4
        if self.action_points > 8:
            self.action_points = 8

        # Modelo
        self.model.advanceInvasion()
        self.model.enviroment_update()
        self.model.replenish_POI()
        print(self.action_points)
        print(" ")



#---------------------------------------------------------
#-----------Get grid (solo simulacion en notebook)--------
#---------------------------------------------------------
def get_grid(model):
  grid = np.zeros( (model.grid.width, model.grid.height) )
  for content, (x,y) in model.grid.coord_iter():
    grid[x][y] = model.cell_state[x][y]
    if len(content) != 0:
      grid[x][y] = len(content) + 6
  return grid



#-------------------------------------------------------
#----------------ALien Invasion model-------------------
#-------------------------------------------------------
class AlienInvasionModel(Model):
  def __init__(self, width=8, height=6, players=4):
      super().__init__()
      self.grid = MultiGrid(width, height, torus=False)
      self.schedule = BaseScheduler(self)
      self.datacollector = DataCollector()
      self.damage = 0
      self.POI = 3
      self.victims = 10
      self.saved_victims = 0
      self.lost_victims = 0
      self.false_alarms = 5
      self.ambulance = [(0, 3), (2, 0), (5, 5), (7, 2)]
      self.width=width
      self.height=height
      self.cord_POIs = [(0, 1), (7, 1), (3, 4)]
      self.lostGame = False
      self.winGame = False

      self.cell_state = [[0,1,0,0,0,0],
                         [0,0,0,4,4,0],
                         [0,0,0,4,4,0],
                         [0,0,4,4,1,0],
                         [0,0,0,4,0,0],
                         [4,4,0,0,0,0],
                         [0,4,0,0,0,0],
                         [0,1,0,0,0,0]
                        ]

          # 0 - Nada
          # 1 - POI
          # 2 - POI en Hole
          # 3 - Hole - Humo
          # 4 - Alien - Fuego
          # 5 - Victima
          # 6 - Victima en Hole

      self.cell_walls = [[[2, 0, 0, 2],[2, 2, 0, 0],[2, 0, 0, 2],[4, 0, 0, 0],[2, 0, 0, 0],[2, 2, 0, 0]],
                         [[0, 0, 0, 2],[0, 2, 0, 0],[0, 0, 2, 2],[0, 0, 3, 0],[0, 0, 0, 0],[0, 2, 0, 0]],
                         [[0, 0, 0, 4],[0, 2, 0, 0],[2, 0, 0, 2],[3, 2, 0, 0],[0, 0, 2, 2],[0, 2, 3, 0]],
                         [[0, 0, 0, 2],[0, 3, 0, 0],[0, 0, 0, 3],[0, 2, 0, 0],[2, 0, 0, 2],[3, 2, 0, 0]],
                         [[0, 0, 3, 2],[0, 2, 2, 0],[0, 0, 0, 2],[0, 2, 0, 0],[0, 0, 3, 2],[0, 2, 2, 0]],
                         [[3, 0, 0, 2],[2, 2, 0, 0],[0, 0, 3, 2],[0, 2, 2, 0],[3, 0, 0, 2],[2, 4, 0, 0]],
                         [[0, 0, 3, 2],[0, 2, 2, 0],[3, 0, 0, 2],[2, 2, 0, 0],[0, 0, 0, 2],[0, 2, 0, 0]],
                         [[3, 0, 2, 2],[2, 2, 2, 0],[0, 0, 4, 2],[0, 4, 2, 0],[0, 0, 2, 4],[0, 2, 2, 0]]
                         ]

          # 0 - Nada
          # 1 - Pared con daño
          # 2 - Pared
          # 3 - Puerta cerrada
          # 4 - Puerta abierta

      self.costs = [[[5, 1, 1, 5],[1, 1, 1, 5],[1, 1, 1, 1],[1, 1, 5, 5],[5, 1, 1, 5],[1, 1, 5, 5]],
                    [[5, 1, 1, 1],[2, 2, 2, 2],[2, 3, 2, 2],[1, 5, 5, 1],[5, 1, 1, 1],[1, 1, 5, 1]],
                    [[5, 1, 1, 1],[2, 6, 6, 2],[6, 2, 2, 3],[1, 1, 5, 5],[5, 1, 1, 1],[1, 1, 2, 1]],
                    [[5, 1, 1, 2],[1, 1, 5, 5],[6, 2, 2, 2],[2, 2, 3, 2],[2, 1, 1, 1],[1, 1, 5, 1]],
                    [[5, 5, 1, 1],[1, 2, 5, 1],[6, 2, 2, 2],[1, 1, 5, 1],[5, 5, 1, 1],[1, 2, 5, 1]],
                    [[1, 1, 1, 5],[1, 1, 5, 2],[5, 5, 1, 1],[1, 2, 5, 1],[6, 2, 2, 6],[2, 2, 6, 3]],
                    [[5, 1, 1, 1],[1, 1, 5, 1],[5, 1, 1, 5],[1, 1, 5, 2],[6, 6, 2, 2],[1, 2, 5, 1]],
                    [[5, 5, 1, 1],[1, 5, 2, 1],[2, 5, 1, 1],[1, 1, 5, 1],[1, 5, 1, 5],[1, 5, 5, 2]]
                    ]

      self.datacollector = DataCollector(
        model_reporters={
            "Grid": get_grid,
            "Steps": lambda model: model.steps,
            "POIs": lambda model: model.POI,
            "Victoria": lambda model: model.endGameWin(),
            "Derrota": lambda model: model.endGameLoose(),
            "Victimas_Salvadas": lambda model: model.saved_victims,
            "Victimas_Perdidas": lambda model: model.lost_victims,
            "Dmg": lambda model: model.damage,
        }
    )

      for i in range (players):
          # astronauta
          agent = AstronautAgent(self)
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

  def adjust_costs(self, x, y, z):
    return 0
    if z == -1:
      for i in range(4):
        self.costs[x][y] -= 1
    elif z == -2:
      for i in range(4):
        self.costs[x][y] += 1
    elif z >= 0:
      if self.cel_state[x][y] == 4:
        self.costs[x][y][z] == 2
      else:
        self.costs[x][y][z] == 1
      if self.cell_walls[x][y][z] in (0, 4):
        self.costs[x][y][z] += 0
      elif self.cell_walls[x][y][z] in (1, 3):
        self.costs[x][y][z] += 2
      else:
        self.costs[x][y][z] += 4



  def false_alarm(self, x, y):
    if self.cell_state[x][y] == 2:
      self.cell_state[x][y] = 3
    if self.cell_state[x][y] == 1:
      self.cell_state[x][y] = 0

  def reveal_POI(self, pos):
      x, y = pos
      vict  = False
      if self.victims > 0 and self.false_alarms > 0:
        if random.randint(0, 2) in (0, 1):
          vict = True
      elif self.victims > 0:
        vict = True
      if vict == False:
        self.false_alarms -= 1
        self.false_alarm(x, y)
        self.POI -= 1
      return vict

  def replenish_POI(self):
    while self.POI < 3:
      x = random.randint(0, 7)
      y = random.randint(0, 5)
      position = (x, y)
      if self.cell_state[x][y] in (0, 3, 4):
        if not(self.grid.is_cell_empty(position)):
          vict = self.reveal_POI(position)
          if vict == True:
            agents = self.grid.get_cell_list_contents(position)
            self.agents[0].aux_reveal_POI(position)
        else:
          if self.cell_state[x][y] == 4:
            self.adjust_costs(x, y, -1) # de alien a nada
          self.cell_state[x][y] = 1
        self.POI += 1
        for i in self.ambulance:
          agents = self.grid.get_cell_list_contents(i)
          for j in agents:
            pos = j.pos
            if pos == i and i == position:
              self.save_victim()
              if self.cell_state[x][y] == 4:
                self.adjust_costs(x, y, -1) # de alien a nada
              self.cell_state[x][y] = 0

  def eliminate_POI(self, pos):
    x, y = pos
    if self.cell_state[x][y] == 5:
      self.cell_state[x][y] = 0
    elif self.cell_state[x][y] == 6:
      self.cell_state[x][y] = 3

  def invasionRemains(self, pos, state):
    agents = self.grid.get_cell_list_contents(pos)
    for agent in agents:
      agent.knockedDown()
    x, y = pos
    vict = False
    if state in (1, 2):
      vict = self.reveal_POI(pos)
      self.cell_state[x][y] = 4
      self.adjust_costs(x, y, -2) # de nada a alien
    if state in (5, 6) or vict == True:
      self.eliminate_POI(pos)
      self.lost_victims += 1
      self.POI -= 1
      self.cell_state[x][y] = 4
      self.adjust_costs(x, y, -2) # de nada a alien

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
                self.adjust_costs(x, y, -2) # de nada a alien
                pos = (x, y)
                self.invasionRemains(pos, state)

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
          self.adjust_costs(x, y, -2) # de nada a alien
          pos = (x, y)
          self.invasionRemains(pos, state)

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
            self.cell_state[adjX][adjY] = 4   # alien
            self.adjust_costs(x, y, -2) # de nada a alien


  def endGameWin(self):
    return (self.saved_victims == 7 and self.lostGame == False)
  def endGameLoose(self):
    return ((self.lost_victims >= 4 or self.damage >= 24) and self.winGame == False)


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
            self.adjust_costs(x, y, move)
            self.damage += 1
            return

        # Cuando topa con puerta cerrado
        elif self.cell_walls[x][y][move] == 3:
            self.cell_walls[x][y][move] = 0
            self.adjust_costs(x, y, move)
            return

        # Si no continua
        if 0 <= next_x < 8 and 0 <= next_y < 6:
          self.shockwave(next_x, next_y, x, y)
    # Si es vacío o hay hole = alien
    elif self.cell_state[x][y] in (0, 2, 3, 6): # ver que pasa con POI:
        state = self.cell_state[x][y]
        self.cell_state[x][y] = 4
        self.adjust_costs(x, y, -2)
        pos = (x, y)
        self.invasionRemains(pos, state)
        return