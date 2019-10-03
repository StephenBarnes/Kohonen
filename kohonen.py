from pygame_framework import *
import math
import numpy as np


SCREEN_SHAPE = np.asarray((800, 800))


MOVEMENT_RATE = .03
NEIGHBOR_NARROWNESS = 10
MAX_REPULSION = 0.05
LATTICE_SIDE = 25

NODE_CIRC_RADIUS = 2
LINE_COLOR = (150, 150, 150)
HIGHLIGHT_COLOR = (255, 0, 0)

RANDOM_PRESS_RATE = 15


class KohonenNetwork:
	def __init__(self, num_objects, initial_node_generator):
		self.nodes = [initial_node_generator() for i in xrange(num_objects)]
		self.highlighted_node = None

	def find_closest(self, new_point):
		shortest_dist = float('inf')
		closest_node = None
		for node in self.nodes:
			dist = node.center_distance(new_point)
			if dist < shortest_dist:
				shortest_dist = dist
				closest_node = node
		assert closest_node is not None
		return shortest_dist, closest_node

	def move_winner_region(self, new_point, winning_node):
		for node in self.nodes:
			lattice_dist = node.lattice_distance(winning_node)
			weight = self.movement_weight(lattice_dist)
			#print "Moving node-center at %s with weight %s" % (node.center.pos, weight)
			node.center.move_towards(new_point, weight)
	
	def movement_weight(self, lattice_dist):
		# Should be between 1 and 0; probably between like 0.1 and 0
		# Should decrease as lattice_dist increases

		# One option is to use decaying exponential:
		#return math.exp(-lattice_dist * NEIGHBOR_NARROWNESS) * MOVEMENT_RATE
		# Another option is Gaussian:
		#return math.exp(-(lattice_dist**2) * NEIGHBOR_NARROWNESS) * MOVEMENT_RATE
		# Another option is Gaussian plus negative movement for faraway stuff
		return (math.exp(-(lattice_dist**2) * NEIGHBOR_NARROWNESS) - MAX_REPULSION) * MOVEMENT_RATE / (1 - MAX_REPULSION)

	def learn_point(self, new_point):
		shortest_dist, closest_node = self.find_closest(new_point)
		self.highlighted_node = closest_node
		self.move_winner_region(new_point, closest_node)
	
	def draw(self, screen):
		raise NotImplementedError


class KohonenNode:
	def __init__(self, center, lattice_pos):
		self.center = center
		self.lattice_pos = lattice_pos

	def center_distance(self, point):
		return self.center.distance(point)

	def lattice_distance(self, other_node):
		return self.lattice_pos.distance(other_node.lattice_pos)

	def draw(self, screen):
		raise NotImplementedError


class KohonenNode2DTo2D(KohonenNode):
	color = (255,255,255)
	def draw(self, screen, color=None):
		if color is None:
			color = self.color
		pg.draw.circle(screen, color, map(int, self.center.pos * SCREEN_SHAPE), NODE_CIRC_RADIUS)


class KohonenNetwork2DTo2D(KohonenNetwork):
	def __init__(self, side_length = LATTICE_SIDE):
		self.side_length = side_length
		self.lattice = [] # 2D array of nodes
		self.nodes = [] # same as self.lattice, except flattened
		self.highlighted_node = None
		for x in xrange(side_length):
			self.lattice.append([])
			for y in xrange(side_length):
				new_node = KohonenNode2DTo2D(center = Point2DEuclidean(np.random.random(2)),
					lattice_pos = Point2DEuclidean((x / float(side_length), y / float(side_length))))
				self.lattice[-1].append(new_node)
				self.nodes.append(new_node)
	
	def draw_line_between(self, screen, x, y, x2, y2):
		start_pos = self.lattice[x][y].center.pos * SCREEN_SHAPE
		end_pos = self.lattice[x2][y2].center.pos * SCREEN_SHAPE
		pg.draw.line(screen, LINE_COLOR, start_pos, end_pos, 2)
	
	def draw(self, screen):
		# Draw lines
		for x in xrange(self.side_length - 1):
			for y in xrange(self.side_length):
				self.draw_line_between(screen, x, y, x+1, y)
		for y in xrange(self.side_length - 1):
			for x in xrange(self.side_length):
				self.draw_line_between(screen, x, y, x, y+1)

		# Draw circles
		for x in xrange(self.side_length):
			for y in xrange(self.side_length):
				self.lattice[x][y].draw(screen)
		# Highlight node
		if self.highlighted_node is not None:
			self.highlighted_node.draw(screen, HIGHLIGHT_COLOR)


class Point2DEuclidean:
	def __init__(self, pos):
		self.pos = np.asarray(pos)

	def distance(self, other):
		return (self - other).norm()

	def norm(self):
		return ((self.pos**2).sum())**.5

	def move_towards(self, other, distance):
		displacement = other - self
		movement_direction = displacement / displacement.norm()
		self.pos += movement_direction.pos * distance
	
	def __sub__(self, other):
		return Point2DEuclidean(self.pos - other.pos)
	def __mul__(self, scalar):
		return Point2DEuclidean(self.pos * scalar)
	def __div__(self, scalar):
		return Point2DEuclidean(self.pos / scalar)


class StandardKohonenGameState(GameState):
	def __init__(self, game):
		self.game = game
		self.network = KohonenNetwork2DTo2D(LATTICE_SIDE)

	def draw(self, screen, screen_shape=None):
		self.network.draw(screen)
	
	def make_random_input_point(self):
		# (averaging several points so it's a more interesting distribution than just uniform)
		def generate(n):
			return sum(np.random.random(2) for i in xrange(n)) / n
		return Point2DEuclidean(generate(2))

	def update(self, input_data):
		if input_data[pg.K_r]:
			for i in xrange(RANDOM_PRESS_RATE):
				press_point = self.make_random_input_point()
				print "Simulating press at random position:", tuple(press_point.pos)
				self.learn_point(press_point)

	def learn_point(self, point):
		self.network.learn_point(point)


class StandardKohonenGame(Game):
	def process_event(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			mouse_pos = np.asarray(pg.mouse.get_pos(), "float")
			point = Point2DEuclidean(mouse_pos / SCREEN_SHAPE)
			print "Adding point at", point.pos
			self.state.learn_point(point)
			return False
		elif event.type == pg.QUIT:
			return True
		elif event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				return True
		return False

	def get_input_data(self):
		return pg.key.get_pressed()


game = StandardKohonenGame(screen_shape=SCREEN_SHAPE)
game.state = StandardKohonenGameState(game)
game.run()


