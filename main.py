"""Игра «Крестики-нолики» для двух игроков."""

import time
import tkinter as tk
from tkinter import messagebox, ttk


class Game:
    """Хранить поле и проверять правила партии для двух игроков."""

    LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )

    def __init__(self):
        """Создать пустую партию."""
        self.reset()

    def reset(self):
        """Очистить поле и передать первый ход X."""
        self.board = [""] * 9
        self.current = "X"
        self.winner = None
        self.winning_line = None
        self.draw = False

    @property
    def finished(self):
        """Сообщить, закончилась ли партия."""
        return self.winner is not None or self.draw

    def play(self, index):
        """Выполнить ход и вернуть фигуру; ошибку обозначить ValueError."""
        if type(index) is not int or not 0 <= index < 9:
            raise ValueError("Номер клетки должен быть целым от 0 до 8.")
        if self.finished:
            raise ValueError("Партия уже завершена.")
        if self.board[index]:
            raise ValueError("Клетка уже занята.")
        mark = self.current
        self.board[index] = mark
        for line in self.LINES:
            if all(self.board[cell] == mark for cell in line):
                self.winner = mark
                self.winning_line = line
                break
        self.draw = not self.winner and all(self.board)
        if not self.finished:
            self.current = "O" if mark == "X" else "X"
        return mark


class BoardRenderer:
    """Отображать поле, фигуры и выигрышную линию на Canvas."""

    SIZE = 420
    CELL = SIZE // 3
    COLORS = {"X": "#2563eb", "O": "#e05b39"}

    def __init__(self, parent):
        """Создать игровое полотно фиксированного размера."""
        self.canvas = tk.Canvas(
            parent, width=self.SIZE, height=self.SIZE,
            bg="#ffffff", highlightthickness=0, cursor="hand2",
        )
        self.canvas.pack(pady=16)
        self.clear()

    def clear(self):
        """Очистить фигуры и заново нарисовать сетку."""
        self.canvas.delete("all")
        for offset in (self.CELL, self.CELL * 2):
            self.canvas.create_line(
                offset, 12, offset, self.SIZE - 12,
                fill="#dce3ed", width=3,
            )
            self.canvas.create_line(
                12, offset, self.SIZE - 12, offset,
                fill="#dce3ed", width=3,
            )

    def center(self, index):
        """Вернуть координаты центра клетки."""
        row, column = divmod(index, 3)
        return ((column + 0.5) * self.CELL,
                (row + 0.5) * self.CELL)

    def draw_mark(self, index, mark, progress):
        """Нарисовать долю фигуры от нуля до единицы."""
        tag = f"mark_{index}"
        self.canvas.delete(tag)
        x, y = self.center(index)
        radius = 39
        color = self.COLORS[mark]
        if mark == "X":
            # Половина времени отведена каждой диагонали крестика.
            for start_x, end_x, part in (
                (x - radius, x + radius, min(1, progress * 2)),
                (x + radius, x - radius, max(0, progress * 2 - 1)),
            ):
                if part > 0:
                    self.canvas.create_line(
                        start_x, y - radius,
                        start_x + (end_x - start_x) * part,
                        y - radius + 2 * radius * part,
                        fill=color, width=8, capstyle=tk.ROUND, tags=tag,
                    )
        elif progress >= 1:
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                outline=color, width=8, tags=tag,
            )
        elif progress > 0:
            self.canvas.create_arc(
                x - radius, y - radius, x + radius, y + radius,
                start=90, extent=-360 * progress, style=tk.ARC,
                outline=color, width=8, tags=tag,
            )

    def draw_win(self, line, progress):
        """Соединить крайние клетки выигрышной линии."""
        self.canvas.delete("win")
        x1, y1 = self.center(line[0])
        x2, y2 = self.center(line[-1])
        self.canvas.create_line(
            x1, y1, x1 + (x2 - x1) * progress,
            y1 + (y2 - y1) * progress,
            fill="#16a36a", width=7, capstyle=tk.ROUND, tags="win",
        )


class Controls:
    """Создать панель управления и отображать состояние игры."""

    def __init__(self, parent, new_round, reset_scores, show_rules):
        """Разместить статус, счёт, кнопки и ползунок."""
        self.status = tk.StringVar(value="Ход X")
        self.score = tk.StringVar(value="X: 0   ·   Ничьи: 0   ·   O: 0")
        self.duration = tk.IntVar(value=260)
        ttk.Label(parent, textvariable=self.status,
                  font=("Segoe UI", 18, "bold")).pack()
        ttk.Label(parent, textvariable=self.score,
                  font=("Segoe UI", 11)).pack(pady=(6, 14))
        buttons = ttk.Frame(parent)
        buttons.pack()
        for title, command in (
            ("Новая партия", new_round),
            ("Сбросить счёт", reset_scores),
            ("Правила", show_rules),
        ):
            ttk.Button(buttons, text=title, command=command).pack(
                side=tk.LEFT, padx=4,
            )
        settings = ttk.Frame(parent)
        settings.pack(fill=tk.X, pady=(18, 0))
        ttk.Label(settings, text="Длительность хода (мс)").pack()
        tk.Scale(
            settings, from_=100, to=600, resolution=20,
            orient=tk.HORIZONTAL, variable=self.duration,
            length=320, highlightthickness=0,
        ).pack()


class App:
    """Управлять окном и жизненным циклом анимированной партии."""

    def __init__(self):
        """Создать окно и подключить события управления."""
        self.root = tk.Tk()
        self.root.title("Крестики-нолики")
        self.root.resizable(False, False)
        self.game = Game()
        self.scores = {"X": 0, "O": 0, "draw": 0}
        self.busy = False
        self.pending = None
        container = ttk.Frame(self.root, padding=24)
        container.pack()
        ttk.Label(container, text="КРЕСТИКИ-НОЛИКИ",
                  font=("Segoe UI", 22, "bold")).pack()
        ttk.Label(container, text="Два игрока · одно поле · три в ряд").pack(
            pady=(4, 0),
        )
        self.renderer = BoardRenderer(container)
        self.controls = Controls(
            container, self.new_round, self.reset_scores, self.show_rules,
        )
        ttk.Label(
            container, text="1–9 — ход    R — новая партия    F1 — правила",
            font=("Segoe UI", 9),
        ).pack(pady=(12, 0))
        self.renderer.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<KeyPress>", self.on_key)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def run(self):
        """Запустить цикл обработки событий tkinter."""
        self.root.mainloop()

    def on_click(self, event):
        """Преобразовать щелчок в индекс клетки."""
        size = self.renderer.SIZE
        if 0 <= event.x < size and 0 <= event.y < size:
            cell = self.renderer.CELL
            self.play((event.y // cell) * 3 + event.x // cell)

    def on_key(self, event):
        """Обработать горячие клавиши, не мешая ползунку."""
        if event.char in "123456789" and event.char:
            self.play(int(event.char) - 1)
        elif event.keysym.lower() == "r":
            self.new_round()
        elif event.keysym == "F1":
            self.show_rules()
        elif event.keysym == "Escape":
            self.close()

    def play(self, index):
        """Выполнить допустимый ход и анимировать его."""
        if self.busy or self.game.finished:
            return
        try:
            mark = self.game.play(index)
        except ValueError:
            self.root.bell()
            return
        self.busy = True
        self.controls.status.set(f"Ход {mark}…")
        self.animate(
            lambda progress: self.renderer.draw_mark(index, mark, progress),
            self.finish_move,
        )

    def animate(self, draw, complete):
        """Планировать кадры по времени без блокировки интерфейса."""
        start = time.perf_counter()
        duration = self.controls.duration.get() / 1000

        def frame():
            """Нарисовать кадр и запланировать следующий."""
            self.pending = None
            progress = min(1.0, (time.perf_counter() - start) / duration)
            draw(progress)
            if progress < 1:
                self.pending = self.root.after(16, frame)
            else:
                complete()

        frame()

    def finish_move(self):
        """Обновить результат и при победе запустить подсветку."""
        if self.game.winner:
            winner = self.game.winner
            self.scores[winner] += 1
            self.controls.status.set(f"Победил {winner}!")
            self.update_score()
            self.animate(
                lambda progress: self.renderer.draw_win(
                    self.game.winning_line, progress,
                ),
                self.unlock,
            )
        elif self.game.draw:
            self.scores["draw"] += 1
            self.controls.status.set("Ничья!")
            self.update_score()
            self.unlock()
        else:
            self.controls.status.set(f"Ход {self.game.current}")
            self.unlock()

    def unlock(self):
        """Разрешить следующий ход после завершения анимации."""
        self.busy = False

    def update_score(self):
        """Обновить счёт текущего сеанса."""
        self.controls.score.set(
            f"X: {self.scores['X']}   ·   "
            f"Ничьи: {self.scores['draw']}   ·   O: {self.scores['O']}",
        )

    def new_round(self):
        """Отменить кадр анимации и начать новую партию."""
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None
        self.game.reset()
        self.renderer.clear()
        self.busy = False
        self.controls.status.set("Ход X")

    def reset_scores(self):
        """Очистить счёт и поле."""
        self.scores = {"X": 0, "O": 0, "draw": 0}
        self.new_round()
        self.update_score()

    def show_rules(self):
        """Показать правила и управление."""
        messagebox.showinfo(
            "Правила игры",
            "Два игрока по очереди ставят X и O в свободные клетки.\n"
            "X начинает. Три одинаковые фигуры в строке, столбце или\n"
            "диагонали приносят победу. Полное поле без победы — ничья.\n\n"
            "Щелчок или 1–9 — ход (клетки по строкам сверху вниз).\n"
            "R — новая партия, Escape — выход.\n"
            "Ползунок задаёт длительность следующей анимации.",
            parent=self.root,
        )

    def close(self):
        """Отменить ожидающий кадр и закрыть окно."""
        if self.pending is not None:
            self.root.after_cancel(self.pending)
        self.root.destroy()


if __name__ == "__main__":
    App().run()
