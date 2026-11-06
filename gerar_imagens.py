
import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("imagens", exist_ok=True)
AZUL = "#2a78d6"
LARANJA = "#eb6834"
ESCURO = "#0d366brendas = [1300, 1500, 1700, 1900, 2100, 2300, 2500, 2800, 3200, 40000]
media = np.mean(rendas)
mediana = np.median(rendas)

fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
cores = [AZUL] * 9 + [LARANJA]
ax.bar(range(1, 11), rendas, color=cores, width=0.7)
ax.axhline(media, color=LARANJA, linewidth=2)
ax.axhline(mediana, color=ESCURO, linewidth=2, linestyle="--")
ax.text(0.6, media + 900, f"Média: R$ {media:,.0f}".replace(",", "."), color=LARANJA, fontsize=10, fontweight="bold")
ax.text(0.6, mediana + 900, f"Mediana: R$ {mediana:,.0f}".replace(",", "."), color=ESCURO, fontsize=10, fontweight="bold")
ax.set_title("Dez casas da mesma rua: uma renda alta muda tudo", fontsize=12, loc="left")
ax.set_xlabel("Casas", color=TEXTO)
ax.set_ylabel("Renda do responsável (R$)", color=TEXTO)
ax.set_xticks(range(1, 11))
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig("imagens/media_x_mediana.png")
plt.close(fig)

dados = np.concatenate([np.random.default_rng(7).lognormal(7.6, 0.35, 300), [5200, 5900, 7000]])
q1, mediana, q3 = np.percentile(dados, [25, 50, 75])
iqr = q3 - q1

fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150)
ax.boxplot(dados, vert=False, widths=0.45, patch_artist=True,
           boxprops={"facecolor": "#cde2fb", "color": AZUL},
           medianprops={"color": ESCURO, "linewidth": 2},
           whiskerprops={"color": AZUL}, capprops={"color": AZUL},
           flierprops={"marker": "o", "markerfacecolor": LARANJA, "markeredgecolor": LARANJA, "markersize": 6})
ax.annotate("Q1 (25%)", xy=(q1, 1.23), xytext=(q1 - 600, 1.45), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("Mediana (50%)", xy=(mediana, 1.23), xytext=(mediana - 200, 1.55), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("Q3 (75%)", xy=(q3, 1.23), xytext=(q3 + 300, 1.45), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("", xy=(q1, 0.7), xytext=(q3, 0.7), arrowprops={"arrowstyle": "<->", "color": ESCURO})
ax.text((q1 + q3) / 2, 0.58, "IQR = Q3 − Q1", ha="center", fontsize=9, color=ESCURO)
ax.text(dados.max(), 0.78, "Outliers:\nacima de Q3 + 1,5 × IQR", ha="right", fontsize=9, color=LARANJA)
ax.set_yticks([])
ax.set_ylim(0.4, 1.75)
ax.set_xlabel("Renda (R$)", color=TEXTO)
ax.set_title("Como ler um boxplot", fontsize=12, loc="left")
ax.spines[["top", "right", "left"]].set_visible(False)
fig.tight_layout()
fig.savefig("imagens/como_ler_boxplot.png")
plt.close(fig)

print("imagens prontas na pasta imagens/")
