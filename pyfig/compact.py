"""Compact Figure archives built from a pickle and shared numeric arrays."""

import hashlib
import json
import os
import pickle
import shutil
import tempfile
import zipfile
from itertools import chain
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

_FORMAT = "pyfig-compact"
_VERSION = 1
_ARRAY_THRESHOLD = 4096
_LINE_CACHES = ("_x", "_y", "_xy", "_path", "_transformed_path", "_x_filled")


class UnsupportedFigureError(TypeError):
    """A figure contains an artist that the compact format cannot save safely."""


def _check_artists(figure):
    if not type(figure).__module__.startswith("matplotlib."):
        cls = type(figure)
        raise UnsupportedFigureError(
            f"compact format does not support {cls.__module__}.{cls.__qualname__}"
        )
    for artist in figure.findobj():
        if isinstance(artist, Artist) and not type(artist).__module__.startswith("matplotlib."):
            cls = type(artist)
            raise UnsupportedFigureError(
                f"compact format does not support {cls.__module__}.{cls.__qualname__}"
            )


def _clear_line_caches(figure):
    """Discard recomputable drawing data, including on the source figure."""
    data_lines = chain(getattr(figure, "lines", ()), *(axes.lines for axes in figure.axes))
    for line in data_lines:
        for key in _LINE_CACHES:
            line.__dict__[key] = None
        line._invalidx = line._invalidy = True


class _CompactPickler(pickle.Pickler):
    def __init__(self, file, archive):
        super().__init__(file, protocol=5)
        self.archive = archive
        self._object_references = {}
        self._blob_names = set()

    def _store_array(self, array):
        if array.flags.c_contiguous:
            payload = array
            order = b"C"
        elif array.flags.f_contiguous:
            payload = array.T
            order = b"F"
        else:
            payload = np.ascontiguousarray(array)
            order = b"C"
        digest = hashlib.sha256()
        digest.update(repr(array.dtype.descr).encode("utf-8"))
        digest.update(repr(array.shape).encode("ascii"))
        digest.update(order)
        digest.update(memoryview(payload).cast("B"))
        name = f"arrays/{digest.hexdigest()}.npy"
        if name not in self._blob_names:
            with self.archive.open(name, "w", force_zip64=True) as output:
                np.save(output, array, allow_pickle=False)
            self._blob_names.add(name)
        return name

    def persistent_id(self, obj):
        if type(obj) is np.ndarray and obj.nbytes >= _ARRAY_THRESHOLD:
            if obj.dtype.hasobject:
                return None
            if id(obj) not in self._object_references:
                object_id = len(self._object_references)
                token = ("array", object_id, self._store_array(obj))
                self._object_references[id(obj)] = (obj, token)
            return self._object_references[id(obj)][1]

        if type(obj) is np.ma.MaskedArray and obj.nbytes >= _ARRAY_THRESHOLD:
            if obj.dtype.hasobject:
                return None
            if id(obj) not in self._object_references:
                object_id = len(self._object_references)
                data_name = self._store_array(np.asarray(obj.data))
                mask_name = self._store_array(np.ascontiguousarray(np.ma.getmaskarray(obj)))
                token = (
                    "masked", object_id, data_name, mask_name, obj.fill_value, obj.hardmask
                )
                self._object_references[id(obj)] = (obj, token)
            return self._object_references[id(obj)][1]

        return None


class _CompactUnpickler(pickle.Unpickler):
    def __init__(self, file, archive):
        super().__init__(file)
        self.archive = archive
        self._objects = {}

    def _load_array(self, name):
        if not name.startswith("arrays/") or not name.endswith(".npy"):
            raise pickle.UnpicklingError("invalid array reference")
        with self.archive.open(name) as source:
            return np.load(source, allow_pickle=False)

    def persistent_load(self, token):
        if not isinstance(token, tuple) or len(token) < 3:
            raise pickle.UnpicklingError("invalid compact figure reference")
        kind, object_id = token[:2]
        if object_id not in self._objects:
            if kind == "array" and len(token) == 3:
                self._objects[object_id] = self._load_array(token[2])
            elif kind == "masked" and len(token) == 6:
                data = self._load_array(token[2])
                mask = self._load_array(token[3])
                self._objects[object_id] = np.ma.array(
                    data, mask=mask, fill_value=token[4], hard_mask=token[5], copy=False
                )
            else:
                raise pickle.UnpicklingError("invalid compact figure reference")
        return self._objects[object_id]


def save_compact_figure(figure: Figure, path) -> Path:
    """Save a Figure as a compact archive; return its ``.pyfig`` path.

    Standard Matplotlib artists are supported. Custom Artist subclasses are
    rejected rather than silently changing the figure.
    """
    if not isinstance(figure, Figure):
        raise TypeError("figure must be a matplotlib.figure.Figure")
    _check_artists(figure)
    _clear_line_caches(figure)

    destination = Path(path)
    if destination.suffix != ".pyfig":
        destination = destination.with_name(destination.name + ".pyfig")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=3, allowZip64=True) as archive:
            with tempfile.TemporaryFile(dir=destination.parent) as pickle_file:
                _CompactPickler(pickle_file, archive).dump(figure)
                pickle_file.seek(0)
                with archive.open("figure.pkl", "w", force_zip64=True) as output:
                    shutil.copyfileobj(pickle_file, output)
            archive.writestr("manifest.json", json.dumps({
                "format": _FORMAT,
                "version": _VERSION,
                "matplotlib": matplotlib.__version__,
            }))
        os.replace(temporary_name, destination)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return destination


def load_compact_figure(path) -> Figure:
    """Load a trusted compact figure archive."""
    with zipfile.ZipFile(path) as archive:
        try:
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("format") != _FORMAT or manifest.get("version") != _VERSION:
                raise ValueError("unsupported .pyfig format version")
            with archive.open("figure.pkl") as source:
                figure = _CompactUnpickler(source, archive).load()
        except KeyError as error:
            raise ValueError("incomplete .pyfig archive") from error
    if not isinstance(figure, Figure):
        raise TypeError("file does not contain a matplotlib.figure.Figure")
    return figure
