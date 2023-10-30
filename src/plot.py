from typing import Tuple

import matplotlib

# Backend for interactive plots to work when app is bundled.
# Needs to be before import matplotlib.pyplot
matplotlib.use('qtagg')
import matplotlib.pyplot as plt
import seaborn as sns

from eltypes import data


def setup_plots():
    sns.set_style("whitegrid")


def lineplot(
    df: data,
    data_sources: list[str],
    element_ids: list[int],
    measurement_kinds: list[str],
    dims: Tuple[int, int] = (15, 8),
) -> None:
    same = lambda xs: all(x == xs[0] for x in xs)
    same_sources = same(data_sources)
    title = f"{data_sources[0]}" if same_sources else f"{', '.join(data_sources)}"
    same_kinds = same(measurement_kinds)
    if same_kinds:
        plt.figure(figsize=dims)
        plt.title(title)

    dedup_label = lambda s: s.split(".")[0]
    for idx, (t_col, val_col) in enumerate(
        zip(df.columns[::2], df.columns[1::2])
    ):
        if not same_kinds:
            plt.figure(figsize=dims)

        sns.lineplot(
            x=t_col,
            y=val_col,
            data=df[[t_col, val_col]],
            label=f"{measurement_kinds[idx]} of element {element_ids[idx]}",
        )
        if not same_kinds:
            plt.title(title)
            plt.xlabel(dedup_label(plt.gca().get_xlabel()))
            plt.ylabel(dedup_label(plt.gca().get_ylabel()))
            plt.show()

    if same_kinds:
        plt.show()
