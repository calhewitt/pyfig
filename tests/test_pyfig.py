import os
import pickle
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

os.environ["MPLBACKEND"] = "Agg"

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure

from pyfig import UnsupportedFigureError, load_figure, save_figure
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
        self.assertTrue(zipfile.is_zipfile(path))

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

    def test_loads_legacy_figure_pickle(self):
        figure = Figure()
        figure.subplots().plot([0, 1], [3, 4])
        path = Path(self.directory.name) / "legacy.pyfig"
        with path.open("wb") as file:
            pickle.dump(figure, file, protocol=pickle.HIGHEST_PROTOCOL)

        restored = load_figure(path)
        self.assertEqual(list(restored.axes[0].lines[0].get_ydata()), [3, 4])

    def test_large_lines_are_smaller_and_array_values_are_preserved(self):
        x = np.arange(50_000, dtype=np.float64) / 50_000
        figure, axes = plt.subplots()
        first, = axes.plot(x, np.sin(x), label="first")
        second, = axes.plot(x, np.cos(x), label="second")
        figure.canvas.draw()
        original_path = first.get_path().vertices.copy()
        plain_size = len(pickle.dumps(figure))

        path = save_figure(figure, Path(self.directory.name) / "lines.pyfig")
        self.assertLess(path.stat().st_size, plain_size * 0.3)
        np.testing.assert_array_equal(first.get_path().vertices, original_path)

        with zipfile.ZipFile(path) as archive:
            arrays = []
            for name in archive.namelist():
                if name.startswith("arrays/"):
                    with archive.open(name) as file:
                        arrays.append(np.load(file, allow_pickle=False))
        self.assertEqual(sum(np.array_equal(array, x) for array in arrays), 1)

        restored = load_figure(path)
        np.testing.assert_array_equal(restored.axes[0].lines[0].get_ydata(), np.sin(x))
        np.testing.assert_array_equal(restored.axes[0].lines[1].get_ydata(), np.cos(x))
        self.assertIsNot(
            restored.axes[0].lines[0].get_xdata(), restored.axes[0].lines[1].get_xdata()
        )
        restored.canvas.draw()
        self.assertEqual(len(restored.axes[0].lines[0].get_path().vertices), len(x))

    def test_image_and_scatter_round_trip(self):
        image = np.ma.array(np.arange(10_000).reshape(100, 100), mask=False)
        image.mask[3, 4] = True
        figure, (left, right) = plt.subplots(1, 2)
        left.imshow(image)
        right.scatter(np.arange(1000), np.arange(1000) * 2)
        figure.canvas.draw()
        original_pixels = np.asarray(figure.canvas.buffer_rgba()).copy()

        restored = load_figure(save_figure(figure, Path(self.directory.name) / "mixed"))
        restored_image = restored.axes[0].images[0].get_array()
        self.assertTrue(restored_image.mask[3, 4])
        self.assertEqual(restored_image[5, 6], image[5, 6])
        np.testing.assert_array_equal(
            restored.axes[1].collections[0].get_offsets(), right.collections[0].get_offsets()
        )
        restored.canvas.draw()
        np.testing.assert_array_equal(np.asarray(restored.canvas.buffer_rgba()), original_pixels)

    def test_custom_artist_is_rejected(self):
        class CustomArtist(Artist):
            def draw(self, renderer):
                pass

        figure = Figure()
        figure.add_artist(CustomArtist())
        path = Path(self.directory.name) / "custom.pyfig"
        with self.assertRaises(UnsupportedFigureError):
            save_figure(figure, path)
        self.assertFalse(path.exists())

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
