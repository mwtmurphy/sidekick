'''blueprint for all pages focussed on movements'''

import flask
from flask import current_app
import itertools
import json
import networkx as nx
import pandas as pd
import random
import time
import typing

from sidekik import db, forms, models
from sidekik.models import Warmup, Workout


#typing
created_warmups = typing.Tuple[typing.List[str], typing.List[typing.List[str]]]


#blueprint
bp = flask.Blueprint("movements", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    form = forms.MoveListForm()

    work_query = Workout.query.all()
    work_moves = sorted([row.name for row in work_query if row.warmups_labelled])

    warm_moves = []
    if form.validate_on_submit():
        sel_moves = [move["move"].title() for move in form.moves.data if move["move"]]
        if not sel_moves:
            flask.flash("No movements found in workout form")
            return flask.redirect(flask.url_for("index", _anchor="create_warmup"))

        work_rows = Workout.query.filter(Workout.name.in_(sel_moves)).all()
        warm_rows = set([item for sublist in [row.warmups for row in work_rows] for item in sublist])
        df = pd.DataFrame(map(convert_to_dict, warm_rows)).set_index("name")
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

        try:
            t_init = time.time()
            warm_options = create_warmups(df, max_moves=5)
            t_end = round(time.time() - t_init, 4)

        except RuntimeError:
            flask.flash(("sidekik was not able to create a warm-up for this workout. It has been "
                         "logged, and a developer will fix this as soon as possible."))
            failed_warmup = models.CreatedWarmup(workouts=work_rows, passed=False)
            db.session.add(failed_warmup)
            db.session.commit()

            return flask.render_template("movements/index.html", form=form, scroll="create_warmup", 
                                         work_moves=json.dumps(work_moves))
        
        else:
            warm_moves = random.choice(warm_options)
            warm_rows = Warmup.query.filter(Warmup.name.in_(warm_moves)).all()
            created_warmup = models.CreatedWarmup(warmups=warm_rows, workouts=work_rows, 
                                                  ex_time=t_end, passed=True)
            db.session.add(created_warmup)
            db.session.commit()

            return flask.render_template("movements/index.html", form=form, scroll="create_warmup", 
                                         warm_moves=warm_moves, warm_options=json.dumps(warm_options),
                                         work_moves=json.dumps(work_moves))

    return flask.render_template("movements/index.html", form=form, work_moves=json.dumps(work_moves))


#helper function
def convert_to_dict(row: models.Warmup) -> dict:
    '''returns row in workout/warmup table as dict with variables name
    and move_types'''
    row_dict = {"name": row.name}
    for type_row in row.move_types:
        row_dict[type_row.name] = 1

    return row_dict

def create_warmups(df: pd.DataFrame, max_moves: int, max_out: int = 7) -> created_warmups:
    '''Returns initial suggestion for warmup and all viable warmups
    found in df with n movements in [min_moves, max_moves].
    
    max_out sets the limit for out edges from each node.
    '''
    mtype_sum = df.sum().sort_values()
    cols = mtype_sum[mtype_sum == mtype_sum.min()].index
    rows = df.index[df[cols].any(axis=1)]
    rows = random.sample(list(rows), max_out) if rows.shape[0] > max_out else rows
    
    graph = nx.DiGraph()
    graph.add_nodes_from(["1_"+move for move in rows])

    counter = 0
    loop = 2
    updating = True 
    warmups = []
    
    while updating and loop <= max_moves+1:
        updating = False
        max_out -= 1
                
        for i, leaf in enumerate(list(graph.nodes)[counter:]):
            rows = [node.split("_")[1] for node in get_par_nodes(graph, leaf)]
            cols = df.iloc[0, (df.loc[rows].sum() > 0).values].index
            sub_df = df.drop(index=rows, columns=cols).dropna(axis=0, how="all")

            if sub_df.shape == (0, 0):
                warmups.append(sorted(rows))

            elif loop != max_moves+1:
                mtype_sum = sub_df.sum().sort_values()
                cols = mtype_sum[mtype_sum == mtype_sum.min()].index
                rows = sub_df.index[sub_df[cols].any(axis=1)]
                rows = random.sample(list(rows), max_out) if rows.shape[0] > max_out else rows
                
                graph.add_edges_from([(leaf, f"{loop}{i}_"+move) for move in rows])
                updating = True

            counter += 1
        loop += 1
            
    if not warmups:
        raise RuntimeError(f"No warm-ups found with less than {max_moves} movements")
                
    #remove duplicates and supersets
    warmups.sort()
    warmups = list(warmup for warmup, _ in itertools.groupby(warmups))
    warmups = remove_warmup_supersets(warmups)
    
    return warmups

def get_par_nodes(graph: nx.DiGraph, node: str) -> typing.List[str]:
    '''Returns all parent nodes leading to initial movement'''
    preds = list(graph.predecessors(node))
    return [node] + get_par_nodes(graph, preds[0]) if preds else [node]
    
def remove_warmup_supersets(warmups: typing.List[typing.List[str]]) -> typing.List[typing.List[str]]:
    '''Returns all sublists which are not a subset of any other 
    sublist in warmups'''
    counts = set(map(len, warmups))
    count_dict = {n: [warmup for warmup in warmups if len(warmup) == n] for n in counts}

    for i, j in [(i, j) for i in counts for j in counts if i > j]:
        for lg_warmup in count_dict[i]:
            if lg_warmup in warmups:
                for sm_warmup in count_dict[j]:
                    if set(lg_warmup).issuperset(sm_warmup):
                        warmups.remove(lg_warmup)
                        break
                        
    return warmups