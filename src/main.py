import tkinter as tk

from gui.layout import FinancialModelingApp


def main():
    root = tk.Tk()
    root.title("Financial Modeling Application")
    root.geometry("600x400")

    FinancialModelingApp(root)  # noqa: F841

    root.mainloop()


if __name__ == "__main__":
    main()
