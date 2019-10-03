import pygame as pg
import numpy as np
import sys
import logging as lg


def logistic(x):
	return 1 / (1. + 2.71828 ** (-x))

def norm(v):
	return ((v**2).sum())**.5

def distance(p1, p2):
	return norm(p1 - p2)


class Game:
	def __init__(self, 
		verbose = False,
		fps = 60,
		screen_shape = (400,300),
		bgcolor = (30,30,30),
		):
		self.verbose = verbose
		self.fps = fps
		self.screen_shape = screen_shape
		self.bgcolor = bgcolor
		self.to_quit = False

	def setup(self):
		pass

	def draw(self, screen):
		screen.fill(self.bgcolor)
		self.state.draw(screen, self.screen_shape)

	def process_event(self, event):
		if event.type == pg.QUIT:
			self.quit()
		elif event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				self.quit()
		else:
			self.state.process_event(event)

	def get_input_data(self):
		# Examples of stuff to put here:
		# pressed = pg.key.get_pressed()
		# mouse_pressed = pg.mouse.get_pressed()
		# mouse_pos = pg.mouse.get_pos()
		return None

	def quit(self):
		lg.info("Quitting game...")
		lg.info("Quitting game...")
		pg.display.quit()
		lg.info("Quitting game 2...")
		pg.quit()
		lg.info("Quitting game 3...")
		self.to_quit = True

	def run(self, render=True):
		self.setup()

		self.clock = pg.time.Clock()
		pg.init()
		if render: self.screen = pg.display.set_mode(self.screen_shape)
		to_quit = False

		while True:
			try:
				lg.debug("Main loop processing events...")
				for event in pg.event.get():
					self.process_event(event)
					if self.to_quit: return

				lg.debug("Main loop updating game state...")
				input_data = self.get_input_data()
				self.state.update(input_data)
				if self.to_quit: return

				lg.debug("Main loop drawing game...")
				if render: self.draw(self.screen)
				if render: pg.display.flip()

				self.clock.tick(self.fps)
			except KeyboardInterrupt as e:
				lg.info("KeyboardInterrupt encountered")
				self.quit()
				return


class GameState:
	def __init__(self, game):
		self.game = game

	def draw(self, screen, screen_shape=None):
		pass

	def update(self, input_data):
		pass

	def process_event(self, event):
		pass


class ObjectCollection:
	"""Group of objects; each updates on its own (using game state), and draws itself."""
	object_type = None # override
	def __init__(self, game, num_objects=10):
		self.game = game
		self.objects = [self.make_object() for i in xrange(num_objects)]
		self.objects_to_add = []
		self.objects_to_remove = []
	
	def make_object(self):
		return self.object_type(self.game)

	def __getitem__(self, idx):
		return self.objects[idx]

	def process_additions_deletions(self):
		for obj in self.objects_to_add:
			self.objects.append(obj)
		for obj in self.objects_to_remove:
			self.objects.remove(obj)
		self.objects_to_add = []
		self.objects_to_remove = []
	def queue_add_object(self, obj):
		self.objects_to_add.append(obj)
	def queue_remove_object(self, obj):
		self.objects_to_remove.append(obj)

	def update(self, input_data, game_state):
		self.process_additions_deletions()
		for obj in self.objects:
			obj.update(input_data, game_state)

	def draw(self, screen):
		self.process_additions_deletions()
		for obj in self.objects:
			obj.draw(screen)


class ObjectCollectionGameState(GameState):
	"""State of a game where only an ObjectCollection exists, nothing else."""
	object_collection_class = ObjectCollection
	def __init__(self, game, num_objects=10):
		self.object_collection = self.object_collection_class(game, num_objects)
		self.game = game
		self.screen_shape = game.screen_shape

	def update(self, input_data):
		self.object_collection.update(input_data, self)

	def draw(self, screen, screen_shape):
		self.object_collection.draw(screen)


class PositionedObject:
	def __init__(self, pos, screen_shape):
		if pos is None:
			pos = screen_shape * np.random.random(2)
		self.pos = pos

	def draw(self, screen):
		pass

	def update(self, input_data, game_state):
		pass


class PixelObject(PositionedObject):
	default_color = (255,255,255)
	def __init__(self, pos, screen_shape, color=None):
		if color is None: color = self.default_color
		if pos is None:
			pos = np.random.random(2) * screen_shape
		self.pos = pos
		self.color = color

	def draw(self, screen):
		assert type(self.pos) == np.ndarray
		assert self.pos.shape == (2,)
		screen.set_at(map(int, self.pos), self.color)

	def update(self, input_data, game_state):
		pass


class NewtonianPixel(PixelObject):
	default_color = (255,255,255)
	def __init__(self, game, pos = None, color = None, velocity = None):
		if pos is None:
			pos = game.screen_shape * np.random.random(2)
		self.pos = pos

		if color is None: color = self.default_color
		self.color = color

		if velocity is None:
			velocity = np.zeros(2)
		self.velocity = velocity

	def update(self, input_data, game_state):
		self.update_velocity(input_data, game_state)
		self.apply_velocity()
		self.control_bounding(game_state.screen_shape)
	
	def control_bounding(self, screen_shape):
		pass

	def apply_velocity(self):
		self.pos += self.velocity
	
	def update_velocity(self, input_data, game_state):
		pass

	def distance_to(self, other, game_state):
		return distance(self.pos, other.pos)


class BlockedNewtonianPixel(NewtonianPixel):
	# NewtonianPixel that's blocked at the boundaries of the screen
	def control_bounding(self, screen_shape):
		self.velocity[self.pos < np.zeros(2)] = 0.
		self.pos[self.pos < np.zeros(2)] = 0.

		self.velocity[self.pos > screen_shape] = 0.
		self.pos[self.pos > screen_shape] = screen_shape[self.pos > screen_shape] - 1


class WraparoundNewtonianPixel(NewtonianPixel):
	# NewtonianPixel that wraps around at the boundaries of the screen

	def control_bounding(self, screen_shape):
		if not (0 <= self.pos[0] < screen_shape[0]):
			self.pos = np.asarray((self.pos[0] % screen_shape[0], self.pos[1]))
		if not (0 <= self.pos[1] < screen_shape[1]):
			self.pos = np.asarray((self.pos[0], self.pos[1] % screen_shape[1]))

	def wraparound_distance_to(self, other, game_state):
		x_changes = (0, +1 if self.pos[0] > game_state.screen_shape[0]/2 else -1)
		y_changes = (0, +1 if self.pos[1] > game_state.screen_shape[1]/2 else -1)
		shortest_distance = float('inf')
		for x_change in x_changes:
			for y_change in y_changes:
				other_pos = other.pos + np.asarray((x_change, y_change)) * game_state.screen_shape
				dist = distance(other_pos, self.pos)
				if dist < shortest_distance:
					shortest_distance = dist
		return shortest_distance
	distance_to = wraparound_distance_to


