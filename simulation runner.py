import collections
import matplotlib.pyplot as plt
import numpy as np
from main import run_single_simulation
from config import (TOTAL_SPARTAN_COUNT, TOTAL_PERSIAN_COUNT, PERSIAN_INITIAL_AMMO,
                    SPARTAN_MAX_MORALE_CAP, DEFAULT_MORALE, MAX_ITERATIONS)

NUM_SIMULATIONS = 50

def run_multiple_simulations():
    all_run_results = []
    print(f"Memulai {NUM_SIMULATIONS} simulasi...")
    for i in range(NUM_SIMULATIONS):
        if (i + 1) % max(1, NUM_SIMULATIONS // 10) == 0 or i == 0 or i == NUM_SIMULATIONS -1 :
            print(f"Menjalankan simulasi {i + 1}/{NUM_SIMULATIONS}...")
        
        result = run_single_simulation(visual_mode=False)
        all_run_results.append(result)
        
        if (i + 1) % max(1, NUM_SIMULATIONS // 10) == 0 or i == 0 or i == NUM_SIMULATIONS -1 or (i + 1) == NUM_SIMULATIONS:
             print(f"  Selesai simulasi {i + 1}. Pemenang: {result['winner']}. Iterasi: {result['iterations']}.")
    print(f"\nSelesai semua {NUM_SIMULATIONS} simulasi.")
    return all_run_results

def analyze_and_plot_results(results_list):
    if not results_list:
        print("Tidak ada hasil simulasi untuk dianalisis.")
        return

    winners_counter = collections.Counter([r['winner'] for r in results_list if r['winner'] is not None])
    iteration_data = [r['iterations'] for r in results_list]
    avg_iterations = sum(iteration_data) / len(iteration_data) if iteration_data else 0

    spartans_initial_fixed = TOTAL_SPARTAN_COUNT
    persians_initial_fixed = TOTAL_PERSIAN_COUNT
    avg_spartans_remaining = sum(r['spartans_remaining'] for r in results_list) / len(results_list)
    avg_persians_remaining = sum(r['persians_remaining'] for r in results_list) / len(results_list)
    spartan_survival_rate = (avg_spartans_remaining / spartans_initial_fixed * 100) if spartans_initial_fixed > 0 else 0
    persian_survival_rate = (avg_persians_remaining / persians_initial_fixed * 100) if persians_initial_fixed > 0 else 0

    spartan_initial_morale_fixed = SPARTAN_MAX_MORALE_CAP
    persian_initial_morale_fixed = DEFAULT_MORALE
    avg_final_spartan_morale_overall = sum(r['avg_final_spartan_morale'] for r in results_list) / len(results_list)
    avg_final_persian_morale_overall = sum(r['avg_final_persian_morale'] for r in results_list) / len(results_list)

    initial_total_persian_ammo_fixed = persians_initial_fixed * PERSIAN_INITIAL_AMMO
    avg_remaining_total_persian_ammo = sum(r['remaining_total_persian_ammo'] for r in results_list) / len(results_list) if results_list else 0
    avg_persian_ammo_used = initial_total_persian_ammo_fixed - avg_remaining_total_persian_ammo
    persian_ammo_usage_percentage = (avg_persian_ammo_used / initial_total_persian_ammo_fixed * 100) if initial_total_persian_ammo_fixed > 0 else 0

    print("\n--- Hasil Kumulatif Simulasi ---")
    print(f"Total simulasi dijalankan: {len(results_list)}")
    print("\n Distribusi Kemenangan:")
    for winner, count in winners_counter.items():
        print(f"  {winner}: {count} kemenangan ({count/len(results_list)*100:.2f}%)")
    print(f"\n Rata-rata Iterasi per Simulasi: {avg_iterations:.2f} (dari maks {MAX_ITERATIONS})")
    if iteration_data:
        median_iterations = np.median(iteration_data)
        q1_iterations = np.percentile(iteration_data, 25)
        q3_iterations = np.percentile(iteration_data, 75)
        print(f"   Median Iterasi: {median_iterations:.2f}")
        print(f"   Kuartil 1 (Q1) Iterasi: {q1_iterations:.2f}")
        print(f"   Kuartil 3 (Q3) Iterasi: {q3_iterations:.2f}")
    print("\n Rata-rata Jumlah Pasukan:")
    print(f"  Spartan: Awal: {spartans_initial_fixed}, Rata-rata Tersisa: {avg_spartans_remaining:.2f} ({spartan_survival_rate:.2f}% selamat)")
    print(f"  Persia: Awal: {persians_initial_fixed}, Rata-rata Tersisa: {avg_persians_remaining:.2f} ({persian_survival_rate:.2f}% selamat)")
    print("\n Moral Pasukan (yang hidup):")
    print(f"  Spartan: Awal: {spartan_initial_morale_fixed}, Rata-rata Akhir: {avg_final_spartan_morale_overall:.2f}")
    print(f"  Persia: Awal: {persian_initial_morale_fixed}, Rata-rata Akhir: {avg_final_persian_morale_overall:.2f}")
    print("\n Statistik Amunisi Persia:")
    print(f"  Amunisi Awal Total (Konstan): {initial_total_persian_ammo_fixed}")
    print(f"  Rata-rata Amunisi Sisa Total: {avg_remaining_total_persian_ammo:.2f}")
    print(f"  Rata-rata Amunisi Digunakan: {avg_persian_ammo_used:.2f} ({persian_ammo_usage_percentage:.2f}% dari total awal)")

    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(17, 10)) 
        gs = fig.add_gridspec(2, 6)
        ax_kemenangan = fig.add_subplot(gs[0, 0:2])
        ax_iterasi_boxplot = fig.add_subplot(gs[0, 2:4])
        ax_amunisi = fig.add_subplot(gs[0, 4:6])
        ax_jumlah_unit = fig.add_subplot(gs[1, 0:3])
        ax_moral = fig.add_subplot(gs[1, 3:6])
        fig.suptitle(f'Analisis Komprehensif Simulasi Pertempuran ({NUM_SIMULATIONS} Skenario)', fontsize=16, fontweight='bold')
        
        font_size_title = 13
        font_size_label = 11
        font_size_tick = 9
        font_size_legend = 9
        font_size_text = 8

        win_names = list(winners_counter.keys())
        win_counts = list(winners_counter.values())
        colors_pie = {'Sparta': '#d62728', 'Persia': '#1f77b4', 'Draw': '#7f7f7f', 'USER_ABORTED': '#ff7f0e', 'INCONCLUSIVE': '#bdbdbd'}
        pie_colors = [colors_pie.get(name, '#2ca02c') for name in win_names]
        ax_kemenangan.pie(win_counts, labels=win_names, autopct='%1.1f%%', startangle=120, colors=pie_colors,
                          wedgeprops={'edgecolor': 'white'}, textprops={'fontsize': font_size_text + 1})
        ax_kemenangan.set_title('Distribusi Kemenangan Fraksi', fontsize=font_size_title)
        ax_kemenangan.axis('equal')

        if iteration_data:
            boxplot_props = dict(patch_artist=True,
                                 boxprops=dict(facecolor='lightcoral', color='black', alpha=0.75),
                                 medianprops=dict(color='darkred', linewidth=2),
                                 whiskerprops=dict(color='black', linestyle='--'),
                                 capprops=dict(color='black'),
                                 flierprops=dict(marker='o', markerfacecolor='grey', markersize=5, alpha=0.6))
            ax_iterasi_boxplot.boxplot(iteration_data, vert=False, **boxplot_props)
            ax_iterasi_boxplot.set_yticklabels(['Durasi Simulasi'])
            ax_iterasi_boxplot.set_xlabel('Jumlah Iterasi', fontsize=font_size_label)
            ax_iterasi_boxplot.set_title(f'Distribusi Durasi Simulasi (Rata-rata: {avg_iterations:.2f})', fontsize=font_size_title)
            ax_iterasi_boxplot.grid(axis='x', linestyle='--')
            ax_iterasi_boxplot.tick_params(axis='x', which='major', labelsize=font_size_tick)
            ax_iterasi_boxplot.tick_params(axis='y', which='major', labelsize=font_size_label-1)
        else:
            ax_iterasi_boxplot.text(0.5, 0.5, "Tidak ada data iterasi", ha='center', va='center', fontsize=font_size_label)
            ax_iterasi_boxplot.set_title('Distribusi Durasi Simulasi', fontsize=font_size_title)

        labels_ammo = ['Amunisi Persia']
        bar_width_ammo = 0.4
        rect_ammo_initial = ax_amunisi.bar(0 - bar_width_ammo/2, initial_total_persian_ammo_fixed, bar_width_ammo, 
                                           label=f'Awal ({initial_total_persian_ammo_fixed:.0f})', 
                                           color='darkgrey', edgecolor='black')
        rect_ammo_remaining = ax_amunisi.bar(0 + bar_width_ammo/2, avg_remaining_total_persian_ammo, bar_width_ammo, 
                                            label=f'Sisa Rata-rata ({avg_remaining_total_persian_ammo:.1f})', 
                                            color='skyblue', edgecolor='black')
        ax_amunisi.set_ylabel('Jumlah Amunisi', fontsize=font_size_label)
        ax_amunisi.set_title('Status Amunisi Persia', fontsize=font_size_title)
        ax_amunisi.set_xticks([0])
        ax_amunisi.set_xticklabels(labels_ammo, fontsize=font_size_label -1)
        ax_amunisi.legend(fontsize=font_size_legend, loc='best')
        ax_amunisi.grid(axis='y', linestyle=':')
        ax_amunisi.set_ylim(0, initial_total_persian_ammo_fixed * 1.15 if initial_total_persian_ammo_fixed > 0 else 10)
        for rect in rect_ammo_initial + rect_ammo_remaining:
            height = rect.get_height()
            ax_amunisi.annotate(f'{height:.1f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=font_size_text)
        if initial_total_persian_ammo_fixed > 0:
            percentage_used_text = f"{persian_ammo_usage_percentage:.1f}% digunakan"
            ax_amunisi.text(0, initial_total_persian_ammo_fixed * 0.6, percentage_used_text, 
                            ha='center', va='center', fontsize=font_size_text+1, color='black', fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=0.5, alpha=0.8))
        ax_amunisi.tick_params(axis='y', which='major', labelsize=font_size_tick)

        labels_units = ['Spartan', 'Persia']
        initial_counts = [spartans_initial_fixed, persians_initial_fixed]
        remaining_avg_counts = [avg_spartans_remaining, avg_persians_remaining]
        x_indices_units = np.arange(len(labels_units))
        bar_width = 0.35
        rects_initial = ax_jumlah_unit.bar(x_indices_units - bar_width/2, initial_counts, bar_width, label='Awal', color='coral', edgecolor='black')
        rects_remaining = ax_jumlah_unit.bar(x_indices_units + bar_width/2, remaining_avg_counts, bar_width, label='Rata-rata Sisa', color='lightseagreen', edgecolor='black')
        ax_jumlah_unit.set_ylabel('Jumlah Pasukan', fontsize=font_size_label)
        ax_jumlah_unit.set_title('Jumlah Pasukan: Awal vs. Rata-rata Sisa', fontsize=font_size_title)
        ax_jumlah_unit.set_xticks(x_indices_units)
        ax_jumlah_unit.set_xticklabels(labels_units, fontsize=font_size_label -1)
        ax_jumlah_unit.legend(fontsize=font_size_legend)
        ax_jumlah_unit.grid(axis='y', linestyle=':')
        for rect_group in [rects_initial, rects_remaining]:
            for rect in rect_group:
                height = rect.get_height()
                ax_jumlah_unit.annotate(f'{height:.1f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                                        xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=font_size_text)
        ax_jumlah_unit.tick_params(axis='both', which='major', labelsize=font_size_tick)

        labels_morale = ['Spartan', 'Persia']
        initial_morale_values = [spartan_initial_morale_fixed, persian_initial_morale_fixed]
        final_avg_morale_values = [avg_final_spartan_morale_overall, avg_final_persian_morale_overall]
        x_indices_morale = np.arange(len(labels_morale))
        rects_morale_initial = ax_moral.bar(x_indices_morale - bar_width/2, initial_morale_values, bar_width, label='Moral Awal', color='gold', edgecolor='black')
        rects_morale_final = ax_moral.bar(x_indices_morale + bar_width/2, final_avg_morale_values, bar_width, label='Rata-rata Moral Akhir', color='darkorange', edgecolor='black')
        ax_moral.set_ylabel('Nilai Moral', fontsize=font_size_label)
        ax_moral.set_title('Moral Pasukan: Awal vs. Rata-rata Akhir', fontsize=font_size_title)
        ax_moral.set_xticks(x_indices_morale)
        ax_moral.set_xticklabels(labels_morale, fontsize=font_size_label-1)
        ax_moral.legend(fontsize=font_size_legend)
        ax_moral.grid(axis='y', linestyle=':')
        ax_moral.set_ylim(0, max(max(initial_morale_values, default=0), max(final_avg_morale_values, default=0)) * 1.15 if initial_morale_values or final_avg_morale_values else 10)
        for rect_group in [rects_morale_initial, rects_morale_final]:
            for rect in rect_group:
                height = rect.get_height()
                ax_moral.annotate(f'{height:.1f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                                  xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=font_size_text)
        ax_moral.tick_params(axis='both', which='major', labelsize=font_size_tick)

        plt.tight_layout(rect=[0, 0, 1, 0.955])
        plt.show()

    except ImportError:
        print("\nMatplotlib atau NumPy tidak terinstal. Tidak dapat menampilkan grafik.")
        print("Silakan instal menggunakan: pip install matplotlib numpy")
    except Exception as e:
        print(f"\nTerjadi kesalahan saat plotting: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    results = run_multiple_simulations()
    analyze_and_plot_results(results)
