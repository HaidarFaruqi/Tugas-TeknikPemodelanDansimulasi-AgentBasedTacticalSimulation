import pygame
import sys
import random
from config import *
from unit import Unit

placed_coords = set()
initial_persian_total_count = 0
persian_debuff_thresholds_triggered = set()
DRAW_GRID_BOOL = True
pygame_initialized = False

def _place_unit_safely(x, y, unit_type, faction, hp, attack_power, defense, attack_range, speed, name, orientation,
                       units_list_faction, current_map_width, current_map_height,
                       is_frontline=False):
    global placed_coords
    if not (0 <= x < current_map_width and 0 <= y < current_map_height):
        return None
    if (x,y) in placed_coords:
        return None
    unit = Unit(x, y, unit_type, faction, hp, attack_power, defense, attack_range, speed, name)
    unit.orientation = orientation
    if faction == "Sparta":
        unit.is_on_frontline = True
        unit.is_resting = False
    else:
        unit.is_on_frontline = is_frontline
    placed_coords.add((x,y))
    units_list_faction.append(unit)
    return unit

def setup_units_thermopylae_formation(
    total_spartan_count_in, num_persian_immortals_in, 
    map_w, map_h):
    global placed_coords, initial_persian_total_count, persian_debuff_thresholds_triggered
    placed_coords.clear()
    initial_persian_total_count = num_persian_immortals_in
    persian_debuff_thresholds_triggered.clear()
    spartan_units_all = []
    persian_units_all = []
    common_formation_width = 30 
    if common_formation_width > map_w:
        common_formation_width = map_w 
    spartan_pass_width = common_formation_width
    spartan_total_ranks = (total_spartan_count_in + spartan_pass_width - 1) // spartan_pass_width if spartan_pass_width > 0 else 0
    spartan_line_start_x = map_w // 2 - spartan_pass_width // 2
    spartan_y_bottom_margin = 3
    spartan_line_start_y = map_h - spartan_y_bottom_margin - spartan_total_ranks 
    if spartan_line_start_y < 0:
        spartan_line_start_y = 0
    spartans_placed_count = 0
    for rank in range(spartan_total_ranks):
        for col in range(spartan_pass_width):
            if spartans_placed_count < total_spartan_count_in:
                unit = _place_unit_safely(
                    spartan_line_start_x + col, spartan_line_start_y + rank, "Spearman", "Sparta",
                    hp=180, attack_power=16, defense=13, attack_range=1, speed=1,
                    name=f"Hoplite_{spartans_placed_count}", orientation=0,
                    units_list_faction=spartan_units_all, current_map_width=map_w, current_map_height=map_h,
                    is_frontline=True) 
                if unit:
                    spartans_placed_count += 1
    persian_front_y = 2
    persian_current_line_width = common_formation_width
    immortal_ranks = (num_persian_immortals_in + persian_current_line_width - 1) // persian_current_line_width if persian_current_line_width > 0 else 0
    count_persian_immortals = 0
    persian_start_x = map_w // 2 - persian_current_line_width // 2
    for r_idx in range(immortal_ranks):
        for w_idx in range(persian_current_line_width):
            if count_persian_immortals < num_persian_immortals_in:
                px, py = persian_start_x + w_idx, persian_front_y + r_idx
                unit = _place_unit_safely(
                    px, py, "Immortal", "Persia",
                    hp=PERSIAN_INFANTRY_HP, 
                    attack_power=PERSIAN_RANGED_ATTACK_POWER, 
                    defense=PERSIAN_INFANTRY_DEFENSE, 
                    attack_range=PERSIAN_RANGED_ATTACK_RANGE, speed=1, 
                    name=f"Immortal_{count_persian_immortals}", orientation=2,
                    units_list_faction=persian_units_all, current_map_width=map_w, current_map_height=map_h)
                if unit:
                    count_persian_immortals += 1
    return spartan_units_all, persian_units_all

def draw_grid(screen):
    for x_coord in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GREY, (x_coord, 0), (x_coord, SCREEN_HEIGHT))
    for y_coord in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GREY, (0, y_coord), (SCREEN_WIDTH, y_coord))

def display_stats(screen, spartan_units, persian_units, font, game_winner, victory_condition, iteration):
    spartan_total_alive = sum(1 for u in spartan_units if not u.is_destroyed) 
    persian_alive_count = sum(1 for u in persian_units if not u.is_destroyed) 
    spartan_casualties = TOTAL_SPARTAN_COUNT - spartan_total_alive
    persian_casualties = initial_persian_total_count - persian_alive_count
    spartan_survival_percentage = (spartan_total_alive / TOTAL_SPARTAN_COUNT * 100) if TOTAL_SPARTAN_COUNT > 0 else 0.0
    persian_survival_percentage = (persian_alive_count / initial_persian_total_count * 100) if initial_persian_total_count > 0 else 0.0

    font_h = font.get_height()
    padding = 10
    line_spacing = 5

    iter_text_x_anchor = SCREEN_WIDTH - padding
    iter_text_surface = font.render(f"Iterasi: {iteration}", True, WHITE)
    screen.blit(iter_text_surface, (iter_text_x_anchor - iter_text_surface.get_width(), padding))
    max_iter_text_surface = font.render(f"Maks Iterasi: {MAX_ITERATIONS}", True, WHITE)
    screen.blit(max_iter_text_surface, (iter_text_x_anchor - max_iter_text_surface.get_width(), padding + font_h + line_spacing))

    current_y_topleft = padding
    persia_status_text = font.render(f"Persia Hidup: {persian_alive_count} ({persian_survival_percentage:.1f}%) (Korban: {persian_casualties})", True, IMMORTAL_COLOR_RANGED)
    screen.blit(persia_status_text, (padding, current_y_topleft))
    current_y_topleft += font_h + line_spacing

    if ENABLE_MORALE:
        active_persians_morale_list = [u.morale for u in persian_units if not u.is_destroyed]
        avg_persian_morale = sum(active_persians_morale_list) / len(active_persians_morale_list) if active_persians_morale_list else 0.0
        persia_morale_text = font.render(f"Moral Rata-rata Persia: {avg_persian_morale:.1f}", True, IMMORTAL_COLOR_RANGED)
        screen.blit(persia_morale_text, (padding, current_y_topleft))
        current_y_topleft += font_h + line_spacing
        persians_ammo_left = sum(u.ammo for u in persian_units if not u.is_destroyed and u.unit_type == "Immortal")
        persia_ammo_text = font.render(f"Amunisi Persia: {persians_ammo_left}", True, IMMORTAL_COLOR_RANGED)
        screen.blit(persia_ammo_text, (padding, current_y_topleft))

    current_y_bottomleft = SCREEN_HEIGHT - padding
    if ENABLE_MORALE:
        active_spartans_morale_list = [u.morale for u in spartan_units if not u.is_destroyed]
        avg_spartan_morale = sum(active_spartans_morale_list) / len(active_spartans_morale_list) if active_spartans_morale_list else 0.0
        sparta_morale_text = font.render(f"Moral Rata-rata Spartan: {avg_spartan_morale:.1f}", True, RED)
        current_y_bottomleft -= font_h
        screen.blit(sparta_morale_text, (padding, current_y_bottomleft))
        current_y_bottomleft -= line_spacing

    sparta_status_text = font.render(f"Spartan Hidup: {spartan_total_alive} ({spartan_survival_percentage:.1f}%) (Korban: {spartan_casualties})", True, RED)
    current_y_bottomleft -= font_h
    screen.blit(sparta_status_text, (padding, current_y_bottomleft))
    
    if game_winner and game_winner != "USER_ABORTED" and game_winner != "INCONCLUSIVE":
        winner_message_lines = []
        if game_winner == "Draw":
            winner_message_lines.append("HASIL SERI!")
        elif game_winner == "Sparta":
            winner_message_lines.append("SPARTA MENANG!")
        elif game_winner == "Persia":
            winner_message_lines.append("PERSIA MENANG!")
        winner_message_lines.append(f"({victory_condition})")
        if game_winner == "Sparta":
            winner_message_lines.append("PERSIA KALAH!")
        elif game_winner == "Persia":
            winner_message_lines.append("SPARTA KALAH!")
        winner_message_lines.append("--- Persentase Sisa Unit ---")
        winner_message_lines.append(f"Spartan: {spartan_survival_percentage:.2f}%")
        winner_message_lines.append(f"Persia: {persian_survival_percentage:.2f}%")
        
        msg_line_height = font.get_height() 
        msg_line_spacing = 4
        msg_padding = 20

        max_msg_text_width = 0
        for line_text in winner_message_lines:
            text_surf_temp = font.render(line_text, True, WHITE)
            if text_surf_temp.get_width() > max_msg_text_width:
                max_msg_text_width = text_surf_temp.get_width()

        total_msg_block_height = (msg_line_height * len(winner_message_lines)) + \
                                 (msg_line_spacing * (len(winner_message_lines) - 1 if len(winner_message_lines) > 1 else 0)) + \
                                 (msg_line_spacing if game_winner != "Draw" else 0)

        msg_bg_box_width = max_msg_text_width + (2 * msg_padding)
        msg_bg_box_height = total_msg_block_height + (2 * msg_padding)
        msg_bg_rect = pygame.Rect(0, 0, msg_bg_box_width, msg_bg_box_height)
        msg_bg_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(screen, BLACK, msg_bg_rect)
        pygame.draw.rect(screen, WHITE, msg_bg_rect, 3)

        current_y_msg_text = msg_bg_rect.top + msg_padding
        for i, line_text in enumerate(winner_message_lines):
            color = WHITE
            if "MENANG!" in line_text: color = (100, 255, 100)
            elif "KALAH!" in line_text: color = (255, 100, 100)
            elif "SERI!" in line_text: color = (200, 200, 100)
            elif "Persentase Sisa Unit" in line_text: color = (180, 180, 255)
            winner_text_surface = font.render(line_text, True, color)
            text_rect = winner_text_surface.get_rect(centerx=msg_bg_rect.centerx, top=current_y_msg_text)
            screen.blit(winner_text_surface, text_rect)
            current_y_msg_text += msg_line_height + msg_line_spacing
            if game_winner != "Draw" and i == 2:
                 current_y_msg_text += msg_line_spacing

def apply_persian_attrition(persian_units_list, iteration_num):
    global initial_persian_total_count, persian_debuff_thresholds_triggered
    if not ENABLE_MORALE or initial_persian_total_count == 0:
        return
    persians_alive = sum(1 for u in persian_units_list if not u.is_destroyed)
    persian_casualties = initial_persian_total_count - persians_alive
    persian_loss_percentage = persian_casualties / initial_persian_total_count if initial_persian_total_count > 0 else 0.0
    for threshold_percent in PERSIAN_ATTRITION_CASUALTY_THRESHOLDS:
        if persian_loss_percentage >= threshold_percent and threshold_percent not in persian_debuff_thresholds_triggered:
            for p_unit in persian_units_list:
                if not p_unit.is_destroyed:
                    p_unit.update_morale("attrition_debuff", amount=PERSIAN_ATTRITION_MORALE_PENALTY)
            persian_debuff_thresholds_triggered.add(threshold_percent)

def run_single_simulation(visual_mode=False):
    global pygame_initialized, initial_persian_total_count 
    screen, clock, font = None, None, None
    if visual_mode:
        if not pygame_initialized:
            pygame.init()
            pygame_initialized = True
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Thermopylae: Simulasi Pertempuran")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 28)
    
    current_map_width = MAP_WIDTH
    current_map_height = MAP_HEIGHT
    
    spartan_units, persian_units = setup_units_thermopylae_formation(
        TOTAL_SPARTAN_COUNT, TOTAL_PERSIAN_COUNT, 
        current_map_width, current_map_height
    )
    all_units = spartan_units + persian_units
    
    game_winner = None
    victory_condition = ""
    iteration_count = 0
    
    running_main_loop = True if visual_mode else False
    game_logic_running = True

    while running_main_loop or (not visual_mode and game_logic_running):
        if visual_mode:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_main_loop = False
                    game_logic_running = False 
                    if not game_winner: 
                        game_winner = "USER_ABORTED"
                        victory_condition = "User menutup window"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running_main_loop = False
                        game_logic_running = False
                        if not game_winner:
                            game_winner = "USER_ABORTED"
                            victory_condition = "User menekan tombol Escape"
        
        if not running_main_loop and visual_mode: 
            break 

        if game_logic_running:
            iteration_count += 1
            apply_persian_attrition(persian_units, iteration_count)

            current_turn_order_units = [u for u in all_units if not u.is_destroyed]
            random.shuffle(current_turn_order_units)

            for unit in current_turn_order_units:
                if unit.is_destroyed: continue
                enemy_list_for_this_unit = persian_units if unit.faction == "Sparta" else spartan_units
                active_enemy_list = [e for e in enemy_list_for_this_unit if not e.is_destroyed]
                unit.update(all_units, active_enemy_list)
            
            total_spartans_alive = sum(1 for u in spartan_units if not u.is_destroyed)
            total_persians_alive = sum(1 for u in persian_units if not u.is_destroyed)

            if iteration_count >= MAX_ITERATIONS:
                spartan_survival_percentage = (total_spartans_alive / TOTAL_SPARTAN_COUNT * 100) if TOTAL_SPARTAN_COUNT > 0 else 0.0
                persian_survival_percentage = (total_persians_alive / initial_persian_total_count * 100) if initial_persian_total_count > 0 else 0.0
                percentage_difference = abs(spartan_survival_percentage - persian_survival_percentage)
                if percentage_difference <= 15.0:
                    game_winner = "Draw"
                    victory_condition = (f"Iterasi maks. Selisih unit akhir ({percentage_difference:.2f}%) <= 15%.")
                elif spartan_survival_percentage > persian_survival_percentage:
                    game_winner = "Sparta"
                    victory_condition = (f"Iterasi maks. Spartan unggul.")
                else:
                    game_winner = "Persia"
                    victory_condition = (f"Iterasi maks. Persia unggul.")
            
            if ENABLE_MORALE and not game_winner:
                active_spartans_morale_check = [u.morale for u in spartan_units if not u.is_destroyed]
                if active_spartans_morale_check: 
                    avg_spartan_morale_val = sum(active_spartans_morale_check) / len(active_spartans_morale_check)
                    if avg_spartan_morale_val < TEAM_MORALE_COLLAPSE_THRESHOLD:
                        game_winner = "Persia"; victory_condition = f"Moral Spartan runtuh ({avg_spartan_morale_val:.1f})"
                if not game_winner:
                    active_persians_morale_check = [u.morale for u in persian_units if not u.is_destroyed]
                    if active_persians_morale_check:
                        avg_persian_morale_val = sum(active_persians_morale_check) / len(active_persians_morale_check)
                        if avg_persian_morale_val < TEAM_MORALE_COLLAPSE_THRESHOLD:
                            game_winner = "Sparta"; victory_condition = f"Moral Persia runtuh ({avg_persian_morale_val:.1f})"
            
            if not game_winner:
                if total_spartans_alive == 0 and total_persians_alive > 0:
                    game_winner = "Persia"; victory_condition = "Semua Spartan tereliminasi!"
                elif total_persians_alive == 0 and total_spartans_alive > 0:
                    game_winner = "Sparta"; victory_condition = "Semua Persia tereliminasi!"
                elif total_spartans_alive == 0 and total_persians_alive == 0:
                    game_winner = "Draw"; victory_condition = "Pemusnahan Mutual!" 
            
            if game_winner: 
                game_logic_running = False

        if visual_mode and screen and clock and font:
            screen.fill(BLACK)
            if DRAW_GRID_BOOL:
                 draw_grid(screen)
            for unit_to_draw in all_units: 
                unit_to_draw.draw(screen)
            display_stats(screen, spartan_units, persian_units, font, game_winner, victory_condition, iteration_count)
            pygame.display.flip()
            clock.tick(FPS)
        
        if not visual_mode and not game_logic_running:
            break

    active_spartans_morale = [u.morale for u in spartan_units if not u.is_destroyed]
    avg_final_spartan_morale = sum(active_spartans_morale) / len(active_spartans_morale) if active_spartans_morale else 0
    active_persians_morale = [u.morale for u in persian_units if not u.is_destroyed]
    avg_final_persian_morale = sum(active_persians_morale) / len(active_persians_morale) if active_persians_morale else 0
    initial_total_persian_ammo = initial_persian_total_count * PERSIAN_INITIAL_AMMO
    remaining_total_persian_ammo = sum(u.ammo for u in persian_units if not u.is_destroyed and u.unit_type == "Immortal")

    results_dict = {
        "winner": game_winner if game_winner else "INCONCLUSIVE",
        "victory_condition": victory_condition,
        "iterations": iteration_count,
        "spartans_initial": TOTAL_SPARTAN_COUNT,
        "persians_initial": initial_persian_total_count,
        "spartans_remaining": sum(1 for u in spartan_units if not u.is_destroyed),
        "persians_remaining": sum(1 for u in persian_units if not u.is_destroyed),
        "avg_final_spartan_morale": avg_final_spartan_morale,
        "avg_final_persian_morale": avg_final_persian_morale,
        "initial_total_persian_ammo": initial_total_persian_ammo,
        "remaining_total_persian_ammo": remaining_total_persian_ammo,
    }
    return results_dict

if __name__ == '__main__':
    run_single_simulation(visual_mode=True)
    if pygame_initialized: 
        pygame.quit()
        sys.exit()
