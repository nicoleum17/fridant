using UnityEngine;
using System.Collections.Generic;

public class AgentController : MonoBehaviour
{
    public GameObject astronautaPrefab;
    private List<GameObject> activeAgents = new List<GameObject>();

    private void OnEnable()
    {
        GameManager.OnStateChanged += HandleSimulationUpdate;
    }

    private void OnDisable()
    {
        GameManager.OnStateChanged -= HandleSimulationUpdate;
    }

    private void HandleSimulationUpdate(SimulationState state)
    {
        foreach (GameObject agentObject in activeAgents)
        {
            Destroy(agentObject);
        }
        activeAgents.Clear(); 

        if (state.agents == null) return;

        foreach (AgentModel agentData in state.agents)
        {
            Vector3 position = new Vector3(state.cuadricula[agentData.x, agentData.y, 0], 0, state.cuadricula[agentData.x, agentData.y, 1]);

            GameObject newAgent = Instantiate(astronautaPrefab, position, Quaternion.identity);

            activeAgents.Add(newAgent);
        }
    }
}