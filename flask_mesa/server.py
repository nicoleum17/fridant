from flask import Flask, jsonify
from model import AlienInvasionModel, get_sim_data
model = AlienInvasionModel(width=8, height=6, players=4)

NUMERO_AGENTES = 4


app = Flask(__name__)

@app.route("/data", methods=['GET'])
def simulation():
    simulation_state = get_sim_data(model)
    return jsonify(simulation_state)

@app.route("/new_step", methods=['POST'])
def step():
    model.step()
    simulation_state = get_sim_data(model)
    return jsonify(simulation_state)

@app.route("/new_sim",  methods=['POST'])
def new_sim():
    model = AlienInvasionModel(width=8, height=6, players=4)
    simulation_state = get_sim_data(model)
    return jsonify(simulation_state)


    
if __name__=="__main__":
    app.run()
