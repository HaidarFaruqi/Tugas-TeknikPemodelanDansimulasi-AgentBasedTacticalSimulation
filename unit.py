import pygame
import random
import math
from config import *

class Unit:
    def __init__(self, x, y, unit_type, faction, hp, attack_power, defense, attack_range, speed, name="Unit"):
        self.x = x
        self.y = y
        self.unit_type = unit_type
        self.faction = faction
        self.max_hp = hp
        self.hp = hp
        self.initial_max_hp = hp
        self.attack_power = attack_power
        self.defense = defense
        self.attack_range = attack_range
        self.speed = speed
        self.name = name
        self.orientation = 0
        self.target = None
        self.is_destroyed = False
        self.is_fleeing = False
        self.is_on_frontline = False
        self.is_resting = False
        self.ammo = 0
        if self.unit_type == "Immortal" and self.faction == "Persia":
            self.ammo = PERSIAN_INITIAL_AMMO

        if ENABLE_MORALE:
            if self.faction == "Sparta":
                self.initial_max_morale = SPARTAN_MAX_MORALE_CAP
                self.morale = SPARTAN_MAX_MORALE_CAP
            else:
                self.initial_max_morale = DEFAULT_MORALE
                self.morale = DEFAULT_MORALE
        else:
            self.initial_max_morale = 100
            self.morale = 100

        if self.faction == "Sparta":
            self.orientation = 0
            self.base_color = RED
        else:
            self.orientation = 2
            self.base_color = IMMORTAL_COLOR_RANGED
        
        self.color = self.base_color
        self._set_unit_specific_colors()
        self._apply_type_specific_attributes()

    def _set_unit_specific_colors(self):
        if self.unit_type == "Spearman" and self.faction == "Sparta":
            self.color = RED
        elif self.unit_type == "Immortal" and self.faction == "Persia":
            self.color = IMMORTAL_COLOR_RANGED if self.ammo > 0 else IMMORTAL_COLOR_MELEE

    def _apply_type_specific_attributes(self):
        if self.unit_type == "Spearman" and self.faction == "Sparta":
            self.speed = 1
            self.attack_range = 1
        elif self.unit_type == "Immortal" and self.faction == "Persia":
            self.max_hp = PERSIAN_INFANTRY_HP
            self.hp = self.max_hp
            self.initial_max_hp = self.max_hp
            self.defense = PERSIAN_INFANTRY_DEFENSE
            if self.ammo > 0:
                self.attack_power = PERSIAN_RANGED_ATTACK_POWER
                self.attack_range = PERSIAN_RANGED_ATTACK_RANGE
            else:
                self.attack_power = PERSIAN_MELEE_ATTACK_POWER_WEAK
                self.attack_range = 1
            self.speed = 1

    def draw(self, screen):
        if screen is None or self.is_destroyed:
            return

        current_display_color = self.color
        if ENABLE_MORALE:
            if self.is_fleeing:
                if pygame.time.get_ticks() % 500 < 250:
                    current_display_color = WHITE
            elif self.morale < MORALE_LOW_THRESHOLD and self.morale > MORALE_ROUT_THRESHOLD:
                current_display_color = tuple(max(0, c - 50) for c in self.color)

        rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, current_display_color, rect)

        bar_max_width = GRID_SIZE - 2 * STATUS_BAR_PADDING
        morale_bar_y = rect.top + GRID_SIZE - STATUS_BAR_HEIGHT - STATUS_BAR_PADDING
        morale_bg_rect = pygame.Rect(rect.left + STATUS_BAR_PADDING, morale_bar_y, bar_max_width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(screen, BAR_BACKGROUND_COLOR, morale_bg_rect)
        morale_ratio = self.morale / self.initial_max_morale if self.initial_max_morale > 0 else 0
        current_morale_width = int(morale_ratio * bar_max_width)
        morale_fill_rect = pygame.Rect(rect.left + STATUS_BAR_PADDING, morale_bar_y, current_morale_width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(screen, MORALE_BAR_COLOR, morale_fill_rect)

        hp_bar_y = morale_bar_y - STATUS_BAR_HEIGHT - (STATUS_BAR_PADDING // 2 if STATUS_BAR_PADDING > 0 else 1)
        hp_bg_rect = pygame.Rect(rect.left + STATUS_BAR_PADDING, hp_bar_y, bar_max_width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(screen, BAR_BACKGROUND_COLOR, hp_bg_rect)
        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 0
        current_hp_width = int(hp_ratio * bar_max_width)
        hp_fill_rect = pygame.Rect(rect.left + STATUS_BAR_PADDING, hp_bar_y, current_hp_width, STATUS_BAR_HEIGHT)
        pygame.draw.rect(screen, HP_BAR_COLOR, hp_fill_rect)

        center_x = rect.centerx
        center_y = rect.centery
        line_length = GRID_SIZE // 3
        if self.orientation == 0: end_point = (center_x, center_y - line_length)
        elif self.orientation == 1: end_point = (center_x + line_length, center_y)
        elif self.orientation == 2: end_point = (center_x, center_y + line_length)
        elif self.orientation == 3: end_point = (center_x - line_length, center_y)
        else: end_point = (center_x, center_y - line_length)
        pygame.draw.line(screen, BLACK, (center_x, center_y), end_point, 2)

    def get_grid_pos(self):
        return (self.x, self.y)

    def distance_to(self, other_unit_or_pos):
        if isinstance(other_unit_or_pos, Unit):
            other_x, other_y = other_unit_or_pos.x, other_unit_or_pos.y
        else:
            other_x, other_y = other_unit_or_pos
        return math.sqrt((self.x - other_x)**2 + (self.y - other_y)**2)

    def find_nearest_enemy(self, enemy_list):
        closest_enemy = None
        min_dist = float('inf')
        valid_enemies = [e for e in enemy_list if not e.is_destroyed]
        if not valid_enemies:
            return None
        for enemy in valid_enemies:
            dist = self.distance_to(enemy)
            if dist < min_dist:
                min_dist = dist
                closest_enemy = enemy
        return closest_enemy

    def _is_cell_occupied(self, pos, all_units):
        for unit in all_units:
            if unit != self and not unit.is_destroyed and unit.get_grid_pos() == pos:
                return True
        return False

    def move_towards(self, target_pos_tuple, all_units):
        if self.is_destroyed:
            return
        is_actually_fleeing = ENABLE_MORALE and self.is_fleeing
        if is_actually_fleeing:
            dx = self.x - target_pos_tuple[0]
            dy = self.y - target_pos_tuple[1]
        else:
            dx = target_pos_tuple[0] - self.x
            dy = target_pos_tuple[1] - self.y
        moved_this_step = False
        new_pos_x, new_pos_y = self.x, self.y
        if abs(dx) > abs(dy):
            if dx != 0:
                potential_x = self.x + (1 if dx > 0 else -1)
                if 0 <= potential_x < MAP_WIDTH and not self._is_cell_occupied((potential_x, self.y), all_units):
                    new_pos_x = potential_x
                    moved_this_step = True
            if not moved_this_step and dy != 0:
                potential_y = self.y + (1 if dy > 0 else -1)
                if 0 <= potential_y < MAP_HEIGHT and not self._is_cell_occupied((self.x, potential_y), all_units):
                    new_pos_y = potential_y
                    moved_this_step = True
        else:
            if dy != 0:
                potential_y = self.y + (1 if dy > 0 else -1)
                if 0 <= potential_y < MAP_HEIGHT and not self._is_cell_occupied((self.x, potential_y), all_units):
                    new_pos_y = potential_y
                    moved_this_step = True
            if not moved_this_step and dx != 0:
                potential_x = self.x + (1 if dx > 0 else -1)
                if 0 <= potential_x < MAP_WIDTH and not self._is_cell_occupied((potential_x, self.y), all_units):
                    new_pos_x = potential_x
                    moved_this_step = True
        if moved_this_step:
            if not is_actually_fleeing:
                if new_pos_x > self.x: self.orientation = 1
                elif new_pos_x < self.x: self.orientation = 3
                elif new_pos_y > self.y: self.orientation = 2
                elif new_pos_y < self.y: self.orientation = 0
            self.x, self.y = new_pos_x, new_pos_y

    def take_damage(self, damage_amount, all_units=None):
        self.hp -= damage_amount
        if self.hp <= 0:
            self.hp = 0
            self.is_destroyed = True
            if ENABLE_MORALE and all_units:
                self.notify_allies_of_fall(all_units)
            return
        if ENABLE_MORALE:
            hp_percentage = self.hp / self.initial_max_hp if self.initial_max_hp > 0 else 0
            if hp_percentage < 0.2:
                self.update_morale(event_type="hp_critical", amount=MORALE_HP_20_PERCENT_PENALTY, all_units=all_units)
            elif hp_percentage < 0.5:
                self.update_morale(event_type="hp_low", amount=MORALE_HP_50_PERCENT_PENALTY, all_units=all_units)

    def notify_allies_of_fall(self, all_units):
        if not ENABLE_MORALE: return
        ally_fallen_penalty = MORALE_ALLY_FALLEN_PENALTY
        if self.faction == "Sparta":
             ally_fallen_penalty /= 2
        for unit in all_units:
            if not unit.is_destroyed and unit.faction == self.faction and unit != self:
                if self.distance_to(unit) <= MORALE_ALLY_FALLEN_RADIUS:
                    unit.update_morale(event_type="ally_fallen", amount=ally_fallen_penalty, all_units=all_units)

    def get_relative_position_of_attacker(self, attacker):
        dx = attacker.x - self.x
        dy = attacker.y - self.y
        tolerance = 0.5 
        if self.orientation == 0:
            if dy < 0 and abs(dy) > abs(dx) - tolerance: return "front"
            if dy > 0 and abs(dy) > abs(dx) - tolerance: return "rear"
            return "flank"
        elif self.orientation == 1:
            if dx > 0 and abs(dx) > abs(dy) - tolerance: return "front"
            if dx < 0 and abs(dx) > abs(dy) - tolerance: return "rear"
            return "flank"
        elif self.orientation == 2:
            if dy > 0 and abs(dy) > abs(dx) - tolerance: return "front"
            if dy < 0 and abs(dy) > abs(dx) - tolerance: return "rear"
            return "flank"
        elif self.orientation == 3:
            if dx < 0 and abs(dx) > abs(dy) - tolerance: return "front"
            if dx > 0 and abs(dx) > abs(dy) - tolerance: return "rear"
            return "flank"
        return "front"

    def attack(self, target_unit, all_units):
        if self.is_destroyed or target_unit.is_destroyed: return
        if ENABLE_MORALE and self.is_fleeing: return
        current_attack_power = self.attack_power
        current_attack_range = self.attack_range
        is_ranged_attack = False
        if self.unit_type == "Immortal" and self.faction == "Persia":
            if self.ammo > 0:
                current_attack_power = PERSIAN_RANGED_ATTACK_POWER
                current_attack_range = PERSIAN_RANGED_ATTACK_RANGE
                is_ranged_attack = True
            else:
                current_attack_power = PERSIAN_MELEE_ATTACK_POWER_WEAK
                current_attack_range = 1
                if self.attack_range > 1 or self.color != IMMORTAL_COLOR_MELEE :
                    self.attack_power = PERSIAN_MELEE_ATTACK_POWER_WEAK
                    self.attack_range = 1
                    self.color = IMMORTAL_COLOR_MELEE
        if self.distance_to(target_unit) > current_attack_range: return
        if random.random() > HIT_CHANCE: return
        concentration_multiplier = 1.0
        if ENABLE_LANCHESTER_SQUARE_BONUS and is_ranged_attack and self.unit_type == "Immortal" and self.faction == "Persia":
            supporting_units_count = 0
            for friendly_unit in all_units:
                if (friendly_unit != self and
                    friendly_unit.faction == self.faction and
                    friendly_unit.unit_type == self.unit_type and
                    not friendly_unit.is_destroyed and
                    not (ENABLE_MORALE and friendly_unit.is_fleeing) and
                    getattr(friendly_unit, 'ammo', 0) > 0 and
                    self.distance_to(friendly_unit) <= LANCHESTER_RANGED_SUPPORT_RADIUS):
                    supporting_units_count += 1
            bonus_value = min(LANCHESTER_MAX_RANGED_CONCENTRATION_BONUS,
                              supporting_units_count * LANCHESTER_RANGED_BONUS_PER_SUPPORTING_UNIT)
            concentration_multiplier = 1.0 + bonus_value
        if is_ranged_attack and self.unit_type == "Immortal" and self.faction == "Persia":
            self.ammo -= 1
            if self.ammo == 0:
                self.attack_power = PERSIAN_MELEE_ATTACK_POWER_WEAK
                self.attack_range = 1
                self.color = IMMORTAL_COLOR_MELEE
        attacker_morale_modifier = 1.0
        if ENABLE_MORALE and not self.is_fleeing:
            if self.morale <= MORALE_ROUT_THRESHOLD:
                attacker_morale_modifier = (1.0 - ATTACKER_CRITICAL_MORALE_DAMAGE_PENALTY)
            elif self.morale < MORALE_LOW_THRESHOLD:
                attacker_morale_modifier = (1.0 - MORALE_LOW_EFFECT_PENALTY)
        base_damage = current_attack_power * concentration_multiplier * attacker_morale_modifier
        damage_multiplier_positional = 1.0
        attacker_relative_pos = target_unit.get_relative_position_of_attacker(self)
        if attacker_relative_pos == "flank": damage_multiplier_positional = FLANK_BONUS
        elif attacker_relative_pos == "rear": damage_multiplier_positional = REAR_ATTACK_BONUS
        if target_unit.unit_type == "Spearman" and target_unit.faction == "Sparta":
            if attacker_relative_pos == "front":
                damage_multiplier_positional *= 0.8
                if is_ranged_attack and self.unit_type == "Immortal" and self.faction == "Persia":
                    damage_multiplier_positional *= 0.50
        current_target_defense = target_unit.defense
        if ENABLE_MORALE and target_unit.morale < MORALE_LOW_THRESHOLD:
            current_target_defense *= (1.0 - MORALE_LOW_EFFECT_PENALTY)
        if target_unit.unit_type == "Spearman" and target_unit.faction == "Sparta" and \
           not is_ranged_attack and attacker_relative_pos == "front":
            current_target_defense *= 1.3
        calculated_damage_value = (base_damage * damage_multiplier_positional) - current_target_defense
        current_damage_variance_roll = random.uniform(DAMAGE_VARIANCE_MIN, DAMAGE_VARIANCE_MAX)
        target_morale_damage_multiplier = 1.0
        if ENABLE_MORALE:
            if target_unit.morale <= MORALE_ROUT_THRESHOLD or target_unit.is_fleeing:
                target_morale_damage_multiplier = ROUTING_TARGET_CRITICAL_MULTIPLIER
                current_damage_variance_roll = DAMAGE_VARIANCE_MAX
            elif target_unit.morale < MORALE_LOW_THRESHOLD:
                target_morale_damage_multiplier = LOW_MORALE_TARGET_DAMAGE_MULTIPLIER
        calculated_damage_value *= target_morale_damage_multiplier
        if calculated_damage_value < 0: calculated_damage_value = 0
        final_damage = max(1, int(calculated_damage_value * current_damage_variance_roll)) if calculated_damage_value > 0 else 0
        if final_damage > 0:
            target_unit.take_damage(final_damage, all_units=all_units)

    def update_morale(self, event_type=None, amount=0, all_units=None):
        if not ENABLE_MORALE:
            self.is_fleeing = False
            return
        if event_type:
            self.morale += amount
        if all_units and event_type is None:
            enemies_around = 0
            enemy_faction = "Persia" if self.faction == "Sparta" else "Sparta"
            relevant_enemies = [u for u in all_units if u.faction == enemy_faction and \
                                not u.is_destroyed and self.distance_to(u) <= MORALE_SURROUNDED_RADIUS]
            enemies_around = len(relevant_enemies)
            if enemies_around >= MORALE_SURROUNDED_THRESHOLD:
                surrounded_penalty_val = MORALE_SURROUNDED_PENALTY
                if self.faction == "Sparta":
                    surrounded_penalty_val /= 2
                self.morale += surrounded_penalty_val
        self.morale = max(0, min(self.initial_max_morale, self.morale))
        if self.morale <= MORALE_ROUT_THRESHOLD:
            self.is_fleeing = True
        elif self.morale < MORALE_LOW_THRESHOLD:
            current_flee_chance = MORALE_FLEE_CHANCE
            if self.faction == "Sparta":
                current_flee_chance = 0.005
            if random.random() < current_flee_chance:
                self.is_fleeing = True
        if self.is_fleeing and self.morale >= MORALE_LOW_THRESHOLD:
            if random.random() < 0.75:
                self.is_fleeing = False

    def regenerate_stats(self):
        if self.is_destroyed: return
        if self.faction == "Sparta":
            self.hp = min(self.initial_max_hp, self.hp + SPARTAN_HP_REGEN_RATE)
            if ENABLE_MORALE:
                self.morale = min(self.initial_max_morale, self.morale + SPARTAN_MORALE_REGEN_RATE)

    def update(self, all_units, enemy_units):
        if self.is_destroyed: return
        if ENABLE_MORALE:
            self.update_morale(all_units=all_units)
        if self.faction == "Sparta":
            self.regenerate_stats()
        for _ in range(int(self.speed)):
            if self.is_destroyed: break
            if ENABLE_MORALE and self.is_fleeing:
                nearest_enemy_to_flee_from = self.find_nearest_enemy(enemy_units)
                if nearest_enemy_to_flee_from:
                    self.move_towards(nearest_enemy_to_flee_from.get_grid_pos(), all_units)
                continue
            if self.target is None or self.target.is_destroyed:
                self.target = self.find_nearest_enemy(enemy_units)
            if self.target:
                effective_attack_range = self.attack_range
                if self.unit_type == "Immortal" and self.faction == "Persia" and self.ammo == 0:
                    effective_attack_range = 1
                if self.distance_to(self.target) <= effective_attack_range:
                    self.attack(self.target, all_units)
                    break
                else:
                    self.move_towards(self.target.get_grid_pos(), all_units)
                    if self.target and not self.target.is_destroyed and \
                       self.distance_to(self.target) <= effective_attack_range:
                        self.attack(self.target, all_units)
                        break
            else:
                break
