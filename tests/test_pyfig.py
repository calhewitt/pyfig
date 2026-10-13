import os
import pickle
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["MPLBACKEND"] = "Agg"

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from pyfig import load_figure, save_figure
from pyfig.cli import main


class PyfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(plt.close, "all")

    def test_round_trip_preserves_plot_and_adds_extension(self):
        figure, axes = plt.subplots()
        axes.plot([1, 2, 3], [4, 5, 6], label="measurements")
        axes.set_title("Example")

        path = save_figure(figure, Path(self.directory.name) / "plot")
        self.assertEqual(path.suffix, ".pyfig")
        self.assertTrue(path.is_file())

        restored = load_figure(path)
        self.assertIsInstance(restored, Figure)
        self.assertEqual(restored.axes[0].get_title(), "Example")
        self.assertEqual(restored.axes[0].lines[0].get_ydata().tolist(), [4, 5, 6])
        self.assertEqual(restored.axes[0].lines[0].get_label(), "measurements")

    def test_existing_extension_is_kept(self):
        path = Path(self.directory.name) / "plot.pyfig"
        self.assertEqual(save_figure(Figure(), path), path)

    def test_rejects_non_figures(self):
        path = Path(self.directory.name) / "invalid.pyfig"
        with self.assertRaises(TypeError):
            save_figure(object(), path)

        with path.open("wb") as file:
            pickle.dump({"not": "a figure"}, file)
        with self.assertRaises(TypeError):
            load_figure(path)

    def test_opener_registers_a_figure_created_without_pyplot(self):
        figure = Figure()
        figure.subplots().plot([0, 1], [2, 3])
        path = save_figure(figure, Path(self.directory.name) / "bare.pyfig")

        with patch("pyfig.cli.plt.show") as show:
            self.assertEqual(main([str(path)]), 0)
            show.assert_called_once_with()

        self.assertEqual(len(plt.get_fignums()), 1)
        self.assertEqual(plt.gcf().axes[0].lines[0].get_ydata().tolist(), [2, 3])

    def test_executable_opens_a_saved_figure(self):
        path = save_figure(Figure(), Path(self.directory.name) / "script.pyfig")
        script = Path(__file__).resolve().parents[1] / "open_pyfig"
        result = subprocess.run(
            [str(script), str(path)],
            env={**os.environ, "MPLBACKEND": "Agg"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
