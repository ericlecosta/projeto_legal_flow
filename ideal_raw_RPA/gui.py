"""
Interface gráfica (CustomTkinter) para execução do RPA LMS.
Permite escolher o fluxo, ativar/desativar o modo headless e acompanhar os logs em tempo real.

Os fluxos são executados em um subprocesso (login.py / obter_otp.py), de forma que a interface
permanece responsiva e a execução pode ser interrompida a qualquer momento.
"""

import os
import re
import sys
import queue
import threading
import subprocess
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent

FLUXOS = {
    "Login completo no LMS": "login.py",
    "Somente obtenção do OTP": "obter_otp.py",
}

CREDENCIAIS_SENSIVEIS = ("USER_ID", "PASSWORD", "EMPLOYEE_NUMBER", "PERSONAL_IDENTIFICATION_CODE")

# Paleta LG: vermelho, preto e branco
LG_RED = "#A50034"
LG_RED_HOVER = "#C8003F"
LG_RED_DARK = "#5C001D"
BLACK = "#0B0B0B"
PANEL = "#161616"
PANEL_BORDER = "#2A2A2A"
WHITE = "#FFFFFF"
GRAY = "#9E9E9E"

CORES_LOG = {
    "info": "#E6E6E6",
    "warning": "#F5C451",
    "error": "#FF4D6D",
    "success": "#4ADE80",
    "header": WHITE,
    "system": GRAY,
}


def _carregar_credenciais() -> list[str]:
    """Lê os valores sensíveis do .env para mascará-los nos logs."""
    valores: list[str] = []
    for p in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        if p.exists():
            env = dotenv_values(p)
            valores += [env[k] for k in CREDENCIAIS_SENSIVEIS if env.get(k)]
    # Substitui os mais longos primeiro para evitar mascaramentos parciais
    return sorted(set(valores), key=len, reverse=True)


class RPAApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=BLACK)
        self.title("RPA LMS - Painel de Execução")
        self.geometry("1040x660")
        self.minsize(820, 520)

        self.processo: subprocess.Popen | None = None
        self.fila: queue.Queue = queue.Queue()
        self.inicio: float | None = None
        self.credenciais = _carregar_credenciais()

        self.var_fluxo = ctk.StringVar(value=next(iter(FLUXOS)))
        self.var_headless = ctk.BooleanVar(value=False)
        self.var_mascarar = ctk.BooleanVar(value=True)

        self._montar_layout()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.after(100, self._consumir_fila)

    # ------------------------------------------------------------------ UI
    def _montar_layout(self):
        fonte_titulo = ctk.CTkFont("Segoe UI", 22, "bold")
        fonte_secao = ctk.CTkFont("Segoe UI", 13, "bold")
        fonte_texto = ctk.CTkFont("Segoe UI", 13)
        fonte_menor = ctk.CTkFont("Segoe UI", 11)

        # Cabeçalho com faixa vermelha
        topo = ctk.CTkFrame(self, fg_color=LG_RED, corner_radius=0, height=76)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        ctk.CTkLabel(topo, text="RPA LMS  ·  Automação de Login", font=fonte_titulo, text_color=WHITE).pack(
            side="left", padx=24
        )
        ctk.CTkLabel(topo, text="Ideal Raw RPA — Equipe 1 Legal", font=fonte_menor, text_color=WHITE).pack(
            side="right", padx=24
        )

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=20, pady=20)

        # Painel de controles (esquerda)
        painel = ctk.CTkFrame(
            corpo, fg_color=PANEL, border_color=PANEL_BORDER, border_width=1, corner_radius=12, width=280
        )
        painel.pack(side="left", fill="y", padx=(0, 16))
        painel.pack_propagate(False)

        def secao(texto, topo_pad=18):
            ctk.CTkLabel(painel, text=texto.upper(), font=fonte_secao, text_color=LG_RED_HOVER).pack(
                anchor="w", padx=18, pady=(topo_pad, 8)
            )

        secao("Fluxo")
        for nome in FLUXOS:
            ctk.CTkRadioButton(
                painel,
                text=nome,
                value=nome,
                variable=self.var_fluxo,
                font=fonte_texto,
                text_color=WHITE,
                fg_color=LG_RED,
                hover_color=LG_RED_HOVER,
                border_color=GRAY,
            ).pack(anchor="w", padx=18, pady=4)

        secao("Navegador")
        ctk.CTkSwitch(
            painel,
            text="Modo headless",
            variable=self.var_headless,
            font=fonte_texto,
            text_color=WHITE,
            progress_color=LG_RED,
            button_color=WHITE,
            button_hover_color="#DDDDDD",
        ).pack(anchor="w", padx=18, pady=4)
        ctk.CTkLabel(
            painel,
            text="Desligado: o Chrome abre visível\npara acompanhar a automação.",
            font=fonte_menor,
            text_color=GRAY,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 6))
        ctk.CTkSwitch(
            painel,
            text="Ocultar credenciais nos logs",
            variable=self.var_mascarar,
            font=fonte_texto,
            text_color=WHITE,
            progress_color=LG_RED,
            button_color=WHITE,
            button_hover_color="#DDDDDD",
        ).pack(anchor="w", padx=18, pady=4)

        self.btn_executar = ctk.CTkButton(
            painel,
            text="▶   Executar",
            height=44,
            corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            fg_color=LG_RED,
            hover_color=LG_RED_HOVER,
            text_color=WHITE,
            text_color_disabled="#C9A0AE",
            command=self._executar,
        )
        self.btn_executar.pack(fill="x", padx=18, pady=(26, 8))
        self.btn_parar = ctk.CTkButton(
            painel,
            text="■   Interromper",
            height=38,
            corner_radius=8,
            font=fonte_texto,
            fg_color="transparent",
            border_color="#444444",
            border_width=1,
            hover_color="#262626",
            text_color=WHITE,
            text_color_disabled="#555555",
            state="disabled",
            command=self._parar,
        )
        self.btn_parar.pack(fill="x", padx=18)

        secao("Status", topo_pad=26)
        self.lbl_status = ctk.CTkLabel(painel, text="●  Aguardando", font=fonte_secao, text_color=GRAY, anchor="w")
        self.lbl_status.pack(anchor="w", fill="x", padx=18)
        self.lbl_tempo = ctk.CTkLabel(painel, text="Tempo: --", font=fonte_menor, text_color=GRAY)
        self.lbl_tempo.pack(anchor="w", padx=18)

        # Área de logs (direita)
        area = ctk.CTkFrame(corpo, fg_color=PANEL, border_color=PANEL_BORDER, border_width=1, corner_radius=12)
        area.pack(side="left", fill="both", expand=True)

        barra = ctk.CTkFrame(area, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(barra, text="LOGS DE EXECUÇÃO", font=fonte_secao, text_color=LG_RED_HOVER).pack(side="left")
        for texto, cmd in (("Salvar", self._salvar_logs), ("Limpar", self._limpar_logs)):
            ctk.CTkButton(
                barra,
                text=texto,
                width=80,
                height=30,
                corner_radius=6,
                font=fonte_menor,
                fg_color="#262626",
                hover_color="#333333",
                text_color=WHITE,
                command=cmd,
            ).pack(side="right", padx=(6, 0))

        self.txt_log = ctk.CTkTextbox(
            area,
            fg_color=BLACK,
            text_color=CORES_LOG["info"],
            font=ctk.CTkFont("Cascadia Mono", 12),
            wrap="word",
            corner_radius=8,
            border_width=0,
            scrollbar_button_color=LG_RED_DARK,
            scrollbar_button_hover_color=LG_RED,
        )
        self.txt_log.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.txt_log.configure(state="disabled")

        for tag, cor in CORES_LOG.items():
            self.txt_log.tag_config(tag, foreground=cor)

    # ------------------------------------------------------------ Execução
    def _executar(self):
        if self.processo and self.processo.poll() is None:
            return

        fluxo = self.var_fluxo.get()
        script = BASE_DIR / FLUXOS[fluxo]
        headless = self.var_headless.get()

        env = os.environ.copy()
        env.update(HEADLESS="true" if headless else "false", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")

        self._log(
            f"[{datetime.now():%H:%M:%S}] Iniciando '{fluxo}' " f"(headless={'sim' if headless else 'não'})", "system"
        )

        try:
            self.processo = subprocess.Popen(
                [sys.executable, "-u", str(script)],
                cwd=str(BASE_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            self._log(f"Falha ao iniciar o processo: {exc}", "error")
            return

        threading.Thread(target=self._ler_saida, args=(self.processo,), daemon=True).start()
        self.inicio = time.time()
        self._definir_status("Executando...", WHITE)
        self.btn_executar.configure(state="disabled", fg_color=LG_RED_DARK)
        self.btn_parar.configure(state="normal", border_color=WHITE)
        self._atualizar_tempo()

    def _ler_saida(self, proc: subprocess.Popen):
        for linha in proc.stdout:
            self.fila.put(("linha", linha.rstrip("\n")))
        proc.wait()
        self.fila.put(("fim", proc.returncode))

    def _parar(self):
        if not self.processo or self.processo.poll() is not None:
            return
        self._log("Interrompendo execução...", "warning")
        if os.name == "nt":
            # Encerra também os processos filhos (Chrome / driver do Playwright)
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(self.processo.pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            self.processo.terminate()

    def _consumir_fila(self):
        try:
            while True:
                tipo, valor = self.fila.get_nowait()
                if tipo == "linha":
                    self._log(valor, self._classificar(valor))
                else:
                    self._finalizar(valor)
        except queue.Empty:
            pass
        self.after(100, self._consumir_fila)

    def _finalizar(self, codigo: int):
        decorrido = time.time() - self.inicio if self.inicio else 0
        self.inicio = None
        if codigo == 0:
            self._definir_status("Concluído com sucesso", CORES_LOG["success"])
            self._log(f"Processo finalizado com sucesso em {decorrido:.1f}s.", "success")
        else:
            self._definir_status("Falhou / interrompido", CORES_LOG["error"])
            self._log(f"Processo finalizado com código {codigo} após {decorrido:.1f}s.", "error")
        self.lbl_tempo.configure(text=f"Tempo: {decorrido:.1f}s")
        self.btn_executar.configure(state="normal", fg_color=LG_RED)
        self.btn_parar.configure(state="disabled", border_color="#444444")

    def _atualizar_tempo(self):
        if self.inicio is None:
            return
        self.lbl_tempo.configure(text=f"Tempo: {time.time() - self.inicio:.1f}s")
        self.after(200, self._atualizar_tempo)

    # ---------------------------------------------------------------- Logs
    @staticmethod
    def _classificar(linha: str) -> str:
        if "[ERROR]" in linha or "[ERRO" in linha or "Traceback" in linha:
            return "error"
        if "[WARNING]" in linha:
            return "warning"
        if "SUCESSO" in linha.upper() and "[INFO]" not in linha:
            return "success"
        if re.fullmatch(r"\s*=+\s*", linha) or "RPA LMS -" in linha:
            return "header"
        return "info"

    def _mascarar(self, texto: str) -> str:
        if not self.var_mascarar.get():
            return texto
        for valor in self.credenciais:
            texto = texto.replace(valor, "*" * 8)
        return texto

    def _log(self, texto: str, tag: str = "info"):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", self._mascarar(texto) + "\n", tag)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _limpar_logs(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def _salvar_logs(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".log",
            initialfile=f"rpa_lms_{datetime.now():%Y%m%d_%H%M%S}.log",
            filetypes=[("Log", "*.log"), ("Texto", "*.txt")],
        )
        if caminho:
            Path(caminho).write_text(self.txt_log.get("1.0", "end"), encoding="utf-8")

    def _definir_status(self, texto: str, cor: str):
        self.lbl_status.configure(text=f"●  {texto}", text_color=cor)

    def _ao_fechar(self):
        if self.processo and self.processo.poll() is None:
            if not messagebox.askyesno("Sair", "Há uma execução em andamento. Interromper e sair?"):
                return
            self._parar()
        self.destroy()


if __name__ == "__main__":
    RPAApp().mainloop()
