#Import dependencies
import numpy as numpy
import pandas as pd
import os
import sqlalchemy
import json
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

from flask import (
    Flask,
    render_template,
    jsonify,
    request, 
    redirect)


# Flask Setup
#################################################
app = Flask(__name__)

# Database Setup
#################################################
engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite", echo=False)
# reflect an existing database into a new model | and reflect the tables
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to the table
OTU = Base.classes.otu
Samples = Base.classes.samples
md = Base.classes.samples_metadata

# Create our session (link) from Python to the DB
session = Session(engine)

# Flask Routes
#################################################
# create route that renders index.html template
@app.route('/')
def home():
    return render_template("/index.html")

#################################################
# Query the database and send the jsonified results
#################################################

# sample name query
@app.route('/names')
def names():
    inspector = inspect(engine)
    columns = inspector.get_columns('samples')
    samples_col = []
    for c in columns: 
        samples_col.append(c)
    sample_names= []
    for names in samples_col:
        sample_names.append(names["name"])    
    return jsonify(sample_names[1:])    

# otu descriptions (lowest taxonomic unit) query
@app.route('/otu')
def otu():
    otu_query = session.query(OTU.lowest_taxonomic_unit_found).all()
    return jsonify(otu_query)

# Gets metadata for a given sample
@app.route('/metadata/<sample>')
def metadata(sample):
    for AGE, BBTYPE, ETHNICITY, GENDER, LOCATION, SAMPLEID in \
    session.query(md.AGE, md.BBTYPE, md.ETHNICITY, md.GENDER, md.LOCATION, md.SAMPLEID).\
       filter_by(SAMPLEID = sample[3:]):

        metadict = {'AGE': AGE,
                   "BBTY": BBTYPE,
                   'ETHINICITY': ETHNICITY,
                   'GENDER': GENDER,
                   'LOCATION': LOCATION,
                   'SAMPLEID': f'BB_{str(SAMPLEID)}'
                   }
        return jsonify(metadict)

# Gets washing frequency for a given sample
@app.route('/wfreq/<sample>')
def wash_frequency(sample):
    for SAMPLEID, WFREQ in session.query(md.SAMPLEID, md.WFREQ).\
        filter_by(SAMPLEID = sample):
        return jsonify(WFREQ)

# Gets OTU IDs and Sample Values for a given sample.
@app.route('/samples/<sample>')
def samples(sample):
    results = session.query(Samples.otu_id, getattr(Samples, sample)).\
        filter(getattr(Samples, sample) >= 1 ).order_by(getattr(Samples, sample).desc()).all()
    samples_data = [{
        "otu_ids": [result[0] for result in results],
        "sample_values": [result[1] for result in results]
        }]
    return jsonify(samples_data)


if __name__ == "__main__":
    app.run(debug=True)