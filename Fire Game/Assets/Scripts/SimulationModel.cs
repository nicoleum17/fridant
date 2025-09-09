using System.Collections.Generic;
using System;
using UnityEngine;

[System.Serializable]
public class AgentModel
{
    public int id;
    public int x;
    public int y;
    public int action_points;
    public bool carrying_victim;

}

[System.Serializable]
public class AlienInvasionModel
{
    public int saved_victims;
    public int lost_victims;
    public int damage;
    public int steps;

}
[System.Serializable] 
public class SimulationState
{
    public AlienInvasionModel model_data;
    public List<AgentModel> agents; // Una lista de los agentes
}