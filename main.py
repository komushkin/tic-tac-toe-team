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
