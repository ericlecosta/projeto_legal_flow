import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import sys, os

OUT = sys.argv[1]
INK = "#111827"
AE = "#6D28D9"


def box(ax, x, y, w, h, text, fc, ec, fs=9.5, bold=False, tc=INK):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.6))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc,
            weight="bold" if bold else "normal", linespacing=1.15)


def arrow(ax, p, q, col="#374151", ls="-", rad=0.0, lw=1.6, label=None, lpos=None):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>,head_length=7,head_width=4", color=col, lw=lw,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
    if label:
        x, y = lpos or ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5, color=col,
                bbox=dict(fc="white", ec="none", pad=1.5))


def lane(ax, x0, y0, w, h, title, fc, ec):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.15", fc=fc, ec=ec,
                                lw=1.2, ls="--"))
    ax.text(x0 + 0.18, y0 + h - 0.22, title, ha="left", va="top", fontsize=10.5, weight="bold", color=ec)


def legend_chip(ax, x, y, text, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), 0.28, 0.2, boxstyle="round,pad=0,rounding_size=0.04", fc=fc, ec=ec))
    ax.text(x + 0.36, y + 0.1, text, va="center", fontsize=8.5, color=INK)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)


# ---------- 1. Fluxo atual (AS-IS x TO-BE) ----------
fig, ax = plt.subplots(figsize=(15, 7.3), dpi=170)
ax.set_xlim(0, 15); ax.set_ylim(0, 7.3); ax.axis("off")
ax.text(7.5, 7.2, "Fluxo do processo: cenário manual (AS-IS) e escopo atual do robô (TO-BE)",
        ha="center", va="top", fontsize=13.5, weight="bold", color=INK)
lane(ax, 0.2, 4.2, 14.6, 2.4, "AS-IS  ·  processo manual  ·  4 a 5 h por execução  ·  cerca de 2 vezes por semana",
     "#FEF2F2", "#B91C1C")
asis = ["Exportar relatório\nmacro do LMS", "Selecionar\ncontratos MAO", "Abrir contrato\npor contrato",
        "Ler o Approval\nHistory", "Copiar as 8\ndatas à mão", "Consolidar na\nBase Ideal.xlsx"]
xs = [1.5 + i * 2.4 for i in range(6)]
for i, (x, t) in enumerate(zip(xs, asis)):
    box(ax, x, 5.25, 2.0, 1.0, t, "#FEE2E2" if i in (2, 3, 4) else "white", "#B91C1C")
    if i:
        arrow(ax, (xs[i - 1] + 1.0, 5.25), (x - 1.0, 5.25))
ax.text(xs[3], 4.45, "cerca de 80% do esforço: repetitivo e sujeito a erro de digitação", ha="center",
        fontsize=9, style="italic", color="#B91C1C")
lane(ax, 0.2, 0.2, 14.6, 3.75, "TO-BE  ·  escopo atual do RPA Ideal Raw  ·  execução autônoma em menos de 40 min  ·  todo dia útil",
     "#EFF6FF", "#1D4ED8")
row1 = [("Agendador\ndias úteis", "white"), ("Login SSO\nOTP + Captcha (OCR)", "#DCFCE7"),
        ("Filtro LGESP\n+ exportação", "#FEF9C3"), ("Filtro MAO\n(Pandas)", "white"),
        ("Mineração do\nApproval History", "#FEF9C3")]
row2 = [("De/Para por\nregras fixas", "white"), ("Base Ideal.xlsx\n(aba Ideal Raw)", "white"),
        ("E-mail com\nresumo e logs", "white"), ("Validação humana\nde toda a base", "#F3F4F6")]
xs1 = [1.6 + i * 2.95 for i in range(5)]
for i, (x, (t, c)) in enumerate(zip(xs1, row1)):
    box(ax, x, 2.75, 2.3, 0.95, t, c, "#1D4ED8")
    if i:
        arrow(ax, (xs1[i - 1] + 1.15, 2.75), (x - 1.15, 2.75))
xs2 = [xs1[4] - i * 3.5 for i in range(4)]
for i, (x, (t, c)) in enumerate(zip(xs2, row2)):
    box(ax, x, 1.0, 2.3, 0.95, t, c, "#1D4ED8" if i < 3 else "#6B7280")
    if i:
        arrow(ax, (xs2[i - 1] - 1.15, 1.0), (x + 1.15, 1.0))
arrow(ax, (xs1[4], 2.27), (xs2[0], 1.48))
legend_chip(ax, 0.5, 1.78, "Implementado", "#DCFCE7", "#1D4ED8")
legend_chip(ax, 2.4, 1.78, "Seletores mapeados", "#FEF9C3", "#1D4ED8")
legend_chip(ax, 4.75, 1.78, "A desenvolver", "white", "#1D4ED8")
save(fig, "01_fluxo_atual.png")

# ---------- 2. Fluxo com agentes ----------
fig, ax = plt.subplots(figsize=(15, 9.2), dpi=170)
ax.set_xlim(0, 15); ax.set_ylim(0, 9.2); ax.axis("off")
ax.text(7.5, 9.1, "Fluxo proposto com agentes inteligentes (modelos LLM locais, offline)", ha="center", va="top",
        fontsize=13.5, weight="bold", color=INK)
lane(ax, 0.2, 6.6, 14.6, 1.9, "Humano (Human-in-the-Loop)", "#F9FAFB", "#4B5563")
lane(ax, 0.2, 2.75, 14.6, 3.2, "Camada de agentes (orquestrador + trabalhadores)", "#F5F3FF", AE)
lane(ax, 0.2, 0.2, 14.6, 2.3, "Ferramentas determinísticas (RPA atual reaproveitado)", "#EFF6FF", "#1D4ED8")
box(ax, 1.55, 4.25, 2.2, 1.9, "Agente 1\nORQUESTRADOR\n\nplaneja, delega,\ndecide retry ou\nescalonamento", "#DDD6FE", AE, fs=9)
ag = [(4.35, "Agente 2\nNAVEGADOR\nself-healing de seletores"),
      (7.05, "Agente 3\nEXTRATOR\ntimeline → 8 datas + estado"),
      (9.75, "Agente 4\nVALIDADOR\nregras + comparação + LLM"),
      (12.75, "Agente 5\nANALISTA\nresumo, alertas, perguntas")]
for x, t in ag:
    box(ax, x, 4.7, 2.35, 1.15, t, "#EDE9FE", AE, fs=9)
for i in range(len(ag) - 1):
    arrow(ax, (ag[i][0] + 1.18, 4.7), (ag[i + 1][0] - 1.18, 4.7), col=AE)
arrow(ax, (8.95, 5.28), (7.6, 5.28), col="#B45309", rad=0.6, ls="--")
ax.text(8.15, 5.84, "reprocessar (avaliador–otimizador)", ha="center", fontsize=8.3, color="#B45309", style="italic")
arrow(ax, (2.65, 4.25), (ag[0][0] - 1.18, 4.55), col=AE)
ax.plot([1.55, 1.55, 12.75], [3.3, 3.05, 3.05], color=AE, lw=1, ls=":")
for x, _ in ag:
    ax.plot([x, x], [3.05, 4.12], color=AE, lw=1, ls=":")
ax.text(7.05, 2.9, "controle e logs do orquestrador", ha="center", fontsize=8, color=AE, style="italic")
tools = [(1.55, "Agendador\ndias úteis"), (4.1, "Login SSO\nOTP + Captcha"), (6.5, "Filtro LGESP\n+ exportação"),
         (8.9, "Filtro MAO\n(Pandas)"), (11.3, "Base Ideal.xlsx\nversionada"), (13.6, "E-mail\n(SMTP)")]
for x, t in tools:
    box(ax, x, 1.15, 2.0, 0.9, t, "white", "#1D4ED8", fs=9)
arrow(ax, (1.55, 1.6), (1.55, 3.3), col="#1D4ED8", label="dispara", lpos=(1.55, 2.45))
for xt in (4.1, 6.5, 8.9):
    arrow(ax, (4.35, 4.12), (xt, 1.6), col="#1D4ED8", ls="--", lw=1.1)
arrow(ax, (9.75, 4.12), (11.3, 1.6), col="#1D4ED8", label="base aprovada", lpos=(10.75, 2.2))
arrow(ax, (12.75, 4.12), (13.6, 1.6), col="#1D4ED8", label="resumo", lpos=(13.45, 2.2))
box(ax, 9.95, 7.5, 3.0, 1.0, "Analista de Contratos\nrevisa só as exceções", "white", "#4B5563", fs=9.5)
box(ax, 12.95, 7.5, 2.7, 1.0, "Gestora do Jurídico\nlê o resumo e pergunta", "white", "#4B5563", fs=9.5)
arrow(ax, (9.6, 5.28), (9.6, 7.0), col="#B91C1C", label="exceções", lpos=(9.0, 6.3))
arrow(ax, (10.3, 7.0), (10.3, 5.28), col="#15803D", label="aprova / corrige", lpos=(11.15, 6.3))
arrow(ax, (12.95, 7.0), (12.85, 5.28), col="#4B5563", label="perguntas", lpos=(13.55, 6.3))
box(ax, 4.55, 7.5, 6.9, 1.0,
    "Guardrails: somente leitura no LMS · credenciais no .env · dados não saem da LG\n"
    "(LLMs locais via Ollama) · o LLM não altera dados sozinho · toda decisão fica em log",
    "#FFFBEB", "#B45309", fs=8.4)
save(fig, "02_fluxo_com_agentes.png")

# ---------- 3. Arquitetura ----------
fig, ax = plt.subplots(figsize=(13, 6.4), dpi=170)
ax.set_xlim(0, 13); ax.set_ylim(0, 6.4); ax.axis("off")
ax.text(6.5, 6.3, "Arquitetura: Orquestrador–Trabalhadores com ReAct, Avaliador–Otimizador e Human-in-the-Loop",
        ha="center", va="top", fontsize=12.5, weight="bold", color=INK)
box(ax, 6.5, 5.1, 4.4, 0.9, "ORQUESTRADOR (supervisor)\nestado da execução · plano · roteamento", "#DDD6FE", AE,
    fs=9.5, bold=True)
ws = [(1.9, "Navegador"), (5.0, "Extrator"), (8.0, "Validador"), (11.1, "Analista")]
for x, t in ws:
    box(ax, x, 2.9, 2.5, 1.5, "", "#F5F3FF", AE)
    ax.text(x, 3.4, t.upper(), ha="center", fontsize=10, weight="bold", color=AE)
    ax.text(x, 2.7, "ReAct:\npensar → agir (ferramenta)\n→ observar", ha="center", va="center", fontsize=8.5,
            color=INK)
    arrow(ax, (6.5, 4.63), (x, 3.68), col=AE)
arrow(ax, (6.75, 2.45), (6.25, 2.45), col="#B45309", ls="--")
ax.text(6.5, 1.95, "avaliador–\notimizador", ha="center", fontsize=8.3, color="#B45309", style="italic")
for x, t in [(1.9, "Playwright · seletores\nscreenshot / DOM"), (5.0, "Legenda · De/Para\nexemplos (few-shot)"),
             (8.0, "Pandas (regras)\nbase anterior"), (11.1, "Base consolidada\nhistórico")]:
    box(ax, x, 0.85, 2.5, 0.85, t, "white", "#1D4ED8", fs=8.6)
    arrow(ax, (x, 2.13), (x, 1.3), col="#1D4ED8")
box(ax, 11.4, 5.1, 2.4, 0.8, "Humano\n(exceções)", "white", "#4B5563", fs=9.5)
arrow(ax, (8.6, 3.68), (10.3, 4.75), col="#B91C1C", label="exceções", lpos=(9.3, 4.45))
save(fig, "03_arquitetura_agentes.png")

# ---------- 4. Agente Validador ----------
fig, ax = plt.subplots(figsize=(14, 5.6), dpi=170)
ax.set_xlim(0, 14); ax.set_ylim(0, 5.6); ax.axis("off")
ax.text(7, 5.5, "Agente Validador: validação em 3 camadas", ha="center", va="top", fontsize=13.5,
        weight="bold", color=INK)
box(ax, 1.2, 3.6, 1.9, 0.9, "Base gerada\npelo robô", "white", "#1D4ED8")
box(ax, 1.2, 1.7, 1.9, 0.9, "Base do dia\nanterior", "white", "#1D4ED8")
box(ax, 3.9, 3.6, 2.4, 1.3, "CAMADA 1\nRegras (Pandas)\nformato · domínio\nordem das datas", "#DCFCE7", "#15803D", fs=8.8)
box(ax, 6.8, 3.6, 2.4, 1.3, "CAMADA 2\nComparação\nmudanças · regressões\nvolume · nulos", "#DCFCE7", "#15803D", fs=8.8)
box(ax, 9.6, 1.5, 2.7, 1.3, "CAMADA 3 (LLM)\nexplica · classifica\na gravidade · investiga\n(ReAct: logs, screenshots)",
    "#EDE9FE", AE, fs=8.8)
box(ax, 12.6, 3.6, 2.0, 0.9, "Base aprovada", "#DBEAFE", "#1D4ED8", bold=True)
box(ax, 12.6, 0.6, 2.0, 0.9, "Fila de revisão\n(Analista)", "white", "#B91C1C")
box(ax, 12.6, 4.95, 2.2, 0.6, "E-mail + relatório\nde qualidade", "white", "#1D4ED8", fs=8.5)
arrow(ax, (2.15, 3.6), (2.7, 3.6))
arrow(ax, (5.1, 3.6), (5.6, 3.6))
arrow(ax, (2.15, 1.7), (6.8, 2.95), rad=0.15)
arrow(ax, (8.0, 3.6), (11.6, 3.6), col="#15803D", label="sem anomalia", lpos=(9.8, 3.85))
arrow(ax, (6.8, 2.95), (8.25, 1.75), col="#B45309", label="anomalias", lpos=(7.3, 2.15))
arrow(ax, (10.95, 1.95), (11.9, 3.15), col="#15803D", label="verde / amarelo", lpos=(11.0, 2.75))
arrow(ax, (10.95, 1.0), (11.6, 0.7), col="#B91C1C", label="vermelho", lpos=(11.15, 0.5))
arrow(ax, (12.6, 1.05), (12.6, 3.15), col="#15803D", label="aprova /\ncorrige", lpos=(13.3, 2.1))
arrow(ax, (12.6, 4.05), (12.6, 4.65), col="#1D4ED8")
save(fig, "04_agente_validador.png")
print("ok")
