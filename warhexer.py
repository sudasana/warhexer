# -*- coding: UTF-8 -*-

################################################################################
#                                                                              #
#                   WarHexer: Roguelike Epic Fanasty Battles                   #
#                                                                              #
################################################################################

# Built on Python 2.7.3 and libtcod 1.5.1
# Default Resolution: 1800 x 912
# Unit Portraits: 30 x 26 px, shown as 15 x 13 characters

##### Libraries #####
import libtcodpy as libtcod	# roguelike library
import os			# for an SDL window instruction
from math import sqrt, ceil		# math functions
from math import atan2, degrees, pi	# more math functions
from textwrap import wrap	# for breaking up game messages
import shelve   		# for saving and loading
from random import shuffle	# for shuffling lists of items (used in map generation)
#import time			# for animation timing


##### Constants #####
VERSION = '0.1g'		# arbitrary desgination

SCREEN_WIDTH = 166	# width of the game window in characters
SCREEN_HEIGHT = 57	# height "

MAP_WIDTH = 136		# width of map console in characters
MAP_HEIGHT = 70		# height "

BATTLE_CONSOLE_WIDTH = 70	# width of battle window console in characters
BATTLE_CONSOLE_HEIGHT = 18	# height "

CON_WIDTH = 43		# width of info console in characters

TERRAIN_CON_HEIGHT = 4	# height of terrain info window
STAT_CON_HEIGHT = 22	# height of unit stat console
MSG_CON_HEIGHT = 18	# height of message window

UNIT_WIDTH = 11		# width of unit sprite
UNIT_HEIGHT = 7		# height "

LIMIT_FPS = 30		# maximum frames-per-second displayed

# terrain type codes
OPEN_GROUND = 0
FOREST = 1
TOWN = 2
RUINS = 3

OPEN_GROUND_COLOR = libtcod.Color(0, 64, 0)
FOREST_COLOR = libtcod.Color(0, 28, 0)
ROAD_COLOR = libtcod.Color(32, 40, 32)

# Debug flags

FREE_AP = False

# change in hx, hy values for hexes in each direction
DESTHEX = [
		(0, 1),
		(1, 1),
		(1, 0),
		(0, -1),
		(-1, -1),
		(-1, 0)
		]


################################################################################
#####                               Classes                                #####
################################################################################

# player: contains information on a particular player, current roster, items, experience, etc.
#class Player:
#	def __init__(self):
#		pass


# unit type: defines stats and abilities for a given type of unit, each spawned unit bases
# its stats off of its type
class UnitType:
	def __init__(self, stats):
		self.name = stats[0]
		self.civ_num = stats[1]
		self.rating = stats[2]
		self.unit_class = stats[3]
		self.unit_char = stats[4]
		self.melee = stats[5]
		self.ranged = stats[6]
		self.attack_range = stats[7]
		self.defense = stats[8]
		self.skill = stats[9]
		self.morale = stats[10]
		self.columns = stats[11]
		self.portrait_file = stats[12]
		self.special = stats[13]
		self.points_cost = stats[14]
		self.description = stats[15]
		
		# set up max AP based on unit rating and class
		if self.unit_class == 'Artillery':
			self.max_ap = 2
		elif self.unit_class == 'Infantry':
			self.max_ap = 3
		elif self.unit_class == 'Cavalry':
			if self.rating == 'Light':
				self.max_ap = 5
			else:
				self.max_ap = 4


UNIT_CLASS_DEFS = [
	
	# Name, civ_number, rating, type, character, melee, ranged, ranged range, defense,
	# skill, morale, columns, portrait filename, special, points cost, description
	
	# Human Kingdoms
	['Hearthguard', 0, 'Heavy', 'Infantry', 'h', 8, 0, 0, 5, 9, 7, 7, 'human_hearthguard.png', ['Polearms'], 120, 
		'Well-equipped and well-trained elite infantry. They are armed with long halberds that give them an advantage against enemy cavalry.'],
	['Irregulars', 0, 'Light', 'Infantry', 'i', 6, 0, 0, 5, 7, 7, 7, '', ['Shields', 'Mobility'], 100, 
		'Armed with one-handed weapons and shields, often used to harrass enemy forces and protect the flanks of heavier troops.'],
	['Longbowmen', 0, 'Light', 'Infantry', 'a', 0, 7, 5, 4, 9, 7, 7, 'human_longbowmen.png', [], 110,
		'Ranged troops equipped with the highly effective longbow.'],
	['Knights', 0, 'Heavy', 'Cavalry', 'K', 9, 0, 0, 6, 10, 8, 5, 'human_knights.png', ['Shields', 'Charge'], 170, 
		'The elite cavalry of the kingdoms, powerful charge attack and highly motivated.'],
	['Noble Riders', 0, 'Light', 'Cavalry', 'R', 8, 0, 0, 5, 8, 7, 5, '', ['Mobility'], 150, 
		'Younger sons of the noble families often ride to war together, eager to prove their bravery with sword and flail.'],
	
	# Undead Lords
	['Ghouls', 1, 'Heavy', 'Infantry', 'g', 8, 0, 0, 6, 8, 8, 7, 'undead_ghouls.png', ['Polearms'], 110, 'Test'],
	['Skeletal Host', 1, 'Light', 'Infantry', 's', 7, 0, 0, 6, 8, 7, 7, '', ['Shields'], 90, 'Test'],
	['Skeleton Archers', 1, 'Light', 'Infantry', 'a', 0, 6, 5, 4, 8, 7, 7, 'skeleton_archers.png', [], 100, 'Test'],
	['Knightmares', 1, 'Heavy', 'Cavalry', 'K', 8, 0, 0, 7, 8, 8, 5, 'undead_knightmares.png', ['Charge'], 160, 'Test'],
	['Vampire Lords', 1, 'Light', 'Cavalry', 'V', 9, 0, 0, 6, 7, 7, 5, '', ['Shields', 'Mobility'], 140, 'Test']
	]


# battle object, keeps track of everything going on in the battle
class Battle:
	def __init__(self):
		self.map_hexes = []		# hex terrain
		self.rivers = []		# coordinates of rivers (hx1, hy1, hx2, hy2)
		self.roads = []			# coordinates of roads "
		self.units = []			# units in the battle
		self.melee_locks = []		# list of pairs of units locked in melee
		self.messages = []		# list of game messages
		
		self.selected = None		# currently selected unit, if any
		
		self.current_turn = 1		# current battle turn
		self.turn_limit = 8		# at the end of this turn, the battle ends
		self.active_player = 0		# currently active player
		
		self.player0_score = 0		# TEMP: player 1's score
		self.player1_score = 0		# " 2
	
	
	# create a new melee lock between two enemy units
	def CreateMeleeLock(self, obj1, obj2):
		self.melee_locks.append((obj1, obj2))
		
		# update unit flags and their stat consoles
		for obj in [obj1, obj2]:
			obj.melee_locked = True
			obj.ApplyMods()
			obj.UpdateStatConsole()
	
	
	# returns true if the two units share a melee lock
	def IsMeleeLocked(self, obj1, obj2):
		if (obj1, obj2) in self.melee_locks or (obj2, obj1) in self.melee_locks:
			return True
		return False
	
	
	# break any melee locks that this unit is in
	def BreakLocks(self, obj):
		for (obj1, obj2) in self.melee_locks[::-1]:
			if obj1 == obj or obj2 == obj:
				self.melee_locks.remove((obj1, obj2))
				obj1.UpdateStatConsole()
				obj2.UpdateStatConsole()
		
		# reset unit melee lock flags
		for obj in battle.units:
			obj.melee_locked = False
		
		for (obj1, obj2) in self.melee_locks:
			if not obj1.melee_locked:
				obj1.melee_locked = True
				obj1.UpdateStatConsole()
			if not obj2.melee_locked:
				obj2.melee_locked = True
				obj2.UpdateStatConsole()


# session object, holds stuff unique to the gaming session and not saved between games
class Session:
	def __init__(self):
		self.mouseover = (0, 0)		# current mouse position on screen
		
		# create the map console and battle window console
		self.map_console = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
		self.battle_console = libtcod.console_new(BATTLE_CONSOLE_WIDTH, BATTLE_CONSOLE_HEIGHT)
		
		# create terrain console
		self.terrain_con = libtcod.console_new(CON_WIDTH-4, TERRAIN_CON_HEIGHT)
		
		# create message console
		self.msg_con = libtcod.console_new(CON_WIDTH-4, MSG_CON_HEIGHT)
	
	
	# update the terrain console with info from hex
	def UpdateTerrainCon(self, hx, hy):
		libtcod.console_clear(self.terrain_con)
		if not HexIsOnMap(hx, hy):
			return
		h = GetHexFromMap(hx, hy)
		
		text = ''
		if h.landmark_name is not None:
			text += h.landmark_name + ', '
		if h.terrain_type == OPEN_GROUND:
			text += 'Open Ground'
		elif h.terrain_type == FOREST:
			text += 'Forest'
		elif h.terrain_type == TOWN:
			text += 'Town'
		elif h.terrain_type == RUINS:
			text += 'Ruins'
		if h.river:
			text += ', River'
		if h.road:
			text += ', Road'
		
		libtcod.console_print_ex(self.terrain_con, (CON_WIDTH-4)/2, 0, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		text = 'AP Cost: ' + str(h.move_cost)
		libtcod.console_print(self.terrain_con, 0, 2, text)
		
		text = 'Defense: '
		if h.defense_mod == 0:
			text += '-'
		else:
			if h.defense_mod > 0:
				text += '+'
			text += str(h.defense_mod)
		libtcod.console_print_ex(self.terrain_con, CON_WIDTH-5, 2, libtcod.BKGND_NONE, libtcod.RIGHT, text)


	# update the message console with game messages
	# color not used for now
	def UpdateMsgConsole(self):
		libtcod.console_clear(self.msg_con)
		y = 0
		for (line, color) in battle.messages:
			
			# fade out old messages
			s = 255-((len(battle.messages) - y)*13)
			shade = libtcod.Color(s, s, s)
			libtcod.console_set_default_foreground(self.msg_con, shade)
			libtcod.console_print(self.msg_con, 0, y, line)
			y += 1


# records type of terrain in a given hex
class Hex:
	def __init__(self, hx, hy, terrain_type):
		self.hx = hx
		self.hy = hy
		self.road = False			# no road by default
		self.river = False			# no river by default
		self.landmark_name = None		# no landmark name
		self.higher_ground = False		# not higher ground by default
		self.terrain_type = terrain_type	# terrain type code
	
	
	# set hex terrain features
	def SetTerrain(self):
		if self.terrain_type == OPEN_GROUND:
			self.color = OPEN_GROUND_COLOR
			self.move_cost = 1
			self.defense_mod = 0
		elif self.terrain_type == FOREST:
			self.color = FOREST_COLOR
			self.move_cost = 2
			self.defense_mod = 2
		elif self.terrain_type == TOWN:
			self.color = ROAD_COLOR
			self.move_cost = 2
			self.defense_mod = 1
		elif self.terrain_type == RUINS:
			self.color = OPEN_GROUND_COLOR
			self.move_cost = 2
			self.defense_mod = 1
		
		# river in hex increases AP cost and decreases defense modifier
		# road in hex cancels this
		if self.river and not self.road:
			self.move_cost += 1
			self.defense_mod -= 1


# unit in the battle: infantry, cavalry, etc.
class Unit:
	def __init__(self, name, player, hx, hy, facing):
		
		self.name = name		# unit type name
		self.player = player		# owning player number, 0-1
		self.hx = hx			# hex location
		self.hy = hy
		self.facing = facing		# hex facing, 0 being up, increasing clockwise
		
		self.broken = False		# broken unit flag
		
		self.attack_mod = 0		# total attack value modification
		self.defense_mod = 0		# total defense "
		
		self.melee_locked = False	# flag to note if unit is melee locked
		self.free_attempt = False	# flag to note is unit has attempted to break
						# from melee lock
		
		self.x_offset = 0		# used for animating unit on the map
		self.y_offset = 0		# "
		
		self.ranks = 3			# " ranks
		
		# find this unit's stats in the list of unit types
		self.unit_type = None
		for t in unit_classes:
			if t.name == self.name:
				self.unit_type = t
				break
		
		# if could not find unit type, break with error
		if self.unit_type == None:
			print 'ERROR: Could not find unit type: ' + self.name
			return
		
		# set up unit stats based on unit type
		self.civ_num = self.unit_type.civ_num
		self.rating = self.unit_type.rating
		self.unit_class = self.unit_type.unit_class
		self.unit_char = self.unit_type.unit_char
		self.melee = self.unit_type.melee
		self.ranged = self.unit_type.ranged
		self.attack_range = self.unit_type.attack_range
		self.defense = self.unit_type.defense
		self.skill = self.unit_type.skill
		self.morale = self.unit_type.morale 
		self.columns = self.unit_type.columns
		self.portrait_file = self.unit_type.portrait_file
		self.special = self.unit_type.special
		self.max_ap = self.unit_type.max_ap
		self.ap = self.max_ap
		
		# set up fighter ranks and columns
		self.max_fighters = self.columns * self.ranks
		self.fighters = self.max_fighters
		
		# number of fighters in each rank, int
		self.rank_pop = list()
		for r in range(self.ranks):
			self.rank_pop.append(self.columns)
		
		# record of current filled ranks
		self.current_ranks = self.ranks		
		
		# set up unit consoles and sprite
		self.SetupConsoles()
	
	
	# select this unit
	def SelectMe(self):
		if battle.selected is not None:
			battle.selected.DeselectMe()
		battle.selected = self
		self.DrawSprite()
	
	
	# de-select this unit
	def DeselectMe(self):
		battle.selected = None
		self.DrawSprite()
	
	
	# set up consoles for new battle, after loading a game, or after saving a game
	# also re-draws sprite
	def SetupConsoles(self):
		self.portrait = libtcod.console_new(15, 13)
		self.LoadPortrait()
		self.stat_console = libtcod.console_new(CON_WIDTH-4, STAT_CON_HEIGHT)
		self.UpdateStatConsole()
		self.sprite = libtcod.console_new(UNIT_WIDTH, UNIT_HEIGHT)
		self.DrawSprite()
	
	
	# draw the facing indicator for this unit to the given console
	def DrawFacing(self, console, x, y, color):
		# set color to player color
		libtcod.console_set_default_foreground(console, color)
		# draw facing indicator characters
		if self.facing == 0:
			libtcod.console_put_char(console, x-2, y-2, 30)
			libtcod.console_put_char(console, x, y-2, 30)
			libtcod.console_put_char(console, x+2, y-2, 30)
		elif self.facing == 1:
			libtcod.console_put_char(console, x+3, y-2, '/')
			libtcod.console_put_char(console, x+4, y-1, '/')
			libtcod.console_put_char(console, x+5, y, '/')
		elif self.facing == 2:
			libtcod.console_put_char(console, x+3, y+2, '\\')
			libtcod.console_put_char(console, x+4, y+1, '\\')
			libtcod.console_put_char(console, x+5, y, '\\')
		elif self.facing == 3:
			libtcod.console_put_char(console, x-2, y+2, 31)
			libtcod.console_put_char(console, x, y+2, 31)
			libtcod.console_put_char(console, x+2, y+2, 31)
		elif self.facing == 4:
			libtcod.console_put_char(console, x-3, y+2, '/')
			libtcod.console_put_char(console, x-4, y+1, '/')
			libtcod.console_put_char(console, x-5, y, '/')
		elif self.facing == 5:
			libtcod.console_put_char(console, x-3, y-2, '\\')
			libtcod.console_put_char(console, x-4, y-1, '\\')
			libtcod.console_put_char(console, x-5, y, '\\')
		# reset console color
		libtcod.console_set_default_foreground(console, libtcod.white)
	
	
	# draw or re-draw the unit sprite to its sprite console
	def DrawSprite(self):
		libtcod.console_clear(self.sprite)
		if battle.selected == self:
			fg = libtcod.white
		else:
			if self.player == 0:
				if self.broken:
					fg = libtcod.dark_azure
				else:
					fg = libtcod.azure
			else:
				if self.broken:
					fg = libtcod.dark_flame
				else:
					fg = libtcod.flame
		libtcod.console_set_default_foreground(self.sprite, fg)
		
		# determine if unit is facing up or down
		up = False
		if self.facing == 0 or self.facing == 1 or self.facing == 5:
			up = True
		
		# draw ranks from front to back
		if up:
			y1 = 2
			ys = 1
		else:
			y1 = 4
			ys = -1
		
		x = int(UNIT_WIDTH/2)
		
		# grab each number of fighters in each rank and draw them
		for rank_pop in self.rank_pop:
			text = self.unit_char * rank_pop
			libtcod.console_print_ex(self.sprite, x, y1, libtcod.BKGND_NONE, libtcod.CENTER, text)
			y1 += ys
		
		# draw stats with location based on facing
		if up:
			dy = 5
		else:
			dy = 1
		
		if self.melee > 0:
			text = str(self.melee + self.attack_mod)
		elif self.ranged > 0:
			text = str(self.ranged + self.attack_mod)
		else:
			text = '0'
		text += ' - ' + str(self.defense + self.defense_mod)
		libtcod.console_print_ex(self.sprite, x, dy, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# draw broken indicator if applicable
		if self.broken:
			libtcod.console_set_default_foreground(self.sprite, libtcod.dark_red)
			libtcod.console_put_char(self.sprite, x, dy, 'B', flag=libtcod.BKGND_NONE)
			libtcod.console_set_default_foreground(self.sprite, libtcod.white)
		
		# draw facing indicator
		self.DrawFacing(self.sprite, x, 3, fg)
	
	
	# reset unit for new turn
	def Reset(self):
		self.ap = self.max_ap		# replenish action points
		self.free_attempt = False	# reset break attempt flag
		self.UpdateStatConsole()
	
	
	# remove from game
	def DestroyMe(self):
		Message(self.name + ' has been destroyed!')
		battle.BreakLocks(self)		# remove self from any melee locks
		battle.units.remove(self)	# remove self from list of active units
		if battle.selected == self:	# deselect if was selected
			self.DeselectMe()
		
		# TODO award points to opponent
		#if self.unit_class == 'Infantry':
		#	value = 1
		#else:
		#	value = 2
		#if self.player == 0:
		#	battle.player1_score += value
		#else:
		#	battle.player0_score += value
	
	
	# calculate total active attack and defense modifiers
	def ApplyMods(self):
		self.attack_mod = 0
		# terrain defense bonus
		self.defense_mod = GetHexFromMap(self.hx, self.hy).defense_mod
		
		# rank modifiers
		if self.current_ranks < self.ranks:
			self.attack_mod -= 1
		if self.current_ranks == 1:
			self.defense_mod -= 1
		
		# melee lock modifiers
		if 'Mobility' not in self.special:
			num_locks = 0
			for (obj1, obj2) in battle.melee_locks:
				if obj1 == self or obj2 == self:
					num_locks += 1
			if num_locks > 1:
				self.defense_mod -= num_locks - 1
		
		# TEMP: constrain defense modifier so that defense is at least 2
		if self.defense - self.defense_mod < 2:
			self.defense_mod = 2 - self.defense
		
		self.UpdateStatConsole()
		self.DrawSprite()
	
	
	# draw a representation of the unit to the console
	def DrawMe(self, console):
		# get top left of location on screen
		# if we're animating, use the offset location instead
		if self.x_offset > 0 or self.y_offset > 0:
			x, y = self.x_offset, self.y_offset
		else:
			x, y = Hex2Screen(self.hx, self.hy)
		# blit sprite to screen with background alpha
		libtcod.console_blit(self.sprite, 0, 0, UNIT_WIDTH, UNIT_HEIGHT, console, x+3, y+4, 1.0, 0.0)


	# load unit portrait and blit to portrait console
	def LoadPortrait(self):
		# fill in placeholder if no portrait
		if self.portrait_file == '':
			libtcod.console_set_default_background(self.portrait, libtcod.grey)
			libtcod.console_clear(self.portrait)
			libtcod.console_print_ex(self.portrait, 7, 4, libtcod.BKGND_NONE, libtcod.CENTER, 'Portrait')
			libtcod.console_print_ex(self.portrait, 7, 5, libtcod.BKGND_NONE, libtcod.CENTER, 'will go here')
			return
		# load portrait from file and blit to portrait console
		temp = libtcod.image_load(self.portrait_file)
		libtcod.image_blit_2x(temp, self.portrait, 0, 0)
		del temp


	# update info in stat console
	def UpdateStatConsole(self):
		libtcod.console_clear(self.stat_console)
		
		y = 0
		libtcod.console_print_ex(self.stat_console, (CON_WIDTH-4)/2, y, libtcod.BKGND_NONE, libtcod.CENTER, self.name)
		
		y += 1
		if self.civ_num == 0:
			text = 'Human '
		else:
			text = 'Undead '
		text += self.rating + ' ' + self.unit_class
		libtcod.console_print_ex(self.stat_console, (CON_WIDTH-4)/2, y+1,  libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# broken status
		if self.broken:
			libtcod.console_set_default_foreground(self.stat_console, libtcod.red)
			libtcod.console_print_ex(self.stat_console, (CON_WIDTH-4)/2, y+2, libtcod.BKGND_NONE, libtcod.CENTER, 'BROKEN')
			libtcod.console_set_default_foreground(self.stat_console, libtcod.white)
		
		# stats
		
		# melee value
		libtcod.console_print(self.stat_console, 1, y+3, 'Melee: ')
		if self.melee < 1:
			text = '-'
		else:
			melee = self.melee
			# positive or negative bonus applies
			if self.attack_mod > 0:
				melee += self.attack_mod
				libtcod.console_set_default_foreground(self.stat_console, libtcod.green)
			elif self.attack_mod < 0:
				melee += self.attack_mod
				libtcod.console_set_default_foreground(self.stat_console, libtcod.red)
			text = str(melee)
		libtcod.console_print(self.stat_console, 10, y+3, text)
		libtcod.console_set_default_foreground(self.stat_console, libtcod.white)
		
		# ranged value
		libtcod.console_print(self.stat_console, 1, y+4, 'Ranged: ')
		# original stat of 0 means no ranged attack
		if self.ranged == 0:
			libtcod.console_print(self.stat_console, 10, y+4, '-')
		else:
			ranged = self.ranged
			if self.attack_mod > 0:
				ranged += self.attack_mod
				libtcod.console_set_default_foreground(self.stat_console, libtcod.green)
			elif self.attack_mod < 0:
				ranged += self.attack_mod
				libtcod.console_set_default_foreground(self.stat_console, libtcod.red)
			libtcod.console_print(self.stat_console, 10, y+4, str(ranged))
			libtcod.console_set_default_foreground(self.stat_console, libtcod.white)
			
			attack_range = self.attack_range
			libtcod.console_print(self.stat_console, 12, y+4, '(' + str(attack_range) + ')')
		
		# defense value
		libtcod.console_print(self.stat_console, 1, y+5, 'Defense: ')
		defense = self.defense
		# positive or negative bonus applies
		if self.defense_mod > 0:
			defense += self.defense_mod
			libtcod.console_set_default_foreground(self.stat_console, libtcod.green)
		elif self.defense_mod < 0:
			defense += self.defense_mod
			libtcod.console_set_default_foreground(self.stat_console, libtcod.red)
		libtcod.console_print(self.stat_console, 10, y+5, str(defense))
		libtcod.console_set_default_foreground(self.stat_console, libtcod.white)
		
		# skill value
		libtcod.console_print(self.stat_console, 1, y+6, 'Skill: ')
		libtcod.console_print(self.stat_console, 10, y+6, str(self.skill))
		
		# morale value
		libtcod.console_print(self.stat_console, 1, y+7, 'Morale: ')
		libtcod.console_print(self.stat_console, 10, y+7, str(self.morale))
		
		# AP, only show if not broken
		if self.player == battle.active_player and not self.broken:
			libtcod.console_print(self.stat_console, 1, y+9, 'Action Points:')
			DrawBar(self.stat_console, self.ap, self.max_ap, libtcod.green, libtcod.darker_green, 1, y+10, 20)
			
		# total fighters
		libtcod.console_print(self.stat_console, 1, y+11, 'Fighters:')
		DrawBar(self.stat_console, self.fighters, self.max_fighters, libtcod.red, libtcod.darker_red, 1, y+12, 20)
		
		# display if melee locked
		if self.melee_locked:
			libtcod.console_set_default_foreground(self.stat_console, libtcod.light_red)
			libtcod.console_print(self.stat_console, 1, y+14, 'Melee Locked')
			libtcod.console_set_default_foreground(self.stat_console, libtcod.white)
			if self.player == battle.active_player and not self.broken and not self.free_attempt:
				libtcod.console_print(self.stat_console, 1, y+15, 'Attempt to [F]ree')

		# list specials
		if len(self.special) > 0:
			y = y+18
			for l in self.special:
				libtcod.console_print(self.stat_console, 1, y, l)
				y += 1

		# blit unit portrait to stat console
		libtcod.console_print_frame(self.stat_console, CON_WIDTH-21, 4, 17, 15)
		libtcod.console_blit(self.portrait, 0, 0, 15, 13, self.stat_console, CON_WIDTH-20, 5)


	# attempt to spend ap, returns false if not enough remaining
	def SpendAP(self, ap_cost):
		if self.ap >= ap_cost:
			if not FREE_AP: self.ap -= ap_cost
			self.UpdateStatConsole()
			return True
		return False


	# changes facing and keeps within 0-5 hexside system
	def GetFacing(self, new_facing):
		if new_facing < 0:
			new_facing += 6
		elif new_facing > 5:
			new_facing -= 6
		return new_facing


	# pivot unit in place
	def ChangeFacing(self, change):
		if self.broken:
			Message(self.name + ' is broken.')
			return
		
		# check for melee lock
		if self.melee_locked:
			Message(self.name + ' is melee locked.')
			return
			
		self.facing = self.GetFacing(self.facing + change)
		self.DrawSprite()
		

	# attempt to move forward one hex
	def MoveForward(self):
		if self.broken:
			Message(self.name + ' is broken.')
			return
		
		# check for melee lock
		if self.melee_locked:
			Message(self.name + ' is melee locked.')
			return
		
		hx2, hy2 = GetHexInDir(self.hx, self.hy, self.facing)

		# check to see that destination hex is on the game map
		if not HexIsOnMap(hx2, hy2):
			return
		
		# check to see if there's a unit in the destination hex
		for obj in battle.units:
			if obj.hx == hx2 and obj.hy == hy2:
				if obj.player == self.player:
					# try to initiate unit swap
					self.UnitSwap(obj)
					return
				else:
					Message('Enemy unit in target hex')
					return
		
		# get AP cost to move into hex
		cost = GetMoveCost(self, hx2, hy2)
		
		# check to see that we have enough AP remaining
		if not self.SpendAP(cost):
			Message('Not enough AP to move (' + str(cost) +' required)')
			return
		
		# animate into new hex
		x1, y1 = Hex2Screen(self.hx, self.hy)
		x2, y2 = Hex2Screen(hx2, hy2)
		points = GetLine(x1, y1, x2, y2)
		for (x, y) in points:
			self.x_offset = x
			self.y_offset = y
			RenderAll()
		self.x_offset = 0
		self.y_offset = 0
		
		# move into new hex
		self.hx = hx2
		self.hy = hy2
		
		# apply modifiers of new hex location
		self.ApplyMods()
	
	
	# try to swap positions with a friendly unit
	def UnitSwap(self, obj):
		if obj.broken:
			Message('Target platoon is Broken.')
			return
		
		if obj.melee_locked:
			Message('Target platoon is in melee combat.')
			return
		
		# check that both units have enough AP
		cost1 = GetMoveCost(self, obj.hx, obj.hy)
		if self.ap < cost1:
			Message('Not enough AP to move (' + str(cost1) +' required)')
			return
		cost2 = GetMoveCost(obj, self.hx, self.hy)
		if obj.ap < cost2:
			Message('Target platoon has insufficent AP to attempt swap (' + str(cost2) +' required)')
			return
		
		text = 'Attempt position swap with ' + obj.name + '?'
		if not GetYNWindow(text):
			Message('Swap canceled')
			return
		
		# TODO: require a skill test if any enemy units are adjacent to either hex
		
		#d1, d2 = Roll2D6()
		#Message('Skill roll is ' + str(d1) + ',' + str(d2))
		
		#if d1+d2 > self.skill:
		#	Message('Skill roll unsuccessful')
		#	self.SpendAP(cost1)
		#	return
		
		Message('Swap successful!')
		
		# swap the units
		self.hx, obj.hx = obj.hx, self.hx
		self.hy, obj.hy = obj.hy, self.hy
		self.SpendAP(cost1)			# also update stat consoles
		obj.SpendAP(cost2)
	
	
	# attempt to move along a path to a destination
	# does not spend any AP
	def MovePath(self, hx2, hy2, freemove=False):
		path, cost = GetPath(self, self.hx, self.hy, hx2, hy2)
		if cost < 1:
			Message('Error: No path possible!')
			return False
		else:
			if not freemove:
				if not self.SpendAP(cost):
					return False
			for (hx, hy) in path:
				self.facing = GetDirToHex(self.hx, self.hy, hx, hy)
				self.DrawSprite()	# in case we turned
				
				# animate into new hex
				x1, y1 = Hex2Screen(self.hx, self.hy)
				x2, y2 = Hex2Screen(hx, hy)
				points = GetLine(x1, y1, x2, y2)
				for (x, y) in points:
					self.x_offset = x
					self.y_offset = y
					RenderAll()
				self.x_offset = 0
				self.y_offset = 0
				
				# move into new hex
				self.hx = hx
				self.hy = hy
				
			RenderAll()
			return True
	
	
	# initiate an attack on enemy unit in hex
	def InitAttack(self, hx, hy):
		if self.broken: return
		# get the unit in the target hex
		for obj in battle.units:
			if obj.hx == hx and obj.hy == hy:
				# don't target self!
				if obj == self:
					return
				# don't target allies
				if obj.player == self.player:
					return
				
				# if target is not adjacent or attacker has no melee
				# attack, do a ranged attack
				if self.melee < 1 or GetHexDistance(self.hx, self.hy, obj.hx, obj.hy) > 1:
					self.RangedAttack(obj)
					return
				else:
					self.MeleeAttack(obj)
					return
			

	# start a melee attack on enemy unit
	def MeleeAttack(self, obj):
		
		# see if we are already melee locked
		if self.melee_locked:
			# make sure we're attacking an enemy with whom we are locked
			if not battle.IsMeleeLocked(self, obj):
				Message('Target not part of melee combat, cannot attack.')
				return
		
		# check AP
		if not self.SpendAP(1):
			Message('Not enough AP to attack (1 required)')
			return
		
		# check for existing melee lock and create a new one if none exists
		turn_to_face = False
		charge_bonus = False
		if not battle.IsMeleeLocked(self, obj):
			# if defender is not already involved in melee, it will turn to
			# face this attacker after the first attack
			if not obj.melee_locked:
				turn_to_face = True
			battle.CreateMeleeLock(self, obj)
			
			# possible charge bonus
			if 'Charge' in self.special:
				defense_mod = GetHexFromMap(obj.hx, obj.hy).defense_mod
				if defense_mod <= 0 and 'Polearms' not in obj.special:
					Message('Charge bonus!')  # TEMP
					charge_bonus = True
			
			# possible polearm bonus
			if 'Polearms' in self.special:
				if obj.unit_class == 'Cavalry':
					Message('Polearm bonus!')  # TEMP
					charge_bonus = True
		
		# turn attacker to face target
		self.facing = GetDirToHex(self.hx, self.hy, obj.hx, obj.hy)
		self.DrawSprite()
		
		# show melee attack message
		Message(self.name + ' attacks ' + obj.name)
		RenderAll()
		libtcod.sys_sleep_milli(400)
		
		# do attack, get number of hits on enemy, counter flag, and morale test flag
		hits, counter, def_morale_test = self.Attack(obj, charge=charge_bonus)
		
		# apply any damage
		obj.TakeHits(hits)
		
		own_hits = 0
		# if a counterattack was triggered, work it out now
		if counter:
			Message(obj.name + ' counterattacks!')
			own_hits, null, att_morale_test = obj.Attack(self, counter=True)
			self.TakeHits(own_hits)
		else:
			att_morale_test = False
		
		# pause to show casualties
		if hits > 0 or own_hits > 0:
			RenderAll()
			libtcod.sys_sleep_milli(600)
		
		# do any break tests and remove dead units
		if hits > 0:
			obj.UnitCheck()
		if own_hits > 0:
			self.UnitCheck()
		
		# if target was broken, return
		if obj.broken: return
		
		# if target is ranged and took at least one hit, it must fall back
		# ranged targets can't counter attack so attacker won't have to take
		# hits
		if hits > 0 and self.melee > 0 and obj.ranged > 0 and obj in battle.units:
			Message(obj.name + ' must fall back.')
			obj.FallBackTest(self, auto=True)
		else:
			# work out morale tests to fall back if any;
			# can't be both since counterattack needs a win
			if def_morale_test:
				obj.FallBackTest(self)
			elif att_morale_test:
				self.FallBackTest(obj)
		
		# if defender is still adjacent to attacker, they may turn to face them
		if GetHexDistance(self.hx, self.hy, obj.hx, obj.hy) == 1 and turn_to_face:
			obj.facing = GetDirToHex(obj.hx, obj.hy, self.hx, self.hy)
			obj.DrawSprite()
	
	
	# try to do a ranged attack on target unit
	def RangedAttack(self, obj):
		
		# no ranged attack
		if self.ranged < 1:
			Message('Attacker does not have a ranged attack')
			return
		
		# if we're melee locked, make sure we're attacking an enemy with whom we are locked
		if self.melee_locked and not battle.IsMeleeLocked(self, obj):
			Message('Target not part of melee combat, cannot attack.')
			return
		
		# get range to target
		dist = GetHexDistance(self.hx, self.hy, obj.hx, obj.hy)
		
		if dist > self.attack_range:
			Message('Target is out of range (' + str(dist) + ' hexes)')
			return
		
		# check if target is melee locked and not with us
		half_hits = False
		if obj.melee_locked and not battle.IsMeleeLocked(self, obj):
			Message('Target in melee, hits halved.')
			half_hits = True
		
		# display and check LoS
		RenderAll()
		x1, y1 = Hex2Screen(self.hx, self.hy, center=True)
		x2, y2 = Hex2Screen(obj.hx, obj.hy, center=True)
		points = GetLine(x1, y1, x2, y2)
		for (x, y) in points:
			libtcod.console_set_char_background(0, x, y, libtcod.white, flag=libtcod.BKGND_SET)
		libtcod.console_flush()
		libtcod.sys_sleep_milli(600)
		
		if self.CheckLoS(obj):
			Message('Line of Sight is blocked')
			return
		
		# check AP
		if not self.SpendAP(1):
			Message('Not enough AP to attack (1 required)')
			return
		
		Message(self.name + ' does a ranged attack on ' + obj.name)
		
		# face target
		self.facing = GetDirToHex(self.hx, self.hy, obj.hx, obj.hy)
		self.DrawSprite()
		
		# get number of hits, will never return counter since it's a ranged attack
		hits, counter, def_morale_test = self.Attack(obj, ranged=True, half=half_hits)
		if hits > 0:
			# apply any damage to target
			obj.TakeHits(hits)
		
			# pause to show casualties
			RenderAll()
			libtcod.sys_sleep_milli(600)
			
			# do morale tests and remove dead units
			obj.UnitCheck()
		
		# if target was broken, return
		if obj.broken: return
		
		# if unit is still alive, work out any required fall back test
		if def_morale_test and obj in battle.units:
			obj.FallBackTest(self)
	
	
	# TODO: LoS will have to be moved out of units because engine will need to
	# check them sometimes
	# check LoS between two hexes along a hex spine
	def CheckHexSpineLoS(self, hx1, hy1, hx2, hy2, degs):
		
		# get moves required to build hex line based on angle
		
		if degs == 51:
			moves = [(0,1), (1,0)]
		elif degs == 0:
			moves = [(1,1), (0,-1)]
		elif degs == 310:
			moves = [(1,0), (-1,-1)]
		elif degs == 231:
			moves = [(0,-1), (-1,0)]
		elif degs == 180:
			moves = [(-1,-1), (0,1)]
		elif degs == 130:
			moves = [(-1,0), (1,1)]
		else:
			Message('CheckHexSpineLoS() Error!')
			return []
		
		# start at attacker and step toward target
		hx, hy = hx1, hy1
		while hx != hx2 and hy != hy2:
			# check next pair of hexes
			(xm, ym) = moves[0]
			hx += xm
			hy += ym
			blocks1 = BlocksLoS(hx, hy, self.player)
			
			(xm, ym) = moves[1]
			hx += xm
			hy += ym
			blocks2 = BlocksLoS(hx, hy, self.player)
			
			# if both blocked, LoS is blocked
			if blocks1 and blocks2:
				return True
			
			# step to next hex in line
			(xm, ym) = moves[0]
			hx += xm
			hy += ym
			
			# if this is the target hex, LoS is clear
			if hx == hx2 and hy == hy2:
				return False
			
			# otherwise check this hex, and if it's clear, we can move on to next pair
			if BlocksLoS(hx, hy, self.player):
				return True
		
		# we shouldn't get here, but if we do, LoS is clear
		return False
	
	
	# display and check LoS from this unit to the target 
	def CheckLoS(self, obj):
		# get hex path to target
		x1, y1 = Hex2Screen(self.hx, self.hy, center=True)
		x2, y2 = Hex2Screen(obj.hx, obj.hy, center=True)
		
		# if path is on a hexline, we need to check hexes on both sides of the line
		# TODO: this might not be accurate enough
		dx, dy = x2-x1, y2-y1
		rads = atan2(-dy,dx)
		rads %= 2*pi
		degs = int(ceil(degrees(rads)))
		
		if degs in [51, 0, 310, 231, 180, 130]:
			blocked = self.CheckHexSpineLoS(self.hx, self.hy, obj.hx, obj.hy, degs)
			return blocked
		else:
			points = GetLine(x1, y1, x2, y2)
			LoS = []
			for (x, y) in points:
				hx, hy = GetHex(x, y)
				if (hx, hy) in LoS:
					continue
				LoS.append((hx, hy))
			
		# check the list of hexes intersected by the line of sight
		for (hx, hy) in LoS:
			# ignore attacker's and defender's hex
			if hx == self.hx and hy == self.hy:
				continue
			if hx == obj.hx and hy == obj.hy:
				continue
			
			if BlocksLoS(hx, hy, self.player):
				return True
			
		return False
	
	
	# works out an attack, melee or ranged, on the target and returns number of hits
	# on the target and hits on the attacker resulting from a counterattack
	# also returns True if defender has to take a Break test
	def Attack(self, obj, counter=False, ranged=False, half=False, charge=False):
		# display combat window
		libtcod.console_clear(session.battle_console)
		
		# names
		libtcod.console_print(session.battle_console, 2, 1, self.name)
		libtcod.console_set_default_foreground(session.battle_console, libtcod.red)
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH/2, 1, 
			libtcod.BKGND_NONE, libtcod.CENTER, '>> attacking >>')
		libtcod.console_set_default_foreground(session.battle_console, libtcod.white)
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH-3, 1, 
			libtcod.BKGND_NONE, libtcod.RIGHT, obj.name)
		
		# portraits
		libtcod.console_blit(self.portrait, 0, 0, 15, 13, session.battle_console, 1, 3)
		libtcod.console_blit(obj.portrait, 0, 0, 15, 13, session.battle_console, BATTLE_CONSOLE_WIDTH-16, 3)
		
		# calculate and display attack and defense values
		if ranged:
			attack_value = self.ranged + self.attack_mod
			
			# further attack modifiers for range beyond 2 hexes
			dist = GetHexDistance(self.hx, self.hy, obj.hx, obj.hy)
			dist -= 2
			if dist > 0:
				attack_value -= dist
				Message('Ranged attack value at -' + str(dist) + ' for range.')
				RenderAll()
			
		else:
			attack_value = self.melee + self.attack_mod
			
			if charge:
				attack_value += 2
		
		# limit max effective attack value to 11
		if attack_value > 11: attack_value = 11
		
		defense_value = obj.defense + obj.defense_mod
		
		# limit min effective defense value to 2
		# (already done in ApplyMods)
		#if defense_value < 2: defense_value = 2
		
		# apply shield bonus if any
		if 'Shields' in obj.special:
			if obj.IsInFront(self.hx, self.hy):
				Message('Shield Bonus!')  # TEMP
				defense_value += 1
		
		libtcod.console_print(session.battle_console, 18, 3, 'Attack')
		libtcod.console_print(session.battle_console, 21, 4, str(attack_value))
		
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH-19, 3, 
			libtcod.BKGND_NONE, libtcod.RIGHT, 'Defense')
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH-22, 4, 
			libtcod.BKGND_NONE, libtcod.RIGHT, str(defense_value))
		
		# do attack and defense rolls
		def DisplayDie(x, y, value):
			libtcod.console_rect(session.battle_console, x, y, 3, 3, True, flag=libtcod.BKGND_SET)
			
			if 4 <= value <= 6:
				libtcod.console_put_char(session.battle_console, x, y, 7)	# top left and bottom right
				libtcod.console_put_char(session.battle_console, x+2, y+2, 7)
			if value > 1:
				libtcod.console_put_char(session.battle_console, x+2, y, 7)	# top right and bottom left
				libtcod.console_put_char(session.battle_console, x, y+2, 7)
			if IsOdd(value):
				libtcod.console_put_char(session.battle_console, x+1, y+1, 7)	# center
			if value == 6:
				libtcod.console_put_char(session.battle_console, x, y+1, 7)	# center left and right
				libtcod.console_put_char(session.battle_console, x+2, y+1, 7)
			
		# do a number of rolls for each, displaying each and pausing, the settle on final roll
		libtcod.console_set_default_foreground(session.battle_console, libtcod.black)
		libtcod.console_set_default_background(session.battle_console, libtcod.white)
		ROLLS = 5
		for r in range(ROLLS):
			d1, d2 = Roll2D6()
			#d1, d2 = 6, 6  # TEMP
			attack_roll = d1+d2
			d3, d4 = Roll2D6()
			#d3, d4 = 1, 1  # TEMP
			defense_roll = d3+d4
			
			DisplayDie(18, 10, d1)
			DisplayDie(22, 10, d2)
			DisplayDie(BATTLE_CONSOLE_WIDTH-20, 10, d3)
			DisplayDie(BATTLE_CONSOLE_WIDTH-24, 10, d4)
			
			libtcod.console_blit(session.battle_console, 0, 0, BATTLE_CONSOLE_WIDTH, 
				BATTLE_CONSOLE_HEIGHT, 0, (SCREEN_WIDTH/2)-(BATTLE_CONSOLE_WIDTH/2), 
				(SCREEN_HEIGHT/2)-(BATTLE_CONSOLE_HEIGHT/2))
			libtcod.console_flush()
			libtcod.sys_sleep_milli(80)
		libtcod.console_set_default_background(session.battle_console, libtcod.black)
		
		if attack_roll <= attack_value:
			att = True
			text = 'Success!'
			libtcod.console_set_default_foreground(session.battle_console, libtcod.light_azure)
		else:
			att = False
			text = 'Failed'
			libtcod.console_set_default_foreground(session.battle_console, libtcod.red)
		libtcod.console_print_ex(session.battle_console, 22, 14, 
			libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		if defense_roll <= defense_value:
			dff = True
			text = 'Success!'
			libtcod.console_set_default_foreground(session.battle_console, libtcod.light_azure)
		else:
			dff = False
			text = 'Failed'
			libtcod.console_set_default_foreground(session.battle_console, libtcod.red)
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH-20, 14, 
			libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		libtcod.console_set_default_foreground(session.battle_console, libtcod.white)
		
		# work out effects
		morale_check = False
		# both fail
		if not att and not dff:
			text = 'No Effect'
			hits, counter = 0, False
		
		# attack failed but defense succeeded
		# ranged attacks and counterattacks will never trigger a counterattack
		# units with no melee value and broken units can't counterattack
		# only allow counterattacks against units in front
		elif not att and dff:
			if ranged or counter or obj.melee < 1 or obj.broken or not obj.IsInFront(self.hx, self.hy):
				text = 'No Effect'
				hits, counter = 0, False
			else:
				text = 'Counterattack!'
				hits, counter = 0, True
		else:
			# work out by how many points the attack roll succeeded
			attack_points = attack_value - attack_roll
			
			# attack succeeded and defense failed
			if att and not dff:
				
				# work out by how many points the defense roll failed
				defense_fail = defense_roll - defense_value
				
				hits, counter = attack_points + defense_fail + 1, False
				
				# apply half hits if any, rounded up, at least one hit
				if half:
					hits = int(ceil(hits/2))
					if hits < 1: hits = 1
				
				text = str(hits) + ' Hits'
				
				# if defense failed with doubles, and unit is not broken,
				# morale check needed to avoid falling back
				if d3 == d4 and not obj.broken:
					morale_check = True
				
			else:
				# both attack and defense succeeded
				defense_points = defense_value - defense_roll
				
				if attack_points > defense_points:
					hits, counter = attack_points - defense_points, False
					# apply half hits if any, rounded up, at least one hit
					if half:
						hits = int(ceil(hits/2))
						if hits < 1: hits = 1
					text = str(hits) + ' Hits'
				else:
					text = 'No Effect'
					hits, counter = 0, False
		
		# display result
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH/2, 15, 
			libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# ranged units that take at least one melee hit must fall back
		if hits > 0 and self.melee > 0 and obj.ranged > 0:
			libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH/2, 16, 
				libtcod.BKGND_NONE, libtcod.CENTER, 'Defender Falls Back')
		elif morale_check:
			libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH/2, 16, 
				libtcod.BKGND_NONE, libtcod.CENTER, 'Defender Morale Test')
		
		libtcod.console_print_ex(session.battle_console, BATTLE_CONSOLE_WIDTH/2, 17, 
			libtcod.BKGND_NONE, libtcod.CENTER, 'Space to Continue')
		
		# blit battle console to screen and wait for space
		libtcod.console_blit(session.battle_console, 0, 0, BATTLE_CONSOLE_WIDTH, 
				BATTLE_CONSOLE_HEIGHT, 0, (SCREEN_WIDTH/2)-(BATTLE_CONSOLE_WIDTH/2), 
				(SCREEN_HEIGHT/2)-(BATTLE_CONSOLE_HEIGHT/2))
		libtcod.console_flush()
		
		WaitForSpace()
		
		return hits, counter, morale_check
		
		
	# take a number of hits
	def TakeHits(self, hits):
		if hits < 1: return
		Message(self.name + ' suffers ' + str(hits) + ' hits')
		self.TakeDamage(hits)
		self.DrawSprite()


	# remove a number of fighters from damage
	def TakeDamage(self, damage):
		# go through ranks back to front, removing fighters
		active_ranks = len(self.rank_pop)
		for r in reversed(range(0, active_ranks)):
			if self.rank_pop[r] > 0:
				if self.rank_pop[r] > damage:
					self.rank_pop[r] -= damage
					return
				else:
					damage -= self.rank_pop[r]
					self.rank_pop[r] = 0
					continue
	
	
	# check if the unit is dead, and do a morale test of required
	def UnitCheck(self):
		# count live fighters
		self.fighters = 0
		for rank_pop in self.rank_pop:
			self.fighters += rank_pop
		
		# if nobody's left, unit is dead
		if self.fighters < 1:
			self.DestroyMe()
			return
		
		# record number of populated ranks
		self.current_ranks = int(ceil(float(self.fighters) / float(self.columns)))
		
		# update modifiers in case number has changed
		self.ApplyMods()
		
		# if less than 1/2 remaining, do a morale test
		if self.fighters <= int(self.max_fighters/2):
			self.BreakTest()
		
		self.UpdateStatConsole()


	# take a morale check to see if platoon falls back
	# if auto is true, the unit automatically falls back
	# if unit can't fall back, it stays put
	def FallBackTest(self, obj, auto=False):
		# skip if dead
		if self not in battle.units:
			return
		
		if not auto:
			d1, d2 = Roll2D6()
			#d1, d2 = 6, 6  # TEMP
			if d1 + d2 <= self.morale:
				Message(self.name + ' passes its Morale test.')
				return
			
			Message(self.name + ' fails its Morale test.')
		
		# choose fall back destination
		direction = GetDirToHex(self.hx, self.hy, obj.hx, obj.hy)
		hexes = self.GetRearHexes(direction)
		
		# check that no unit is in a potential move location
		for (hx, hy) in hexes[::-1]:
			if HexIsOccupied(hx, hy):
				hexes.remove((hx, hy))
		
		# if no hexes left, can't fall back, so stays put
		if len(hexes) == 0:
			Message(self.name + ' cannot fall back.')
			return
		
		# break any melee locks that this unit is in
		battle.BreakLocks(self)
		
		# see if a pursuit move is possible
		pursuit_option = False
		if GetHexDistance(self.hx, self.hy, obj.hx, obj.hy) == 1 and not obj.melee_locked:
			pursuit_option = True
			old_hx = self.hx
			old_hy = self.hy
		
		# try to pick a location closest to most friendlies and furthest
		# from enemies
		hx2, hy2 = GetFriendlyHex(hexes, self.player)
		self.hx = hx2
		self.hy = hy2
		
		Message(self.name + ' falls back.')
		# drain AP in case this was result of a counterattack
		self.ap = 0
		
		RenderAll()
		
		# if there is a pursuit option, prompt enemy player
		if pursuit_option:
			if self.player == 1 or self.player == 0: # TEMP
				text = 'Pursue enemy? (No AP cost)'
				if GetYNWindow(text):
					# move attacker
					obj.hx = old_hx
					obj.hy = old_hy
					# re-establish melee lock
					battle.CreateMeleeLock(self, obj)
					
					Message(obj.name + ' pursues.')
			else:
				# TODO: give AI option of pursuit
				pass


	# take a break test
	# TODO: display a window and dice animation
	def BreakTest(self):
		d1, d2 = Roll2D6()
		#d1, d2 = 6, 6  # TEMP
		if d1 + d2 <= self.morale:
			Message(self.name + ' passes its Break test.')
			return
		
		# remove from any melee locks
		battle.BreakLocks(self)
		
		# if already broken, unit is destroyed
		if self.broken:
			Message(self.name + ' fails its Break test while Broken.')
			self.DestroyMe()
			return
		
		# otherwise, unit is broken
		Message(self.name + ' fails its Break test and is Broken.')
		self.broken = True
		self.UpdateStatConsole()
		self.DrawSprite()
		
		# do an immediate retreat move, ignore result
		self.RetreatMove()
	
	
	# returns a list of the three hexes opposite the given direction
	# if hex is off-board, does not return it
	def GetRearHexes(self, direction):
		hexes = []
		for turn in range (2, 5):
			hx, hy = GetHexInDir(self.hx, self.hy, self.GetFacing(direction + turn))
			if HexIsOnMap(hx, hy):
				hexes.append((hx, hy))
		return hexes
	
	
	# returns true if the given hex is in this unit's front arc, otherwise False
	def IsInFront(self, hx, hy):
		base_dir = GetDirToHex(self.hx, self.hy, hx, hy)
		direction = self.GetFacing(base_dir - self.facing)
		if 0 <= direction <= 1 or direction == 5:
			return True
		return False
	
	
	# try to free unit from melee locks
	def FreeAttempt(self):
		if self.broken or self.free_attempt: return
		
		if self.ap < self.max_ap:
			Message('Must attempt as first action of turn.')
			return
		
		if not self.SpendAP(1):
			Message('Not enough AP (1 required).')
			return
		
		# set flag
		self.free_attempt = True
		
		# count up existing melee locks
		infantry_only = True
		locks = 0
		for (obj1, obj2) in battle.melee_locks:
			if obj1 == self:
				locks += 1
				if obj2.unit_class != 'Infantry':
					infantry_only = False
			elif obj2 == self:
				locks += 1
				if obj1.unit_class != 'Infantry':
					infantry_only = False
		
		# cav units locked with only infantry break automatically
		if self.unit_class == 'Cavalry' and infantry_only:
			battle.BreakLocks(self)
			message(self.name + ' breaks out of melee combat.')
			return
		
		# do skill test
		d1, d2 = Roll2D6()
		Message('Skill roll is ' + str(d1) + ',' + str(d2))
		
		if d1+d2 > self.skill - locks:
			Message('Skill roll unsuccessful, unit still in melee lock.')
			return
		Message('Skill roll successful, breaks out of melee combat.')
		battle.BreakLocks(self)
	
	
	########################################################################
	#               Automatic Movement and Other Actions                   #
	########################################################################
	
	# returns a list of adjacent enemy units
	# if unbroken is true, ignores broken units
	def GetAdjacentEnemies(self, hx, hy, unbroken=False):
		adjacent_hexes = GetAdjacents(hx, hy)
		adjacent_foes = []
		for (direction, hx, hy) in adjacent_hexes:
			if direction < 0: continue		# off map
			for obj2 in battle.units:
				if obj2.hx == hx and obj2.hy == hy and obj2.player != self.player:
					if unbroken and obj2.broken: continue
					adjacent_foes.append(obj2)
		return adjacent_foes
	
	
	# returns the best possible melee attack, returns None if no attack possible
	def AIGetBestMelee(self):
		targets = []
		
		# if we're in melee lock, we have to pick an enemy with whom we are locked
		if self.melee_locked:
			enemies = self.GetAdjacentEnemies(self.hx, self.hy)
			for obj in enemies:
				if battle.IsMeleeLocked(self, obj):
					targets.append(obj)
			
			if len(targets) == 0:
				print 'ERROR AIGetBestMelee(): In melee lock but no valid targets'
				return False
		else:
			# get list of adjacent enemies, return if none left
			targets = self.GetAdjacentEnemies(self.hx, self.hy)
			if len(targets) == 0:
				return False
		
		# select best target from list
		top_score = 0
		attacks = []
		for obj in targets:
			# score a hypothetical attack on them
			score = ScoreAttack(self, obj)
			#print 'Scored an attack at ' + str(score)
			attacks.append((score, obj))
			if score > top_score: top_score = score
		
		# do one of the top scored attacks
		best_attacks = [obj for (score, obj) in attacks if score == top_score]
		target = best_attacks[libtcod.random_get_int(0, 0, len(best_attacks)-1)]
		
		return target


	# general AI action function: scores all potential actions
	# returns True if could not find any possible actions
	def AIAction(self):
		
		# can't do anything with less than 1 ap
		if self.ap < 1: return True
		
		# if we're in melee lock, then our potential actions are limited
		if self.melee_locked:
			# try to attack an enemy in lock
			target = self.AIGetBestMelee()
			if target is None:
				return True
			self.MeleeAttack(target)
			return False
	
		# if we're a melee unit, see if we can either attack an enemy right away
		# or move into a position from which we can attack one
		if self.melee > 0:
			
			# go through each enemy unit, scoring a move to each adjacent hex
			# higher scores for lower AP cost to get there, good cover, and adjacent friends
			# lower scores for adjacent enemies, harder targets, broken targets
			
			scored_list = []
			best_score = 0
			
			for obj in battle.units:
				if obj.player != self.player:
					hexes = GetOpenAdjacents(self, obj.hx, obj.hy)
					if len(hexes) == 0:
						continue
					for (hx2, hy2) in hexes:
						path, cost = GetPath(self, self.hx, self.hy, hx2, hy2)
						# if possible to move there and attack
						if cost <= self.ap - 1:
							# calculate location score
							ap_score = (self.ap - cost) * 30
							def_score = GetHexFromMap(hx2, hy2).defense_mod * 20
							
							attack_score = ScoreAttack(self, obj)
							score = attack_score + ap_score + def_score
							
							# add to list
							scored_list.append((score, hx2, hy2, obj))
							if score > best_score:
								best_score = score
			
			# if any moves were possible
			if len(scored_list) > 0:
				
				# TEMP: display moves
				for (score, hx, hy, obj) in scored_list:
					x, y = Hex2Screen(hx, hy, center=True)
					text = str(score)
					libtcod.console_print_ex(0, x, y, libtcod.BKGND_NONE, libtcod.CENTER, text)
					x, y = Hex2Screen(obj.hx, obj.hy, center=True)
					libtcod.console_print_ex(0, x, y, libtcod.BKGND_NONE, libtcod.CENTER, '*')
					
				libtcod.console_flush()
				libtcod.sys_sleep_milli(200)
				
				# select one of the best actions and do it!
				top_list = [(hx, hy, obj) for (score, hx, hy, obj) in scored_list if score == best_score]
				(hx, hy, obj) = top_list[libtcod.random_get_int(0, 0, len(top_list)-1)]
				
				# move
				self.MovePath(hx, hy)
				
				# attack if possible
				if self.ap > 0:
					self.MeleeAttack(obj)
					return False
				return True
				
			else:
				#Message('No attack moves possible')
				self.AIAdvance()
				return True
	
		#self.AIAdvance()
		return True
	
	
	# advance toward enemy and objective locations
	def AIAdvance(self):
		# get list of possible destinations
		max_range = self.ap
		target_hexes = GetHexesWithin(self.hx, self.hy, max_range)
		
		scored_list = []
		top_score = 0
		for (hx, hy) in target_hexes:
			if HexIsOccupied(hx, hy): continue
			score = 0
			# for melee units, closer to enemies is better
			# but 2 hexes away is ideal, to make them move to attack
			for obj in battle.units:
				if obj.player != self.player:
					proximity_score = 40 - GetHexDistance(hx, hy, obj.hx, obj.hy)
					if obj.broken:
						proximity_score = proximity_score // 2
					
					# score terrain
					#defense_mod = GetHexFromMap(hx, hy).defense_mod
					#proximity_score += (defense_mod * 5)
					
					score += proximity_score
			
			# add this scored hex to the list
			scored_list.append((score, hx, hy))
			
			if score > top_score: top_score = score
			
			# TODO: for ranged units, within 5 hexes but not closer to enemies is better
		
		# TEMP: display scores on map
		for (score, hx, hy) in scored_list:
			x, y = Hex2Screen(hx, hy, center=True)
			text = str(score)
			libtcod.console_print_ex(0, x, y, libtcod.BKGND_NONE, libtcod.CENTER, text)
		libtcod.console_flush()
		libtcod.sys_sleep_milli(200)
		#WaitForSpace()
		
		#print 'AIAdvance: Top score is ' + str(top_score)
		
		# run down the list by score and try to move there
		shuffle(scored_list)
		scored_list.sort(key=lambda tup: tup[0], reverse=True)
		for (score, hx, hy) in scored_list:
			if self.MovePath(hx, hy):
				return
		
		print 'AIAdvance: Could not plot a path to any scored target hex'
		
	
	# Retreat move, used for Broken units
	# returns True if it did have to do a retreat move
	def RetreatMove(self):
		# first check: is unit adjacent to an unbroken enemy platoon
		adjacent_foes = self.GetAdjacentEnemies(self.hx, self.hy, unbroken=True)
		if len(adjacent_foes) > 0:
			# find closest hex that has no adjacent enemy platoons
			# start with adjacent hexes and move out to a max radius of 5 hexes
			destinations = []
			for radius in range(1, 6):
				hexes = GetHexesWithin(self.hx, self.hy, radius, exact=True)
				for (hx, hy) in hexes:
					# if it's occupied, skip it
					if HexIsOccupied(hx, hy): continue
					
					enemies = 0
					adjacents = GetAdjacents(hx, hy)
					for (direction, hx2, hy2) in adjacents:
						if HexHasUnbrokenEnemy(hx2, hy2, self.player):
							enemies += 1
					# no adjacent enemies, add to destination list
					if enemies == 0:
						destinations.append((hx, hy))
				if len(destinations) > 0:
					break
			
			# if we found at least one good destination, pick the best one
			# and head there, no AP cost
			if len(destinations) > 0:
				hx, hy = GetFriendlyHex(destinations, self.player)
				Message(self.name + ' retreats.')
				RenderAll()
				libtcod.sys_sleep_milli(600)
				self.MovePath(hx, hy, freemove=True)
				return True
			else:
				Message(self.name + ' cannot retreat.')
				self.DestroyMe()
				return True
		return False


# spawn a new unit into the battle
def SpawnUnit(name, player, hx, hy, facing):
	new_unit = Unit(name, player, hx, hy, facing)
	# if there was an error with the unit type, return
	if new_unit.unit_type is None:
		return None
	battle.units.append(new_unit)
	return new_unit


# returns a score representing the likely success of a given attack
# TODO: needs improvement
def ScoreAttack(attacker, defender):
	if attacker.melee > 0:
		attack_score = attacker.melee + attacker.attack_mod
	elif attacker.ranged > 0:
		attack_score = attacker.ranged + attacker.attack_mod
	else:
		# no attack!
		return -1
	
	defend_score = defender.defense + defender.defense_mod
	
	return int(float(attack_score) / float(defend_score) * 100.0)


# prints a message announcing current turn, turn limit, and active player
def DisplayTurnInfo():
	text = 'Turn ' + str(battle.current_turn) + '/' + str(battle.turn_limit)
	text += ', Player ' + str(battle.active_player+1) + ' is active'
	Message(text)


# returns true if number is odd
def IsOdd(num):
	return num & 1 and True or False


# do a 2D6 roll
def Roll2D6():
	return libtcod.random_get_int(0, 1, 6), libtcod.random_get_int(0, 1, 6)


# add a game message and delete oldest one in queue if necessisary
def Message(new_msg, color=libtcod.white):
	# split the message if necessary, among multiple lines
	new_msg_lines = wrap(new_msg, CON_WIDTH-4, subsequent_indent = ' ')
	
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(battle.messages) == MSG_CON_HEIGHT:
			del battle.messages[0]
		
		#add the new line as a tuple, with the text and the color
		battle.messages.append( (line, color) )
	
	# update the message console
	session.UpdateMsgConsole()


# Bresenham's Line Algorithm
# returns a series of x, y points along a line
# copied from an implementation on the roguebasin wiki
def GetLine(x1, y1, x2, y2):
	points = []
	issteep = abs(y2-y1) > abs(x2-x1)
	if issteep:
		x1, y1 = y1, x1
		x2, y2 = y2, x2
	rev = False
	if x1 > x2:
		x1, x2 = x2, x1
		y1, y2 = y2, y1
		rev = True
	deltax = x2 - x1
	deltay = abs(y2-y1)
	error = int(deltax / 2)
	y = y1
	
	if y1 < y2:
		ystep = 1
	else:
		ystep = -1
	for x in range(x1, x2 + 1):
		if issteep:
			points.append((y, x))
		else:
			points.append((x, y))
		error -= deltay
		if error < 0:
			y += ystep
			error += deltax
			
	# Reverse the list if the coordinates were reversed
	if rev:
		points.reverse()
	return points


# returns True if hex blocks ranged attack LoS for given player
def BlocksLoS(hx, hy, player):
	# see if LoS-blocking terrain is in this hex
	h = GetHexFromMap(hx, hy)
	if h.terrain_type == FOREST:
		return True


# get a yes or no input from the player, returns True if yes, otherwise false
# defaults to No
# TODO: doesn't work when mouse button is being clicked?
def GetYN():
	# render screen to make sure prompt is visible
	RenderAll()
	libtcod.sys_wait_for_event(libtcod.EVENT_KEY_PRESS, key, mouse, True)
	if chr(key.c) == 'y':
		return True
	return False


# display a window with a text prompt, and get a y/n input from the user
# returns True if yes, False if no, defaults to no
# TODO: if hex1 and/or hex2 are supplied, window will be displayed so that this 
# hex is not obscured
def GetYNWindow(text, hex1=None, hex2=None):
	w = 60
	h = 6
	x = (SCREEN_WIDTH/2)-(w/2)
	y = (SCREEN_HEIGHT/2)-(h/2)
	libtcod.console_rect(0, x, y, w, h, True, flag=libtcod.BKGND_SET)
	libtcod.console_print_frame(0, x, y, w, h)
	libtcod.console_print_ex(0, SCREEN_WIDTH/2, y+2, libtcod.BKGND_NONE, libtcod.CENTER, text) 
	libtcod.console_print_ex(0, SCREEN_WIDTH/2, y+4, libtcod.BKGND_NONE, libtcod.CENTER, '(y/N)')
	libtcod.console_flush()
	libtcod.sys_wait_for_event(libtcod.EVENT_KEY_PRESS, key, mouse, True)
	if chr(key.c) == 'y':
		return True
	return False
	

# don't do anything until space is pressed
def WaitForSpace():
	space=False
	while not space:
		libtcod.sys_wait_for_event(libtcod.EVENT_KEY_PRESS, key, mouse, True)
		if key.vk == libtcod.KEY_SPACE:
			space = True
		
		
# returns hex coordinates given a screen character location
def GetHex(x, y):	
	# calculate approximate hexcolumn and save remainder
	(col, x_remainder) = divmod((x-1), 9)
	
	# get hexrow and convert to y value, save remainder
	if IsOdd(col):
		ylimit = 55
	else:
		ylimit = 52
	(row, y_remainder) = divmod((ylimit-y), 6)
	row += col//2
	
	# handle edge cases
	#if x_remainder <= 4:
	#	y_difference = abs(4-y_remainder)
	#	if x_remainder+1 <= y_difference:
	#		col -= 1
	#		if y_remainder < 4:
	#			row -=1
	return col, row


# returns list of hexes within a certain distance of hx, hy
# if exact, only returns hexes that exact distance away
# will only return hexes that are on the map
def GetHexesWithin(hx, hy, distance, exact=False):
	hexes = []
	for h in battle.map_hexes:
		dist = GetHexDistance(hx, hy, h.hx, h.hy)
		if (exact and dist == distance) or (not exact and dist <= distance):
			hexes.append((h.hx, h.hy))
	return hexes


# from a list of hexes, selects one with the greatest number of adjacent unbroken friends,
# and the lowest number of unbroken enemies
# in case of ties, selects a random one
def GetFriendlyHex(hexes, player):
	hex_list = []
	for (hx, hy) in hexes:		
		friends = 0
		for direction in range(0, 6):
			hx2, hy2 = GetHexInDir(hx, hy, direction)
			for obj in battle.units:
				if obj.hx == hx2 and obj.hy == hy2:
					if obj.player == player:
						friends += 1
					else:
						friends -= 1
		hex_list.append((friends, hx, hy))
	
	# grab top scoring hexes from list
	hex_list.sort(key=lambda tup: tup[0], reverse=True)
	(top_score, hx, hy) = hex_list[0]
	top_list = [(hx, hy) for (score, hx, hy) in hex_list if score == top_score]
	
	# return a random top scoring hex
	(hx, hy) = top_list[libtcod.random_get_int(0, 0, len(top_list)-1)]
	return hx, hy


# return true if there's a unit in the given hex
def HexIsOccupied(hx, hy):
	for obj in battle.units:
		if obj.hx == hx and obj.hy == hy:
			return True
	return False


# returns true if there's an unbroken enemy in the given hex
# player is the friendly unit's player
def HexHasUnbrokenEnemy(hx, hy, player):
	for obj in battle.units:
		if obj.hx == hx and obj.hy == hy and not obj.broken and obj.player != player:
			return True
	return False


# returns true if there's an enemy unit, or a friendly broken or in-melee unit in the hex
#def HexIsBlocked(hx, hy, player):
#	for obj in battle.units:
#		if obj.hx == hx and obj.hy == hy:
#			if obj.player != player:
#				return True
#			if obj.broken or obj.melee_locked:
#				return True
#	return False


# returns the adjacent hex in the given direction
def GetHexInDir(hx1, hy1, hex_dir):
	xc, yc = DESTHEX[hex_dir]
	return hx1 + xc, hy1 + yc


# returns the direction needed to face hx2, hy2
def GetDirToHex(hx1, hy1, hx2, hy2):
	
	# if hex is adjacent, direction is straightforward
	if GetHexDistance(hx1, hy1, hx2, hy2) == 1:
		x_diff = hx2-hx1
		y_diff = hy2-hy1
		return DESTHEX.index((x_diff, y_diff))
	
	# otherwise, get a rough direction toward it
	x1, y1 = Hex2Screen(hx1, hy1, center=True)
	x2, y2 = Hex2Screen(hx2, hy2, center=True)
	dx, dy = x2-x1, y2-y1
	rads = atan2(-dy,dx)
	rads %= 2*pi
	degs = int(ceil(degrees(rads)))
	
	if 0 <= degs < 60:
		return 1
	elif 61 <= degs < 120:
		return 0
	elif 121 <= degs < 180:
		return 5
	elif 181 <= degs < 240:
		return 4
	elif 241 <= degs < 300:
		return 3
	return 2


# returns a pointer to a given terrain hex based on hex coordinates
def GetHexFromMap(hx, hy):
	for h in battle.map_hexes:
		if h.hx == hx and h.hy == hy:
			return h
	return None


# returns a list of all adjacent hexes, without directions, ignores if not on map
# or occupied by another unit
# hexes occupied by obj are included as open hexes
def GetOpenAdjacents(obj, hx, hy):
	adjacents = []
	for direction in range(6):
		hx2, hy2 = GetHexInDir(hx, hy, direction)
		if (hx2 == obj.hx and hy2 == obj.hy) or (HexIsOnMap(hx2, hy2) and not HexIsOccupied(hx2, hy2)):
			adjacents.append((hx2, hy2))
	return adjacents


# returns a list of all adjacent hexes in directions 0-5
# if adjacent hex is off map, returns -1, -1, -1 for that direction
def GetAdjacents(hx, hy):
	adjacents = []
	for direction in range(6):
		hx2, hy2 = GetHexInDir(hx, hy, direction)
		if not HexIsOnMap(hx2, hy2):
			adjacents.append((-1, -1, -1))
		else:
			adjacents.append((direction, hx2, hy2))
	return adjacents
	

# returns the distance between two hexes
def GetHexDistance(hx1, hy1, hx2, hy2):
	xd = hx2 - hx1
	yd = hy2 - hy1
	dd = yd - xd
	return max([abs(xd), abs(yd), abs(dd)])


# returns the integer distance between two points
def GetDistance(x1, y1, x2, y2):
	return int(abs(sqrt( (x2 - x1)**2 + (y2 - y1)**2 )))


# returns the cost in AP for the given unit to move into the given hex
# TODO: change so that any source hex can be given for path finding
def GetMoveCost(obj, hx, hy):
	h = GetHexFromMap(hx, hy)
	return h.move_cost


# GetPath - based on http://stackoverflow.com/questions/4159331/python-speed-up-an-a-star-pathfinding-algorithm
# and http://www.policyalmanac.org/games/aStarTutorial.htm
# calculates the path from hx1, hy1 to hx2, hy2 for obj with lowest AP move cost,
# counting friendly broken or in-melee, and all enemy units, as impassible
# returns a list of path hexes and total AP move cost 
def GetPath(obj, hx1, hy1, hx2, hy2):
	
	class Node:
		def __init__(self, hx, hy):
			self.hx = hx
			self.hy = hy
			self.g = 0
			self.h = 0
			self.parent = None
	
	# if destination contains any unit, it is not accessible, so return an empty list
	if HexIsOccupied(hx2, hy2):
		print 'ERROR: GetPath(): target hex ' + str(hx2) + ', ' + str(hy2) + ' is occupied'
		return [], 0
	
	open_list = set()	# contains nodes that may be traversed by the path
	closed_list = set()	# contains nodes that will be traversed by the path
	blocked_hexes = set()	# lists hexes that are blocked
	
	# build list of blocked hexes: intermediate hexes are only blocked by enemies,
	# and by friends that are either broken or in melee
	for obj2 in battle.units:
		if obj.player != obj2.player or obj2.broken or obj2.melee_locked:
			blocked_hexes.add((obj2.hx, obj2.hy))
	
	# function to calculate the H score of a given location to destination
	def GetH(hx1, hy1, hx2, hy2):
		return GetHexDistance(hx1, hy1, hx2, hy2) * 4
	
	# retrace a set of nodes and return the best path
	def RetracePath(end_node):
		path = []
		n = end_node
		done = False
		while not done:
			path.append((n.hx, n.hy))
			if n.parent is None: break	# we've reached the end
			n = n.parent
				
		path.reverse()
		path.pop(0)		# remove the first tile
		
		# return the path and the AP cost of the path
		return path, end_node.g
	
	# create the starting and ending nodes
	start = Node(hx1, hy1)
	start.h = GetH(hx1, hy1, hx2, hy2)
	start.f = start.g + start.h
	end = Node(hx2, hy2)
	
	# add the start node to the open list
	open_list.add(start)

	# while there are still tiles in the 'potentials' list
	# added window check for bug testing
	while open_list and not libtcod.console_is_window_closed():
		
		# grab the node with the best F value from the list of open tiles
		current = sorted(open_list, key=lambda inst:inst.f)[0]
			
		# move this tile from the open to the closed list
		open_list.remove(current)
		closed_list.add(current)
		
		# if we've reached our destination, return the path and cost
		if current.hx == end.hx and current.hy == end.hy:
			return RetracePath(current)
		
		# add the hexes connected to this one to the open list
		for direction in range(6):
			hx, hy = GetHexInDir(current.hx, current.hy, direction)
			
			# ignore hexes off the map
			if not HexIsOnMap(hx, hy): continue
			
			# ignore blocked hexes
			if (hx, hy) in blocked_hexes: continue
			
			# ignore hexes already on closed list
			if (hx, hy) in [(node.hx, node.hy) for node in closed_list]:
				continue
			
			# calculate g value of this node
			# TODO: doesn't calculate road bonus properly yet
			g = GetMoveCost(obj, hx, hy)
			
			# if not in open list, add it
			if not (hx, hy) in [(node.hx, node.hy) for node in open_list]:
				# create a new node
				node = Node(hx, hy)
				node.g = current.g + g
				node.h = GetH(hx, hy, end.hx, end.hy)
				node.f = node.g + node.h
				node.parent = current
				open_list.add(node)

	# if we reach here, no more open tiles!
	Message('Could not find path!')  # TEMP
	return [], 0


# select the first unit of active player, or next unit in list
def SelectNextUnit():
	
	# deselect any selected enemy units
	if battle.selected is not None:
		if battle.selected.player != battle.active_player:
			obj.DeselectMe()
	
	exit = False
	while not exit:
		for obj in battle.units:
			# ignore enemy units
			if obj.player != battle.active_player:
				continue
			
			# if nothing selected yet, select this one
			if battle.selected is None:
				obj.SelectMe()
				exit = True
			
			# otherwise, wait until we find the selected one
			else:
				if obj == battle.selected:
					obj.DeselectMe()


# check to see if hex is on map
def HexIsOnMap(hx, hy):
	if  0 <= hx <= 12 and 0 <= (hy - (hx//2)) < 8:
		return True
	return False


# returns upper left corner of given hex
# if center is true, returns the center character location of the hex
def Hex2Screen(hx, hy, center=False):
	x = (hx*9)-1
	y = 42 - (hy*6) + (hx*3)
	if center:
		x += 8
		y += 4
	return x, y


# function to output an ascii hex, 13 columns x 7 rows, with top left at x, y
def DrawHex(console, x, y):
	libtcod.console_print_ex(console, x+3, y, libtcod.BKGND_SET, libtcod.LEFT, '|-----|')
	libtcod.console_print_ex(console, x+2, y+1, libtcod.BKGND_SET, libtcod.LEFT,  '/       \\')
	libtcod.console_print_ex(console, x+1, y+2, libtcod.BKGND_SET, libtcod.LEFT,  '/         \\')
	libtcod.console_print_ex(console, x, y+3, libtcod.BKGND_SET, libtcod.LEFT,  '|           |')
	libtcod.console_print_ex(console, x+1, y+4, libtcod.BKGND_SET, libtcod.LEFT,  '\\         /')
	libtcod.console_print_ex(console, x+2, y+5, libtcod.BKGND_SET, libtcod.LEFT,  '\\       /')
	libtcod.console_print_ex(console, x+3, y+6, libtcod.BKGND_SET, libtcod.LEFT,  '|-----|')



# draws background color of hex based on terrain type
def DrawTerrain(console, h):
	x, y = Hex2Screen(h.hx, h.hy)
	
	# set background color
	libtcod.console_set_default_background(console, h.color)
	
	for ystep in range(1, 4):
		libtcod.console_rect(console, x+6-ystep, y+1+ystep, 5+(ystep*2), 1, False, flag=libtcod.BKGND_SET)
	for ystep in range(0, 2):
		libtcod.console_rect(console, x+5-ystep, y+6-ystep, 7+(ystep*2), 1, False, flag=libtcod.BKGND_SET)
	
	# draw in character decorations
	if h.terrain_type == TOWN:
		libtcod.console_set_default_foreground(console, libtcod.dark_sepia)
		for house in range(0, 30):
			if libtcod.random_get_int(0, 1, 3) < 3:
				char = 127	# little roof
			else:
				char = 254	# box
			x1 = libtcod.random_get_int(0, x+4, x+12)
			y1 = libtcod.random_get_int(0, y+2, y+6)
			libtcod.console_put_char(console, x1, y1, char, flag=libtcod.BKGND_NONE)
	
	elif h.terrain_type == RUINS:
		libtcod.console_set_default_background(console, ROAD_COLOR)
		for house in range(0, 12):
			c = libtcod.random_get_int(0, 100, 190)
			libtcod.console_set_default_foreground(console, libtcod.Color(c, c, c))
			char = 254	# box
			x1 = libtcod.random_get_int(0, x+4, x+12)
			y1 = libtcod.random_get_int(0, y+2, y+6)
			libtcod.console_put_char(console, x1, y1, char, flag=libtcod.BKGND_SET)
		
	
	# reset console colors
	libtcod.console_set_default_foreground(console, libtcod.white)
	libtcod.console_set_default_background(console, libtcod.black)


# draws an HP-style bar to the given console
def DrawBar(console, a, b, color1, color2, x, y, w):
	libtcod.console_set_default_background(console, color2)
	libtcod.console_rect(console, x, y, w, 1, True, flag=libtcod.BKGND_SET)
	
	libtcod.console_set_default_background(console, color1)
	w2 = int((float(a)/float(b)) * float(w))
	libtcod.console_rect(console, x, y, w2, 1, True, flag=libtcod.BKGND_SET)
	
	libtcod.console_set_default_foreground(console, libtcod.black)
	text = str(a) + '/' + str(b)
	libtcod.console_print_ex(console, (x+(w/2)), y, libtcod.BKGND_NONE, libtcod.CENTER, text)
	
	libtcod.console_set_default_foreground(console, libtcod.white)
	libtcod.console_set_default_background(console, libtcod.black)
	

################################################################################
#                          Random Terrain Generation                           #
################################################################################


# add a path-based feature from hex 1 to hex 2
def AddPath(hx1, hy1, hx2, hy2, path_type):
	
	# add record to battle for later painting
	if path_type == 'river':
		battle.rivers.append((hx1, hy1, hx2, hy2))
	elif path_type == 'road':
		battle.roads.append((hx1, hy1, hx2, hy2))
	
	# mark hex flags
	line = GetLine(hx1, hy1, hx2, hy2)
	for (hx, hy) in line:
		h = GetHexFromMap(hx, hy)
		if path_type == 'river':
			h.river = True
		elif path_type == 'road':
			h.road = True


# create a forest hex
def AddForest(hx, hy):
	h = GetHexFromMap(hx, hy)
	h.terrain_type = FOREST


# generate the map hexes
def GenerateMap():
	
	EDGE_HEXES = [
		(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
		(12,6),(12,7),(12,8),(12,9),(12,10),(12,11),(12,12),(12,13)
		]
	
	# randomly turn one hexside clockwise or counterclockwise
	def TurnDir(current_dir):
		if libtcod.random_get_int(0, 0, 1) == 0:
			current_dir -= 1
		else:
			current_dir += 1
		if current_dir < 0:
			current_dir += 6
		elif current_dir > 5:
			current_dir -= 6
		return current_dir
	
	# generate a random road
	def GenerateRoad():
		
		TURN_CHANCE = 20	# percent chance each hex of turning direction
		MAX_TURNS = 2		# max number of turns per road
		
		# if this is the first road on the map, pick a random edge hex and draw in from there
		if len(battle.roads) == 0:
			(hx, hy) = EDGE_HEXES[libtcod.random_get_int(0, 0, len(EDGE_HEXES)-1)]
			
			# start direction is toward center of map
			y_row = hy - (hx//2)
			# bottom half of map
			if y_row < 4:
				if hx <= 3:
					road_dir = 1
				elif 4 <= hx <= 8:
					road_dir = 0
				else:
					road_dir = 5
			else:
			# top half of map
				if hx <= 3:
					road_dir = 2
				elif 4 <= hx <= 8:
					road_dir = 3
				else:
					road_dir = 4
			
		else:
			# otherwise, find a random, already-existing road hex and
			# start from there
			road_hexes = []
			for h in battle.map_hexes:
				if h.road:
					road_hexes.append((h.hx, h.hy))
			(hx, hy) = road_hexes[libtcod.random_get_int(0, 0, len(road_hexes)-1)]
			
			# pick a random direction
			road_dir = -1
			
			# get list of adjacent hexes and shuffle it
			adjacents = GetAdjacents(hx, hy)
			shuffle(adjacents)
			
			# try to find one that's on the map and not a road hex
			for direction, hx2, hy2 in adjacents:
				if direction < 0: continue	# not on map
				h = GetHexFromMap(hx2, hy2)
				if not h.road:
					road_dir = direction	# found a good one!
					break
			
			# if road_dir is still -1, we couldn't find a good direction
			if road_dir == -1:
				return
		
		# mark starting position
		hx1, hy1 = hx, hy
		
		turns = 0
		while True:
			
			# chance of turning direction if we didn't just start a new segment
			if turns < MAX_TURNS and hx != hx1 and hy != hy1:
				if libtcod.random_get_int(0, 1, 100) <= TURN_CHANCE:
					turns += 1
					
					# add current segment
					AddPath(hx1, hy1, hx, hy, 'road')
					
					# mark new starting position
					hx1, hy1 = hx, hy
					
					# choose new direction
					road_dir = TurnDir(road_dir)
			
			next_hx, next_hy = GetHexInDir(hx, hy, road_dir)
			
			# if next step would be off map, add current segement and return
			if not HexIsOnMap(next_hx, next_hy):
				AddPath(hx1, hy1, hx, hy, 'road')
				return
			
			# step to next hex
			hx, hy = next_hx, next_hy 
	
	# test to see whether a town is generated
	# if force_town, the first suitable hex will spawn a town
	def GenerateTown(force_town = False):
		
		# percent chance that a suitable hex will spawn a town
		TOWN_CHANCE = 60
		
		# create a copy of the list of hexes
		map_hexes = list(battle.map_hexes)
		
		# any hex that is a road hex and is adjacent to more than two road hexes
		# has a chance of spawning a town
		for h in map_hexes:
			if h.road:
				adjacent_roads = 0
				adjacents = GetAdjacents(h.hx, h.hy)
				for direction, hx, hy in adjacents:
					if direction < 0: continue	# off map
					h2 = GetHexFromMap(hx, hy)
					if h2.road:
						adjacent_roads += 1
				# check road total
				if adjacent_roads > 2:
					if force_town or libtcod.random_get_int(0, 1, 100) <= TOWN_CHANCE:
						h.SetTerrain(TOWN)
						h.landmark_name = 'Fooberg'	# TODO random names
						return
	
	
	# start by filling map with open ground hexes
	for hx in range(0, 13):
		ystart = hx//2
		for hy in range(ystart, ystart + 8):
			battle.map_hexes.append(Hex(hx, hy, OPEN_GROUND))
	
	# random map generation
	
	# Road Network
	
	# determine how many roads the map will have: 0, 0, 1, 2, 3
	num_roads = libtcod.random_get_int(0, 0, 4)
	if num_roads > 0: num_roads -= 1
	num_roads = 3  # TEMP
	
	while num_roads > 0:
		GenerateRoad()
		num_roads -= 1
	
	# check for town generation
	GenerateTown(force_town=True)


# generate a pre-designed text map
def GenerateTestMap():
	
	for hx in range(0, 13):
		ystart = hx//2
		for hy in range(ystart, ystart + 8):
			battle.map_hexes.append(Hex(hx, hy, OPEN_GROUND))
	
	# create the town
	h = GetHexFromMap(3, 4)
	h.terrain_type = TOWN
	h.landmark_name = 'Fooberg'
	
	# create the ruins
	h = GetHexFromMap(9, 8)
	h.terrain_type = RUINS
	
	# create some forest
	AddForest(1, 3)
	AddForest(1, 4)
	AddForest(2, 4)
	
	AddForest(9, 10)
	AddForest(9, 9)
	AddForest(10, 9)
	
	AddForest(5, 7)
	AddForest(6, 7)
	
	AddForest(2, 2)
	AddForest(3, 2)
	
	# create rivers
	AddPath(12, 10, 8, 6, 'river')
	AddPath(8, 6, 2, 6, 'river')
	AddPath(2, 6, 2, 8, 'river')
	
	# lay down roads
	AddPath(9, 4, 3, 4, 'road')
	AddPath(3, 4, 3, 8, 'road')
	AddPath(3, 4, 0, 1, 'road')
	AddPath(5, 4, 9, 8, 'road')

	# generate terrain stats for each hex
	for h in battle.map_hexes:
		h.SetTerrain()


# paint map terrain to map console
def PaintMap():
	
	def PaintPath(hx1, hy1, hx2, hy2, path_type):
		# get the line path
		x1, y1 = Hex2Screen(hx1, hy1, center=True)
		x2, y2 = Hex2Screen(hx2, hy2, center=True)
		points = GetLine(x1, y1, x2, y2) 
		
		if path_type == 'river':
			col = libtcod.blue
			size = 3
		else:
			col = ROAD_COLOR
			size = 3
		libtcod.console_set_default_background(session.map_console, col)
		for (x, y) in points:
			libtcod.console_rect(session.map_console, x-((size-1)//2), y-((size-1)//2), size, size-1, False, flag=libtcod.BKGND_SET)
		libtcod.console_set_default_background(session.map_console, libtcod.black)
	
	# clear map console
	libtcod.console_clear(session.map_console)
	
	# draw hex grid with open ground background
	libtcod.console_set_default_background(session.map_console, OPEN_GROUND_COLOR)
	libtcod.console_set_default_foreground(session.map_console, libtcod.black)
	for x in range(13):
		offset = 0
		if IsOdd(x):
			offset = 3
		for y in range (8):
			DrawHex(session.map_console, (x*9)+1, (y*6)+1+offset)
	libtcod.console_set_default_background(session.map_console, libtcod.black)
	libtcod.console_set_default_foreground(session.map_console, libtcod.white)
	
	# draw terrain to map
	for h in battle.map_hexes:
		DrawTerrain(session.map_console, h)
	
	# fill in terrain gaps, skipping outer edge
	for x in range(1, MAP_WIDTH-1):
		for y in range(1, MAP_HEIGHT-1):
			col1 = libtcod.console_get_char_background(session.map_console, x-1, y)
			col2 = libtcod.console_get_char_background(session.map_console, x+2, y)
			if col1 == col2 == FOREST_COLOR:
				libtcod.console_set_char_background(session.map_console, x, y, col1, flag=libtcod.BKGND_SET)
			
			col1 = libtcod.console_get_char_background(session.map_console, x, y-1)
			col2 = libtcod.console_get_char_background(session.map_console, x, y+2)
			if col1 == col2 == FOREST_COLOR:
				libtcod.console_set_char_background(session.map_console, x, y, col1, flag=libtcod.BKGND_SET)		
	
	# draw rivers
	for (hx1, hy1, hx2, hy2) in battle.rivers:
		PaintPath(hx1, hy1, hx2, hy2, 'river')
	
	# draw roads
	for (hx1, hy1, hx2, hy2) in battle.roads:
		PaintPath(hx1, hy1, hx2, hy2, 'road')


################################################################################
#                                   AI Control                                 #
################################################################################


# allow AI to act
def DoAITurn():
	# get list of active units
	my_units = []
	for obj in battle.units:
		if obj.player == battle.active_player:
			my_units.append(obj)
	
	# TEMP shuffle list
	shuffle(my_units)
	
	# go through each unit and act with it
	for obj in my_units:
		
		# select this unit
		obj.SelectMe()
		RenderAll()
		
		# while we still have AP remaining, and we haven't received a stop
		# result from AIAction, keep acting with this unit
		
		# TEMP
		for i in range(20):
			# make sure unit is still unbroken and alive
			if obj.broken: break
			if obj not in battle.units: break
			
			finished = obj.AIAction()
			if finished: break
		
	Message('DEBUG: AI Done!')


# advance to next player-turn
def NextPlayerTurn():
	if battle.active_player == 1:
		battle.current_turn += 1
		battle.active_player = 0
	else:
		battle.active_player = 1
	
	# reset units for newly active player
	for obj in battle.units:
		if obj.player == battle.active_player:
			obj.Reset()
	
	if battle.selected is not None:
		battle.selected.DeselectMe()
	
	SaveGame()
	DisplayTurnInfo()
	
	# do retreat movets for broken units
	for obj in battle.units:
		if obj.broken and obj.player == battle.active_player:
			if not obj.RetreatMove():
				# morale test to recover from broken
				d1, d2 = Roll2D6()
				if d1 + d2 <= obj.morale:
					Message(obj.name + ' passes its Morale test and is no longer Broken.')
					obj.broken = False
					obj.DrawSprite()
				else:
					Message(obj.name + ' did not pass its Morale test and is still Broken.')
	
	RenderAll()


# Main rendering function, draws everything to the main console
def RenderAll():
	# clear the master console
	libtcod.console_clear(con)
	
	# draw menu bar
	libtcod.console_hline(con, 1, 0, 70)
	libtcod.console_print(con, 1, 1, '|  ESC - Game    |  F1 - Help    |  F2 - Scenario    |  F3 - Army    |')
	libtcod.console_hline(con, 0, 2, SCREEN_WIDTH-CON_WIDTH)
	
	# blit map console to the master console
	libtcod.console_blit(session.map_console, 0, 0, MAP_WIDTH, MAP_HEIGHT, con, 0, 3)
	
	# draw any units
	for unit in battle.units:
		unit.DrawMe(con)
	
	# display melee locks
	libtcod.console_set_default_foreground(con, libtcod.red)
	for (obj1, obj2) in battle.melee_locks:
		x1, y1 = Hex2Screen(obj1.hx, obj1.hy, center=True)
		x2, y2 = Hex2Screen(obj2.hx, obj2.hy, center=True)
		x, y = int((x1+x2)/2), int((y1+y2)/2)+3
		libtcod.console_put_char(con, x, y, 21, libtcod.BKGND_NONE) 
	libtcod.console_set_default_foreground(con, libtcod.white)
	
	y = 0
	
	# draw info window frame
	libtcod.console_print_frame(con, SCREEN_WIDTH-CON_WIDTH, y, CON_WIDTH, SCREEN_HEIGHT)
	
	# display turn and active player info
	text = 'Turn: ' + str(battle.current_turn) + '/' + str(battle.turn_limit)
	libtcod.console_print(con, SCREEN_WIDTH-CON_WIDTH+2, y+1, text)
	
	# display game title
	text = 'WarHexer ' + VERSION
	libtcod.console_print_ex(con, SCREEN_WIDTH-4, y+1, libtcod.BKGND_NONE, libtcod.RIGHT, text)
	
	# display current victory points
	text = 'Score: ' + str(battle.player0_score) + '-' + str(battle.player1_score)
	libtcod.console_print(con, SCREEN_WIDTH-CON_WIDTH+2, y+3, text)
	
	# display active player reminder
	text = 'Player: ' + str(battle.active_player+1)
	libtcod.console_print_ex(con, SCREEN_WIDTH-4, y+3, libtcod.BKGND_NONE, libtcod.RIGHT, text)
	
	libtcod.console_hline(con, SCREEN_WIDTH-CON_WIDTH+1, y+4, CON_WIDTH-2)
	
	# blit terrain info console
	libtcod.console_blit(session.terrain_con, 0, 0, CON_WIDTH-4, TERRAIN_CON_HEIGHT, con, SCREEN_WIDTH-CON_WIDTH+2, y+5)
	
	libtcod.console_hline(con, SCREEN_WIDTH-CON_WIDTH+1, TERRAIN_CON_HEIGHT+5+y, CON_WIDTH-2)
	
	y += TERRAIN_CON_HEIGHT+6
	
	# blit stat console of any selected unit
	if battle.selected is not None:
		libtcod.console_blit(battle.selected.stat_console, 0, 0, CON_WIDTH-4, STAT_CON_HEIGHT, con, SCREEN_WIDTH-CON_WIDTH+2, y)
	
	y+=STAT_CON_HEIGHT
	
	#libtcod.console_hline(con, SCREEN_WIDTH-CON_WIDTH+1, y, CON_WIDTH-2)
	
	# display game message console
	y = SCREEN_HEIGHT - MSG_CON_HEIGHT - 1
	libtcod.console_hline(con, SCREEN_WIDTH-CON_WIDTH+1, y-1, CON_WIDTH-2)
	libtcod.console_blit(session.msg_con, 0, 0, CON_WIDTH-4, MSG_CON_HEIGHT, con, SCREEN_WIDTH-CON_WIDTH+2, y)
	
	# finally, blit the master console to the screen
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
	libtcod.console_flush()


# get user input
def HandleInput():
	global battle
	global key, mouse
	
	# check for keyboard or mouse input
	libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
	
	# mouse stuff first
	mx, my = mouse.cx, mouse.cy
	
	# check mouse position against last recorded one
	if (mx, my) != session.mouseover:
		session.mouseover = (mx, my)
		# update displayed terrain info
		hx, hy = GetHex(mx, my)
		session.UpdateTerrainCon(hx, hy)
		RenderAll()
	
	# debug function
	if mouse.mbutton_pressed:
		hx, hy = GetHex(mx, my)
		Message('Clicked on ' + str(mx) + ',' + str(my) + '; hex:' + str(hx) + ',' + str(hy))
		RenderAll()
		return None
	
	# if cursor is over map
	if mx > 0 and mx <= MAP_WIDTH:
		
		# left mouse button clicked on map
		if mouse.lbutton_pressed:
			hx, hy = GetHex(mx, my)
			if hx < 0 and hy < 0:
				return None
			
			# de-select any selected unit
			if battle.selected is not None:
				battle.selected.DeselectMe()
			
			# select any unit in this hex
			for obj in battle.units:
				if obj.hx == hx and obj.hy == hy:
					obj.SelectMe()
					break
			RenderAll()
			return None
		
		# right mouse button clicked on map
		elif mouse.rbutton_pressed:
			hx, hy = GetHex(mx, my)
			if not HexIsOnMap(hx, hy):
				return None
			
			# a unit is selected
			if battle.selected is not None:
				if battle.selected.player == battle.active_player:
					# see if this hex is occupied
					if HexIsOccupied(hx, hy):
						# try to init an attack against this hex
						battle.selected.InitAttack(hx, hy)
					else:
						# if not occupied, plot a path to it
						pass
						#battle.selected.MovePath(hx, hy)
					RenderAll()
					return None
	
	if key.vk == libtcod.KEY_ESCAPE:
		# see if we want to save and quit game
		choice = InGameMenu()
		if choice:
			return 'exit'
		RenderAll()
	
	# scenario screen
	elif key.vk == libtcod.KEY_F2:
		ScenarioMenu()
		RenderAll()
	
	elif key.vk == libtcod.KEY_ENTER:
		# end player turn
		NextPlayerTurn()
		
		if battle.active_player == 1:
			# do AI turn
			DoAITurn()
			RenderAll()
			NextPlayerTurn()
		
	elif key.vk == libtcod.KEY_TAB:
		# select first player unit, or next unit in list
		SelectNextUnit()
		RenderAll()
	
	else:
		# test for other keys
		key_char = chr(key.c)
		
		if battle.selected is not None:
			if battle.selected.player == battle.active_player:
				if key_char == 'q':
					battle.selected.ChangeFacing(-1)
					RenderAll()
				elif key_char == 'e':
					battle.selected.ChangeFacing(1)
					RenderAll()
				elif key_char == 'w':
					battle.selected.MoveForward()
					RenderAll()
				elif key_char == 'f':
					battle.selected.FreeAttempt()
					RenderAll()
	
	return None


# save current battle state to file
def SaveGame():
	# clear unit consoles
	for obj in battle.units:
		del obj.stat_console
		del obj.portrait
		del obj.sprite
	file = shelve.open('savegame', 'n')
	file['battle'] = battle
	file.close
	print 'Game saved'
	# rebuild unit consoles
	for obj in battle.units:
		obj.SetupConsoles()


# load game state from file
def LoadGame():
	global battle
	file = shelve.open('savegame', 'r')
	battle = file['battle']
	file.close()
	# rebuild unit consoles
	for obj in battle.units:
		obj.SetupConsoles()
	print 'Game loaded'


################################################################################
#                               Main Battle Loop                               #
################################################################################

# set up and run a battle, if load_battle is true then load last saved game
def DoBattle(roster, load_battle = False):
	
	global battle, session
	
	# if we're continuing a battle, load it
	# TODO: test loading and if failsm, show an error message and quit to main menu
	if load_battle:
		LoadGame()
		session = Session()	# create session object
		PaintMap()
		
	else:
		# create battle object
		battle = Battle()
		
		# create session object
		session = Session()
		
		# generate the battle map and draw the map console
		#GenerateMap()
		GenerateTestMap()
		PaintMap()
		
		# spawn player's units
		
		# TODO: read from roster
		
		# player's units
		SpawnUnit('Hearthguard', 0, 5, 3, 0)
		SpawnUnit('Hearthguard', 0, 6, 3, 0)
		SpawnUnit('Hearthguard', 0, 7, 4, 0)
		
		#SpawnUnit('Irregulars', 0, 3, 2, 0)
		#SpawnUnit('Irregulars', 0, 9, 5, 0)
		
		SpawnUnit('Longbowmen', 0, 5, 2, 0)
		SpawnUnit('Longbowmen', 0, 7, 3, 0)
		
		SpawnUnit('Knights', 0, 4, 2, 0)
		SpawnUnit('Knights', 0, 8, 4, 0)
		
		#SpawnUnit('Noble Riders', 0, 3, 1, 0)
		#SpawnUnit('Noble Riders', 0, 9, 4, 0)
		
		
		
		# enemy units
		SpawnUnit('Ghouls', 1, 5, 8, 3)
		SpawnUnit('Ghouls', 1, 6, 9, 3)
		SpawnUnit('Ghouls', 1, 7, 9, 3)
		
		#SpawnUnit('Skeletal Host', 1, 4, 9, 3)
		#SpawnUnit('Skeletal Host', 1, 8, 11, 3)
		
		SpawnUnit('Skeleton Archers', 1, 5, 9, 3)
		SpawnUnit('Skeleton Archers', 1, 7, 10, 3)
		
		#SpawnUnit('Vampire Lords', 1, 5, 8, 3)
		#SpawnUnit('Vampire Lords', 1, 7, 9, 3)
		
		SpawnUnit('Knightmares', 1, 4, 8, 3)
		SpawnUnit('Knightmares', 1, 8, 10, 3)
		
		Message('Battle commences!')
	
		# save game state
		SaveGame()
	
	DisplayTurnInfo()
	
	# render the screen for the first time
	RenderAll()
	
	# this will exit us out of the battle if the window is closed
	while not libtcod.console_is_window_closed():
		
		# used with limit FPS so program doesn't use 100% CPU
		libtcod.console_flush()
		
		# handle keys and exit game if needed
		player_action = HandleInput()
		if player_action == 'exit':
			break

	del battle
	del session


################################################################################
#                                In-Game Menu                                  #
################################################################################

# returns True if we're quitting the battle

def InGameMenu():
	
	# darken background
	temp = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
	libtcod.console_clear(temp)
	libtcod.console_blit(temp, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1.0, 0.5)
	libtcod.console_delete(temp)
	
	# highlight menu selection
	libtcod.console_print(0, 4, 1, 'ESC - Return')
	
	W = SCREEN_WIDTH-30
	H = SCREEN_HEIGHT-6
	
	menu_console = libtcod.console_new(W, H)
	libtcod.console_clear(menu_console)
	libtcod.console_print_frame(menu_console, 0, 0, W, H)
	
	text = 'ESC to return to game'
	libtcod.console_print_ex(menu_console, W/2, 16, libtcod.BKGND_NONE, libtcod.CENTER, text)
	text = 'Save and [Q]uit'
	libtcod.console_print_ex(menu_console, W/2, 18, libtcod.BKGND_NONE, libtcod.CENTER, text)
	text = '[A]bandon Game and Delete Saved Game'
	libtcod.console_print_ex(menu_console, W/2, 20, libtcod.BKGND_NONE, libtcod.CENTER, text)
	
	# blit menu console to screen
	libtcod.console_blit(menu_console, 0, 0, W, H, 0, (SCREEN_WIDTH/2)-(W/2), (SCREEN_HEIGHT/2)-(H/2))
	
	menu_exit = False
	while not menu_exit:
		# get input from user
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		
		if key.vk == libtcod.KEY_ESCAPE:
			menu_exit = True
		
		key_char = chr(key.c)
		
		if key_char == 'q' or libtcod.console_is_window_closed():
			SaveGame()
			return True
		
		elif key_char == 'a':
			# TODO: get confirmation
			if os.path.exists('savegame'):
				os.remove('savegame')
			return True
			
		# refresh the screen
		libtcod.console_flush()
	
	return False


# scenario summary screen
def ScenarioMenu():
	
	# TEMP: will be handled by a single in-game menu handler
	
	# darken background
	temp = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
	libtcod.console_clear(temp)
	libtcod.console_blit(temp, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0, 1.0, 0.5)
	libtcod.console_delete(temp)
	
	# highlight menu selection
	libtcod.console_print(0, 4, 1, 'ESC - Return')
	
	W = SCREEN_WIDTH-30
	H = SCREEN_HEIGHT-6
	
	menu_console = libtcod.console_new(W, H)
	libtcod.console_clear(menu_console)
	libtcod.console_print_frame(menu_console, 0, 0, W, H)
	
	# blit menu console to screen
	libtcod.console_blit(menu_console, 0, 0, W, H, 0, (SCREEN_WIDTH/2)-(W/2), (SCREEN_HEIGHT/2)-(H/2))
	
	menu_exit = False
	while not menu_exit:
		# get input from user
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		
		if key.vk == libtcod.KEY_ESCAPE or libtcod.console_is_window_closed():
			menu_exit = True
		
		# refresh the screen
		libtcod.console_flush()


################################################################################
#                                  Main Menu                                   #
################################################################################

# TODO: error checking for continue game
def MainMenu():
	title_img = libtcod.image_load('title.png')
	exit_game = False
	while not exit_game:
		
		# display main menu
		libtcod.console_clear(con)
		libtcod.image_blit_rect(title_img, con, 0, 3, -1, -1, libtcod.BKGND_SET)
		
		libtcod.console_print_ex(con, SCREEN_WIDTH-4, 1, libtcod.BKGND_NONE, libtcod.RIGHT, VERSION)
		
		y = 35
		libtcod.console_print_ex(con, SCREEN_WIDTH/2, y, libtcod.BKGND_NONE, libtcod.CENTER, 'Roguelike Epic Fanasty Battles')
		
		y = 38
		libtcod.console_print_frame(con, 44, y, 24, 5)
		libtcod.console_print(con, 49, y+2, '[N]ew Campaign')
		
		# check for existence of save file
		save_file = False
		libtcod.console_set_default_foreground(con, libtcod.dark_grey)
		if os.path.exists('savegame'):
			save_file = True
			libtcod.console_set_default_foreground(con, libtcod.white)
		
		libtcod.console_print_frame(con, (SCREEN_WIDTH/2)-12, y, 25, 5)
		libtcod.console_print_ex(con, (SCREEN_WIDTH/2), y+2, libtcod.BKGND_NONE, libtcod.CENTER, '[C]ontinue')
		
		libtcod.console_set_default_foreground(con, libtcod.white)
		
		libtcod.console_print_frame(con, 99, y, 24, 5)
		libtcod.console_print(con, 108, y+2, '[Q]uit')
		
		y = 50
		text = 'Built on Python 2.7.3 and Libtcod 1.5.1'
		libtcod.console_print_ex(con, SCREEN_WIDTH/2, y, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# blit main console to screen
		libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
		
		refresh_menu = False
		while not refresh_menu and not exit_game:
			
			# get input from user
			libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
			
			if key.vk == libtcod.KEY_ESCAPE or libtcod.console_is_window_closed():
				exit_game = True
			
			# get pressed key
			key_char = chr(key.c)
			
			# new game
			if key_char == 'n':
				DoBattle(None)
				#force_selection = ForceSelectionMenu()
				#if force_selection is not None:
				#	force_purchase = ForcePurchaseMenu(force_selection)
				#	if len(force_purchase) > 0:
				#		DoBattle(force_purchase)
				refresh_menu = True
			# continue, only allow if save file exists
			elif key_char == 'c' and save_file:
				DoBattle(None, load_battle = True)
				refresh_menu = True
			# quit
			elif key_char == 'q':
				exit_game = True
			# refresh the screen
			libtcod.console_flush()


################################################################################
#                            Force Purchase Menu                               #
################################################################################

# allow player to spend points on units
# will eventually be integrated into campaign system
def ForcePurchaseMenu(selected_force):
	
	def UpdateScreen():
		
		libtcod.console_clear(menu_console)
		libtcod.console_print_frame(menu_console, 0, 0, W, H)
		
		libtcod.console_print_ex(menu_console, W/2, 1, libtcod.BKGND_NONE, libtcod.CENTER, 'Assemble your Army')
		libtcod.console_print_ex(menu_console, W-4, 1, libtcod.BKGND_NONE, libtcod.RIGHT, 'Points Remaining: ' + str(points))
		text = 'W and S to move cursor, Space to purchase, Backspace to cancel last purchase'
		libtcod.console_print_ex(menu_console, W/2, H-3, libtcod.BKGND_NONE, libtcod.CENTER, text)
		text = 'Enter when done, ESC or Q to quit'
		libtcod.console_print_ex(menu_console, W/2, H-2, libtcod.BKGND_NONE, libtcod.CENTER, text)
		
		# available unit info
		libtcod.console_print(menu_console, 4, 6, 'Available Units')
		libtcod.console_print(menu_console, 4, 10, 'Name')
		libtcod.console_print(menu_console, 24, 10, 'Points Cost')
		y = 12
		for u in units:
			if u == selected_unit:
				libtcod.console_set_default_foreground(menu_console, libtcod.light_red)
			libtcod.console_print(menu_console, 4, y, u.name)
			libtcod.console_print(menu_console, 24, y, str(u.points_cost))
			
			libtcod.console_set_default_foreground(menu_console, libtcod.light_grey)
			text = u.rating + ' ' + u.unit_class
			libtcod.console_print(menu_console, 6, y+1, text)
			
			libtcod.console_set_default_foreground(menu_console, libtcod.white)
			y += 4
		
		# selected unit type info
		u = selected_unit
		y = 10
		libtcod.console_print(menu_console, 50, y, u.name)
		text = u.rating + ' ' + u.unit_class
		libtcod.console_print(menu_console, 50, y+1, text)
		
		text = 'Melee: '
		if u.melee > 0:
			text += str(u.melee)
		else:
			text += '-'
		libtcod.console_print(menu_console, 50, y+3, text)
		
		text = 'Ranged: '
		if u.ranged > 0:
			text += str(u.ranged) + ' (' + str(u.attack_range) + ')'
		else:
			text += '-'
		libtcod.console_print(menu_console, 50, y+4, text)
		
		libtcod.console_print(menu_console, 50, y+5, 'Defense: ' + str(u.defense))
		libtcod.console_print(menu_console, 50, y+6, 'Skill: ' + str(u.skill))
		libtcod.console_print(menu_console, 50, y+7, 'Morale: ' + str(u.morale))
		libtcod.console_print(menu_console, 50, y+8, 'Unit Columns: ' + str(u.columns))
		
		text = 'Special: '
		if len(u.special) == 0:
			text += 'None'
		else:
			for l in u.special:
				if u.special.index(l) != 0:
					text += ', '
				text += l
		libtcod.console_print(menu_console, 50, y+9, text)
		
		# unit type description
		desc_lines = wrap(u.description, 28, initial_indent = ' ')
		ys = 0
		for line in desc_lines:
			libtcod.console_print(menu_console, 50, y+11+ys, line)
			ys+=1
		
		# roster info
		libtcod.console_print(menu_console, 95, 6, 'Army Roster')
		libtcod.console_print(menu_console, 95, 10, 'Name')
		libtcod.console_print(menu_console, 115, 10, 'Points Cost')
		libtcod.console_print(menu_console, 115, 40, 'Total')
		libtcod.console_print(menu_console, 115, 41, str(roster_total))
		
		y = 12
		for u in roster:
			libtcod.console_print(menu_console, 95, y, u.name)
			libtcod.console_print(menu_console, 115, y, str(u.points_cost))
			y += 2
		
		libtcod.console_blit(menu_console, 0, 0, W, H, 0, (SCREEN_WIDTH/2)-(W/2), (SCREEN_HEIGHT/2)-(H/2))
	
	
	# build list of availible unit classes
	units = []
	for u in unit_classes:
		if u.civ_num == selected_force:
			if len(units) > 0:
				units[-1].child = u
				units.append(u)
				units[-1].parent = units[-2]
			else:
				units.append(u)
				units[0].parent = None
			units[-1].child = None
	
	libtcod.console_clear(0)
	
	# same as size of InGameMenu() TODO: set at start of file
	W = SCREEN_WIDTH-30
	H = SCREEN_HEIGHT-6
	menu_console = libtcod.console_new(W, H)
	
	# start with an empty roster
	roster = []
	roster_total = 0
	points = 1000
	
	# start with first available unit selected and display screen
	selected_unit = units[0]
	UpdateScreen()
	
	# blit menu console to screen
	libtcod.console_blit(menu_console, 0, 0, W, H, 0, (SCREEN_WIDTH/2)-(W/2), (SCREEN_HEIGHT/2)-(H/2))
	
	menu_exit = False
	while not menu_exit:
		# get input from user
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		
		# cancel and quit
		if key.vk == libtcod.KEY_ESCAPE:
			roster = []
			menu_exit = True
		
		# done
		elif key.vk == libtcod.KEY_ENTER:
			if len(roster) > 0:
				menu_exit = True
		
		# purchase unit
		elif key.vk == libtcod.KEY_SPACE:
			if points >= u.points_cost:
				roster.append(selected_unit)
				roster_total += selected_unit.points_cost
				points -= selected_unit.points_cost
				UpdateScreen()
		
		# cancel last purchase
		elif key.vk == libtcod.KEY_BACKSPACE:
			if len(roster) > 0:
				last_unit = roster[-1]
				roster_total -= last_unit.points_cost
				points += last_unit.points_cost
				roster.pop()
				UpdateScreen()
		
		key_char = chr(key.c)
		
		if key_char == 'q' or libtcod.console_is_window_closed():
			roster = []
			menu_exit = True
		
		elif key_char == 's':
			if selected_unit.child is not None:
				selected_unit = selected_unit.child
				UpdateScreen()
		
		elif key_char == 'w':
			if selected_unit.parent is not None:
				selected_unit = selected_unit.parent
				UpdateScreen()
			
		# refresh the screen
		libtcod.console_flush()
	
	return roster


################################################################################
#                            Force Selection Menu                              #
################################################################################

# first step in starting a new campaign/game
def ForceSelectionMenu():
	
	FORCES = ['Human Kingdoms', 'Undead Lords']
	
	SHIELDS = []
	SHIELDS.append(libtcod.image_load('human_shield.png'))
	SHIELDS.append(libtcod.image_load('undead_shield.png'))
	
	DESCS = ["The Human Kingdoms exist in " +
		"a constant state of civil war, and are seldom able to unite their powers. " +
		"Kingdoms specialize in training a particular type of warrior, and when " +
		"a hero manages to raise a army, each regiment is drawn from " +
		"one particular region. Human forces are well-rounded, can use gunpowder " +
		"weapons, and have some access to magic though no particular talent for it.",
		
		"The Undead are led by charismatic Necromancer Lords whose mastery of death magic " +
		"raises and controls their forces. While their soldiers are often slow and " +
		"clumsy, they are led on by the unstoppable will of their master. Undead soldiers " +
		"wield the weapons they had when they were alive, while a few spirits and monsters " +
		"are purely the creations of the diabolical Necromancers."]
	
	selected_force = 0
	
	def UpdateScreen():
		libtcod.console_clear(con)
		
		x = 34
		y = 6
		for f in FORCES:
			if selected_force == FORCES.index(f):
				libtcod.console_set_default_foreground(con, libtcod.white)
			else:
				libtcod.console_set_default_foreground(con, libtcod.dark_grey)
			libtcod.console_print_frame(con, 18+x, y, 30, 24)
			libtcod.console_print_ex(con, 33+x, y+1, libtcod.BKGND_NONE, libtcod.CENTER, f)
			
			libtcod.image_blit_rect(SHIELDS[FORCES.index(f)], con, 26+x, y+3, -1, -1, libtcod.BKGND_SET)
			
			x+=40
		
		libtcod.console_set_default_foreground(con, libtcod.white)
		
		# grab force description, split into lines, and display
		desc_lines = wrap(DESCS[selected_force], 42, initial_indent = ' ')
		
		y = y+26
		for line in desc_lines:
			libtcod.console_print(con, 66, y, line)
			y+=1
		
		text = 'A and D to move hightlight, ENTER to select, ESC OR Q to Quit to Main Menu'
		libtcod.console_print_ex(con, SCREEN_WIDTH/2, 50, libtcod.BKGND_NONE, libtcod.CENTER, text)
		libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
	
	UpdateScreen()
	
	selected, exit = False, False
	while not selected and not exit:
		
		# get input from user
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		
		if key.vk == libtcod.KEY_ESCAPE or libtcod.console_is_window_closed():
			exit = True
		elif key.vk == libtcod.KEY_ENTER:
			selected = True
		
		# get pressed key
		key_char = chr(key.c)
		
		# move selection or quit
		if key_char == 'a':
			if selected_force > 0:
				selected_force -= 1
				UpdateScreen()
		elif key_char == 'd':
			if selected_force < 1:
				selected_force += 1
				UpdateScreen()
		# quit
		elif key_char == 'q':
			exit = True
		
		libtcod.console_flush()
	
	if exit: return None
	return selected_force
	


#############################################################
#                       Main Script                         #
#############################################################

global mouse, key
global unit_classes

# set up basic stuff
os.environ['SDL_VIDEO_CENTERED'] = '1'		# center window on screen
libtcod.console_set_custom_font('terminal10x16_gs_ro.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'WarHexer', False)
libtcod.sys_set_fps(LIMIT_FPS)
libtcod.console_set_keyboard_repeat(0, 0)

# create the main display console
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.console_set_default_background(con, libtcod.black)
libtcod.console_set_default_foreground(con, libtcod.white)
libtcod.console_set_alignment(con, libtcod.LEFT)
libtcod.console_clear(con)

# create mouse and key event holders
mouse = libtcod.Mouse()
key = libtcod.Key()

# set up unit types
unit_classes = []
for stats in UNIT_CLASS_DEFS:
	new_type = UnitType(stats)
	unit_classes.append(new_type)

# TEMP - for testing
#DoBattle(None)

# display the main game menu
MainMenu()

# END #
