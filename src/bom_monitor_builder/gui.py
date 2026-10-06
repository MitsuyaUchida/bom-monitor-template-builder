from __future__ import annotations

import queue
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from bom_monitor_builder.build.models import BuildResult
from bom_monitor_builder.gui_service import (
    GuiBuildRequest,
    create_build_request,
    default_output_path,
    execute_gui_build,
)


class BuilderWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BOM Monitor Builder - CAB to Excel")
        self.root.geometry("820x590")
        self.root.minsize(720, 500)
        self.root.protocol("WM_DELETE_WINDOW", self._exit_application)
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=True)
        self.keep_intermediate_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="CABファイルを選択してください。")
        self._output_is_auto = True
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._running = False
        self._build_widgets()

    def _build_widgets(self) -> None:
        body = ttk.Frame(self.root, padding=16)
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(5, weight=1)

        ttk.Label(body, text="CABファイル").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        self.input_entry = ttk.Entry(body, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, sticky="ew", pady=6)
        self.input_browse_button = ttk.Button(body, text="参照", command=self._browse_cab)
        self.input_browse_button.grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(body, text="出力Excel").grid(row=1, column=0, sticky="w", padx=(0, 12), pady=6)
        self.output_entry = ttk.Entry(body, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.output_entry.bind("<Key>", self._mark_output_as_manual)
        self.output_browse_button = ttk.Button(body, text="参照", command=self._browse_output)
        self.output_browse_button.grid(row=1, column=2, padx=(8, 0), pady=6)

        options = ttk.Frame(body)
        options.grid(row=2, column=1, columnspan=2, sticky="w", pady=(6, 10))
        self.overwrite_check = ttk.Checkbutton(options, text="既存ファイルを上書き", variable=self.overwrite_var)
        self.overwrite_check.pack(side=tk.LEFT, padx=(0, 20))
        self.keep_intermediate_check = ttk.Checkbutton(
            options, text="中間ファイルを残す", variable=self.keep_intermediate_var
        )
        self.keep_intermediate_check.pack(side=tk.LEFT)

        self.start_button = ttk.Button(body, text="変換開始", command=self._start_conversion)
        self.start_button.grid(row=3, column=1, sticky="w", pady=(2, 8))
        self.exit_button = ttk.Button(body, text="終了", command=self._exit_application)
        self.exit_button.grid(row=3, column=0, sticky="w", pady=(2, 8))
        self.status_label = ttk.Label(body, textvariable=self.status_var)
        self.status_label.grid(row=3, column=2, sticky="e", pady=(2, 8))
        ttk.Label(body, text="実行ログ").grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 4))
        self.log_view = ScrolledText(body, height=18, wrap=tk.WORD, state=tk.DISABLED)
        self.log_view.grid(row=5, column=0, columnspan=3, sticky="nsew")

    def _browse_cab(self) -> None:
        selected = filedialog.askopenfilename(
            title="CABファイルを選択",
            filetypes=[("CAB files", "*.CAB *.cab"), ("All files", "*.*")],
        )
        if selected:
            self.input_var.set(selected)
            if self._output_is_auto or not self.output_var.get().strip():
                self.output_var.set(str(default_output_path(selected)))
                self._output_is_auto = True

    def _browse_output(self) -> None:
        current = self.output_var.get().strip()
        if not current and self.input_var.get().strip():
            current = str(default_output_path(self.input_var.get().strip()))
        initial_path = Path(current) if current else None
        selected = filedialog.asksaveasfilename(
            title="出力Excelの保存先を選択",
            initialdir=str(initial_path.parent) if initial_path else None,
            initialfile=initial_path.name if initial_path else None,
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
        )
        if selected:
            self.output_var.set(selected)
            self._output_is_auto = False

    def _mark_output_as_manual(self, _event: tk.Event[tk.Misc]) -> None:
        self._output_is_auto = False

    def _start_conversion(self) -> None:
        if self._running:
            return
        try:
            request = create_build_request(
                self.input_var.get(), self.output_var.get(),
                overwrite=self.overwrite_var.get(),
                keep_intermediate=self.keep_intermediate_var.get(),
            )
        except (ValueError, OSError) as exc:
            messagebox.showerror("入力を確認してください", str(exc), parent=self.root)
            return
        self._set_running(True)
        self._append_log(f"入力CAB: {request.input_path}")
        self._append_log(f"出力Excel: {request.output_path}")
        self._append_log("変換中...")
        threading.Thread(target=self._run_build, args=(request,), name="bom-monitor-build", daemon=True).start()
        self.root.after(100, self._poll_worker)

    def _run_build(self, request: GuiBuildRequest) -> None:
        try:
            result = execute_gui_build(request)
        except Exception as exc:
            self._events.put(("error", (str(exc), traceback.format_exc())))
        else:
            self._events.put(("success", result))

    def _poll_worker(self) -> None:
        try:
            kind, payload = self._events.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_worker)
            return
        self._set_running(False)
        if kind == "success":
            self._show_success(payload)  # type: ignore[arg-type]
            return
        error_text, traceback_text = payload  # type: ignore[misc]
        self._append_log(f"変換に失敗しました: {error_text}")
        self._append_log(traceback_text)
        self.status_var.set("変換に失敗しました。")
        messagebox.showerror("変換に失敗しました", f"変換に失敗しました。\n\n{error_text}", parent=self.root)

    def _show_success(self, result: BuildResult) -> None:
        self._append_log(f"Profile: {result.profile_id}")
        self._append_log(f"Groups: {result.group_count}")
        self._append_log(f"Monitors: {result.monitor_count}")
        self._append_log("Validation: PASS")
        self._append_log("Build completed successfully.")
        self.status_var.set("変換が正常に完了しました。")
        messagebox.showinfo(
            "変換完了", f"変換が正常に完了しました。\n\n出力:\n{result.output_path}", parent=self.root
        )

    def _append_log(self, message: str) -> None:
        self.log_view.configure(state=tk.NORMAL)
        self.log_view.insert(tk.END, message + "\n")
        self.log_view.see(tk.END)
        self.log_view.configure(state=tk.DISABLED)

    def _set_running(self, running: bool) -> None:
        self._running = running
        state = tk.DISABLED if running else tk.NORMAL
        for widget in (
            self.input_entry, self.input_browse_button, self.output_entry, self.output_browse_button,
            self.overwrite_check, self.keep_intermediate_check, self.start_button,
        ):
            widget.configure(state=state)
        if running:
            self.status_var.set("変換中...")

    def _exit_application(self) -> None:
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    BuilderWindow(root)
    root.mainloop()
